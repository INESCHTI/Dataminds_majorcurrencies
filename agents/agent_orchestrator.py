"""
=====================================
ORCHESTRATOR AGENT (FOUR-EYES)
FX-AlphaLab | Central Decision Brain
=====================================
Combines technical + macro + sentiment signals with a Four-Eyes principle.

Decision rule:
- BUY/SELL only if at least 2 independent agents agree on direction
  with confidence above a minimum threshold.
- Otherwise -> HOLD.

This script reads the latest saved JSON outputs from:
  outputs/signals/technical_<SYMBOL>_*.json
  outputs/signals/macro_<SYMBOL>_*.json
  outputs/signals/sentiment_<SYMBOL>_*.json
"""

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from glob import glob
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv


def load_environment_files() -> None:
    """Load local and root .env files with encoding fallback for Windows."""
    current_file = Path(__file__).resolve()
    env_candidates = [
        current_file.parent / ".env",
        current_file.parents[1] / ".env",
    ]
    encodings = ("utf-8", "utf-8-sig", "utf-16")

    for env_path in env_candidates:
        if not env_path.exists():
            continue
        loaded = False
        for encoding in encodings:
            try:
                if load_dotenv(dotenv_path=env_path, override=False, encoding=encoding):
                    print(f"Loaded env: {env_path} (encoding={encoding})")
                loaded = True
                break
            except UnicodeDecodeError:
                continue
            except Exception as exc:
                print(f"Warning: failed to load {env_path} ({encoding}): {exc}")
                loaded = True
                break
        if not loaded:
            print(f"Warning: could not decode env file {env_path} with supported encodings")


load_environment_files()


DEFAULT_PAIRS = ["EURUSD", "USDCHF", "GBPUSD", "USDJPY"]
PAIRS_ENV = os.getenv("FX_PAIRS", "")
if PAIRS_ENV.strip():
    PAIRS = [p.strip().upper() for p in PAIRS_ENV.split(",") if p.strip()]
else:
    PAIRS = DEFAULT_PAIRS.copy()
PAIRS = list(dict.fromkeys(PAIRS))

DEFAULT_SYMBOL = os.getenv("FX_DEFAULT_SYMBOL", "EURUSD").upper()
RUN_ALL_SYMBOLS = os.getenv("FX_RUN_ALL_SYMBOLS", "1").lower() in {"1", "true", "yes", "on"}

ORCH_MIN_VOTE_CONF = float(os.getenv("FX_ORCH_MIN_VOTE_CONF", "0.55"))
ORCH_MAX_SIGNAL_AGE_MIN = int(os.getenv("FX_ORCH_MAX_SIGNAL_AGE_MIN", "360"))
ORCH_PRIORITY_MIN_CONF = float(os.getenv("FX_ORCH_PRIORITY_MIN_CONF", "0.48"))
ORCH_PRIORITY_REQUIRE_MACRO = os.getenv("FX_ORCH_PRIORITY_REQUIRE_MACRO", "1").lower() in {"1", "true", "yes", "on"}

ORCH_AUTO_RUN_MISSING = os.getenv("FX_ORCH_AUTO_RUN_MISSING", "1").lower() in {"1", "true", "yes", "on"}
ORCH_AUTO_RUN_TIMEOUT_SEC = int(os.getenv("FX_ORCH_AUTO_RUN_TIMEOUT_SEC", "240"))

AGENT_WEIGHTS = {
    "technical": float(os.getenv("FX_ORCH_WEIGHT_TECHNICAL", "0.40")),
    "macro": float(os.getenv("FX_ORCH_WEIGHT_MACRO", "0.35")),
    "sentiment": float(os.getenv("FX_ORCH_WEIGHT_SENTIMENT", "0.25")),
}

AGENT_PRIORITY_BONUS = {
    "technical": float(os.getenv("FX_ORCH_PRIORITY_BONUS_TECHNICAL", "1.00")),
    "macro": float(os.getenv("FX_ORCH_PRIORITY_BONUS_MACRO", "1.20")),
    "sentiment": float(os.getenv("FX_ORCH_PRIORITY_BONUS_SENTIMENT", "0.90")),
}

