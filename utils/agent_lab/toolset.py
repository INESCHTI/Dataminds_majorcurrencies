from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

PAIRS = ["EURUSD", "USDJPY", "GBPUSD", "USDCHF"]


@dataclass
class ToolOutput:
    name: str
    ok: bool
    payload: dict[str, Any]
    error: str | None = None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _signals_dir() -> Path:
    return _repo_root() / "agents" / "outputs" / "signals"


def _read_latest(agent: str, pair: str) -> dict[str, Any] | None:
    base = _signals_dir()
    if not base.exists():
        return None
    files = sorted(base.glob(f"{agent}_{pair}_*.json"))
    for p in reversed(files):
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
    return None


def _safe_get_json(url: str, timeout: float = 6.0) -> dict[str, Any] | None:
    try:
        r = requests.get(url, timeout=timeout)
        if not r.ok:
            return None
        obj = r.json()
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def technical_snapshot(pair: str, api_base: str = "http://localhost:3000") -> ToolOutput:
    pair = pair.upper()
    if pair not in PAIRS:
        return ToolOutput(name="technical_snapshot", ok=False, payload={}, error=f"unsupported pair {pair}")

    payload = _safe_get_json(f"{api_base}/api/v2/trading/pair_snapshots")
    if payload and isinstance(payload.get("snapshots"), dict):
        row = payload["snapshots"].get(pair)
        if isinstance(row, dict):
            return ToolOutput(name="technical_snapshot", ok=True, payload={"pair": pair, "source": "api", **row})

    local = _read_latest("technical", pair)
    if local:
        return ToolOutput(name="technical_snapshot", ok=True, payload={"pair": pair, "source": "signals", **local})

    return ToolOutput(name="technical_snapshot", ok=False, payload={"pair": pair}, error="no technical data")


def sentiment_snapshot(pair: str) -> ToolOutput:
    pair = pair.upper()
    if pair not in PAIRS:
        return ToolOutput(name="sentiment_snapshot", ok=False, payload={}, error=f"unsupported pair {pair}")

    local = _read_latest("sentiment", pair)
    if local:
        return ToolOutput(name="sentiment_snapshot", ok=True, payload={"pair": pair, **local})

    return ToolOutput(name="sentiment_snapshot", ok=False, payload={"pair": pair}, error="no sentiment data")


def freshness_health(api_base: str = "http://localhost:3000") -> ToolOutput:
    payload = _safe_get_json(f"{api_base}/api/v2/monitoring/freshness_health")
    if payload:
        return ToolOutput(name="freshness_health", ok=True, payload=payload)
    return ToolOutput(name="freshness_health", ok=False, payload={}, error="freshness endpoint unavailable")


def fuse_sentiment_technical(pair: str, api_base: str = "http://localhost:3000") -> ToolOutput:
    tech = technical_snapshot(pair, api_base=api_base)
    sent = sentiment_snapshot(pair)

    if not tech.ok and not sent.ok:
        return ToolOutput(name="fuse_sentiment_technical", ok=False, payload={"pair": pair}, error="no inputs available")

    tech_signal = str(tech.payload.get("signal", "NEUTRAL")).upper() if tech.ok else "NEUTRAL"
    sent_signal = str(sent.payload.get("signal", "NEUTRAL")).upper() if sent.ok else "NEUTRAL"

    tech_conf = float(tech.payload.get("confidence", 0.5) or 0.5) if tech.ok else 0.5
    sent_conf = float(sent.payload.get("confidence", 0.5) or 0.5) if sent.ok else 0.5

    def signed(sig: str, conf: float) -> float:
        if sig == "BUY":
            return conf
        if sig == "SELL":
            return -conf
        return 0.0

    score = signed(tech_signal, tech_conf) * 0.55 + signed(sent_signal, sent_conf) * 0.45
    if score > 0.08:
        decision = "BUY"
    elif score < -0.08:
        decision = "SELL"
    else:
        decision = "NEUTRAL"

    return ToolOutput(
        name="fuse_sentiment_technical",
        ok=True,
        payload={
            "pair": pair.upper(),
            "technical_signal": tech_signal,
            "technical_confidence": round(tech_conf, 4),
            "sentiment_signal": sent_signal,
            "sentiment_confidence": round(sent_conf, 4),
            "fusion_score": round(score, 4),
            "decision": decision,
        },
    )
