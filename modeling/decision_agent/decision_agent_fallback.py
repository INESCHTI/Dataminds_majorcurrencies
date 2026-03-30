"""Deterministic fallback synthesis for the Decision Agent."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List

import numpy as np

_SIG_MAP = {"BUY": 1, "HOLD": 0, "SELL": -1}
_INV_SIG_MAP = {1: "BUY", 0: "HOLD", -1: "SELL"}


def _sig_to_num(sig: str) -> int:
    return _SIG_MAP.get(str(sig or "HOLD").upper(), 0)


def _conf(v) -> float:
    try:
        return float(np.clip(float(v), 0.0, 1.0))
    except Exception:
        return 0.0


def _agent_weight(name: str) -> float:
    # Phase 1 static prior weights.
    base = {"technical": 0.45, "macro": 0.30, "sentiment": 0.25}
    return base.get(name, 0.0)


def fallback_decision(
    symbol: str,
    timeframe: str,
    technical_payload: Dict,
    macro_payload: Dict,
    sentiment_payload: Dict,
    *,
    reason: str,
    risk_flags: List[str] | None = None,
) -> Dict:
    risk_flags = list(risk_flags or [])

    agents = {
        "technical": technical_payload,
        "macro": macro_payload,
        "sentiment": sentiment_payload,
    }

    weighted_sum = 0.0
    total_weight = 0.0
    contributing_agents = {}

    for name, payload in agents.items():
        sig = str(payload.get("signal", "N/A")).upper()
        conf = _conf(payload.get("confidence", 0.0))
        missing = int(sig == "N/A" or bool(payload.get("error")))

        prior = _agent_weight(name)
        w = 0.0 if missing else prior * conf

        weighted_sum += w * _sig_to_num(sig)
        total_weight += w

        contributing_agents[name] = {
            "signal": sig,
            "confidence": conf,
            "weight": round(float(w), 6),
            "missing": bool(missing),
            "warning": payload.get("warning"),
            "error": payload.get("error"),
        }

    if total_weight <= 1e-12:
        final_signal = "HOLD"
        raw_score = 0.0
    else:
        raw_score = weighted_sum / total_weight
        if raw_score > 0.20:
            final_signal = "BUY"
        elif raw_score < -0.20:
            final_signal = "SELL"
        else:
            final_signal = "HOLD"

    coverage = float(np.clip(total_weight / (0.45 + 0.30 + 0.25), 0.0, 1.0))
    confidence = float(np.clip((0.30 + 0.65 * abs(raw_score)) * coverage, 0.0, 0.90))

    probs = {
        "buy": float(np.clip((raw_score + 1.0) / 2.0, 0.0, 1.0)),
        "sell": float(np.clip((-raw_score + 1.0) / 2.0, 0.0, 1.0)),
        "hold": float(np.clip(1.0 - abs(raw_score), 0.0, 1.0)),
    }

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "final_signal": final_signal,
        "global_confidence": round(confidence, 6),
        "model_type": "rule_fallback",
        "model_version": "fallback_v1",
        "probabilities": {k: round(v, 6) for k, v in probs.items()},
        "feature_importance": [],
        "contributing_agents": contributing_agents,
        "risk_flags": sorted(set(risk_flags)),
        "fallback_used": True,
        "fallback_reason": reason,
        "decision_timestamp": datetime.now(timezone.utc).isoformat(),
        "raw_score": round(float(raw_score), 6),
    }