SIGNALS_DIR = Path("outputs/signals")
AGENT_NAMES = ["technical", "macro", "sentiment"]
AGENT_SCRIPT = {
    "technical": "agent_technical.py",
    "macro": "agent_macro.py",
    "sentiment": "agent_sentiment.py",
}


@dataclass
class AgentSignal:
    agent: str
    symbol: str
    signal: str
    confidence: float
    timestamp: Optional[datetime]
    path: Optional[str]
    raw: dict


def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    text = str(value).strip()
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _read_json(path: str) -> Optional[dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except UnicodeDecodeError:
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except Exception:
            return None
    except Exception:
        return None


def _normalize_signal(agent: str, symbol: str, payload: dict, path: Optional[str]) -> AgentSignal:
    signal = str(payload.get("signal", "HOLD")).upper().strip()
    if signal not in {"BUY", "SELL", "HOLD"}:
        signal = "HOLD"

    try:
        confidence = float(payload.get("confidence", 0.0) or 0.0)
    except Exception:
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))

    ts = _parse_timestamp(payload.get("timestamp"))
    resolved_symbol = str(payload.get("symbol", symbol)).upper().strip()

    return AgentSignal(
        agent=agent,
        symbol=resolved_symbol,
        signal=signal,
        confidence=confidence,
        timestamp=ts,
        path=path,
        raw=payload,
    )


def load_latest_signal(agent: str, symbol: str) -> Optional[AgentSignal]:
    pattern = str(SIGNALS_DIR / f"{agent}_{symbol}_*.json")
    candidates = sorted(glob(pattern))
    if not candidates:
        return None

    for path in reversed(candidates):
        payload = _read_json(path)
        if not isinstance(payload, dict):
            continue
        return _normalize_signal(agent, symbol, payload, path)
    return None


def is_fresh(signal: AgentSignal) -> bool:
    if signal.timestamp is None:
        return True
    age_minutes = (datetime.now(timezone.utc) - signal.timestamp).total_seconds() / 60.0
    return age_minutes <= ORCH_MAX_SIGNAL_AGE_MIN


def _weighted_confidence(signals: List[AgentSignal], use_priority_bonus: bool = False) -> float:
    weighted = 0.0
    weight_sum = 0.0
    for s in signals:
        base_w = AGENT_WEIGHTS.get(s.agent, 0.0)
        bonus = AGENT_PRIORITY_BONUS.get(s.agent, 1.0) if use_priority_bonus else 1.0
        w = base_w * bonus
        weighted += s.confidence * w
        weight_sum += w
    if weight_sum > 0:
        return round(weighted / weight_sum, 2)
    return round(sum(s.confidence for s in signals) / max(len(signals), 1), 2)


def run_missing_agent(agent: str, symbol: str) -> dict:
    script_name = AGENT_SCRIPT.get(agent)
    if not script_name:
        return {"agent": agent, "ok": False, "error": "No mapped script"}

    base_dir = Path(__file__).resolve().parent
    script_path = base_dir / script_name
    if not script_path.exists():
        return {"agent": agent, "ok": False, "error": f"Script not found: {script_path}"}

    cmd = [sys.executable, str(script_path), symbol]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(base_dir),
            capture_output=True,
            text=True,
            timeout=ORCH_AUTO_RUN_TIMEOUT_SEC,
        )
        ok = proc.returncode == 0
        info = {
            "agent": agent,
            "ok": ok,
            "returncode": proc.returncode,
            "command": " ".join(cmd),
        }
        if not ok:
            info["stderr_tail"] = (proc.stderr or "")[-500:]
            info["stdout_tail"] = (proc.stdout or "")[-500:]
        return info
    except subprocess.TimeoutExpired:
        return {
            "agent": agent,
            "ok": False,
            "error": f"Timeout after {ORCH_AUTO_RUN_TIMEOUT_SEC}s",
            "command": " ".join(cmd),
        }
    except Exception as exc:
        return {"agent": agent, "ok": False, "error": str(exc), "command": " ".join(cmd)}


def four_eyes_decision(signals: List[AgentSignal]) -> Tuple[str, float, str, dict]:
    eligible = [
        s for s in signals
        if s.signal in {"BUY", "SELL"}
        and s.confidence >= ORCH_MIN_VOTE_CONF
        and is_fresh(s)
    ]

    buy_votes = [s for s in eligible if s.signal == "BUY"]
    sell_votes = [s for s in eligible if s.signal == "SELL"]

    if len(buy_votes) >= 2 and len(sell_votes) == 0:
        final_signal = "BUY"
        agreeing = buy_votes
        decision_mode = "strict"
        reason = "Four-Eyes satisfied: >=2 BUY votes, no eligible SELL conflict"
    elif len(sell_votes) >= 2 and len(buy_votes) == 0:
        final_signal = "SELL"
        agreeing = sell_votes
        decision_mode = "strict"
        reason = "Four-Eyes satisfied: >=2 SELL votes, no eligible BUY conflict"
    else:
        # Priority fallback: 2 aligned fresh votes can pass if weighted confidence is acceptable.
        # Macro has higher priority in this tie-break path.
        fresh_directional = [s for s in signals if s.signal in {"BUY", "SELL"} and is_fresh(s)]
        fresh_buy = [s for s in fresh_directional if s.signal == "BUY"]
        fresh_sell = [s for s in fresh_directional if s.signal == "SELL"]

        final_signal = "HOLD"
        agreeing = []
        decision_mode = "hold"
        reason = "No clean Four-Eyes agreement (insufficient consensus or directional conflict)"

        def _can_priority_pass(votes: List[AgentSignal], opposite_votes: List[AgentSignal]) -> bool:
            if len(votes) < 2 or len(opposite_votes) > 0:
                return False
            has_macro = any(v.agent == "macro" for v in votes)
            if ORCH_PRIORITY_REQUIRE_MACRO and not has_macro:
                return False
            return _weighted_confidence(votes, use_priority_bonus=True) >= ORCH_PRIORITY_MIN_CONF

        if _can_priority_pass(fresh_buy, fresh_sell):
            final_signal = "BUY"
            agreeing = fresh_buy
            decision_mode = "priority_fallback"
            reason = "Priority fallback: aligned BUY votes accepted with macro precedence"
        elif _can_priority_pass(fresh_sell, fresh_buy):
            final_signal = "SELL"
            agreeing = fresh_sell
            decision_mode = "priority_fallback"
            reason = "Priority fallback: aligned SELL votes accepted with macro precedence"

    if agreeing:
        final_conf = _weighted_confidence(agreeing, use_priority_bonus=(decision_mode == "priority_fallback"))
    else:
        # Confidence remains conservative when no consensus is achieved.
        final_conf = 0.45

    audit = {
        "min_vote_confidence": ORCH_MIN_VOTE_CONF,
        "max_signal_age_minutes": ORCH_MAX_SIGNAL_AGE_MIN,
        "eligible_votes": [
            {"agent": s.agent, "signal": s.signal, "confidence": s.confidence}
            for s in eligible
        ],
        "buy_votes": len(buy_votes),
        "sell_votes": len(sell_votes),
        "priority_min_confidence": ORCH_PRIORITY_MIN_CONF,
        "priority_require_macro": ORCH_PRIORITY_REQUIRE_MACRO,
        "decision_mode": decision_mode,
    }
    return final_signal, final_conf, reason, audit


def orchestrate_symbol(symbol: str) -> dict:
    symbol = symbol.upper().strip()
    if symbol not in PAIRS:
        raise ValueError(f"Invalid symbol '{symbol}'. Allowed: {', '.join(PAIRS)}")

    loaded: Dict[str, Optional[AgentSignal]] = {
        agent: load_latest_signal(agent, symbol)
        for agent in AGENT_NAMES
    }

    auto_run_attempts = []
    if ORCH_AUTO_RUN_MISSING:
        initial_missing = [name for name, sig in loaded.items() if sig is None]
        for missing_agent in initial_missing:
            print(f"Auto-run missing agent: {missing_agent} ({symbol})")
            attempt = run_missing_agent(missing_agent, symbol)
            auto_run_attempts.append(attempt)
            loaded[missing_agent] = load_latest_signal(missing_agent, symbol)

    missing = [name for name, sig in loaded.items() if sig is None]
    available = [sig for sig in loaded.values() if sig is not None]

    if not available:
        result = {
            "symbol": symbol,
            "signal": "HOLD",
            "confidence": 0.0,
            "reasoning": "No input signals found from technical/macro/sentiment",
            "four_eyes": False,
            "missing_agents": missing,
            "auto_run_attempts": auto_run_attempts,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": "orchestrator",
        }
        save_signal(result, symbol)
        return result

    final_signal, final_conf, reason, audit = four_eyes_decision(available)

    result = {
        "symbol": symbol,
        "signal": final_signal,
        "confidence": final_conf,
        "reasoning": reason,
        "four_eyes": final_signal in {"BUY", "SELL"},
        "missing_agents": missing,
        "auto_run_attempts": auto_run_attempts,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": "orchestrator",
        "inputs": {
            name: ({
                "signal": sig.signal,
                "confidence": sig.confidence,
                "timestamp": sig.timestamp.isoformat() if sig.timestamp else None,
                "fresh": is_fresh(sig),
                "path": sig.path,
            } if sig else None)
            for name, sig in loaded.items()
        },
        "audit": audit,
    }

    save_signal(result, symbol)
    return result


def save_signal(signal: dict, symbol: str) -> None:
    os.makedirs(SIGNALS_DIR, exist_ok=True)
    path = SIGNALS_DIR / f"orchestrator_{symbol}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(signal, f, indent=2, default=str)
    print(f"Saved signal -> {path}")


def resolve_target_symbol() -> str:
    if len(sys.argv) > 1:
        candidate = sys.argv[1].upper().strip()
    else:
        candidate = DEFAULT_SYMBOL
    if candidate not in PAIRS:
        raise ValueError(f"Invalid symbol '{candidate}'. Allowed: {', '.join(PAIRS)}")
    return candidate


def should_run_all_symbols() -> bool:
    if RUN_ALL_SYMBOLS:
        return True
    if len(sys.argv) <= 1:
        return True
    return sys.argv[1].upper().strip() == "ALL"


def print_report(results: List[dict]) -> None:
    if not results:
        print("No orchestrated results.")
        return

    ranked = sorted(
        results,
        key=lambda x: (
            {"BUY": 0, "SELL": 1, "HOLD": 2}.get(str(x.get("signal", "HOLD")).upper(), 3),
            -float(x.get("confidence", 0) or 0),
        ),
    )

    print(f"\n{'=' * 78}\n  ORCHESTRATOR REPORT (FOUR-EYES)\n{'=' * 78}")
    for item in ranked:
        sym = item.get("symbol", "?")
        sig = item.get("signal", "HOLD")
        conf = float(item.get("confidence", 0) or 0)
        fe = item.get("four_eyes", False)
        missing = ",".join(item.get("missing_agents", [])) or "none"
        print(f"  {sym:<6} -> {sig:<4} ({conf:.0%}) | four_eyes={fe} | missing={missing}")


if __name__ == "__main__":
    print("=" * 60)
    print("  ORCHESTRATOR AGENT")
    print("  FX-AlphaLab | Four-Eyes Principle")
    print("=" * 60)
    print(f"\n  Pairs        : {', '.join(PAIRS)}")
    print(f"  Min vote conf: {ORCH_MIN_VOTE_CONF}")
    print(f"  Priority conf: {ORCH_PRIORITY_MIN_CONF}")
    print(f"  Auto-run miss: {ORCH_AUTO_RUN_MISSING}")
    print(f"  Max age (min): {ORCH_MAX_SIGNAL_AGE_MIN}\n")

    if should_run_all_symbols():
        print("Mode: ALL pairs")
        all_results = []
        for symbol in PAIRS:
            print(f"\nOrchestrating {symbol}...")
            all_results.append(orchestrate_symbol(symbol))
        print_report(all_results)
    else:
        symbol = resolve_target_symbol()
        print(f"Mode: single pair ({symbol})")
        result = orchestrate_symbol(symbol)
        print(json.dumps(result, indent=2, default=str))
