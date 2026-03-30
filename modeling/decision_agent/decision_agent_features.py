"""Feature engineering for the Meta-Decision Agent.

This module transforms specialist-agent outputs into a deterministic,
model-ready feature vector.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import numpy as np

BUY_SELL_HOLD = {"BUY": 1, "HOLD": 0, "SELL": -1}

FEATURE_COLUMNS: List[str] = [
    "technical_signal_num",
    "technical_confidence",
    "technical_missing",
    "technical_freshness_sec",
    "technical_trend_strength",
    "technical_volatility_regime",
    "macro_signal_num",
    "macro_confidence",
    "macro_missing",
    "macro_freshness_sec",
    "macro_regime",
    "macro_event_risk_score",
    "sentiment_signal_num",
    "sentiment_confidence",
    "sentiment_missing",
    "sentiment_freshness_sec",
    "sentiment_score",
    "news_volume",
    "sentiment_momentum",
    "agreement_ratio",
    "conflict_index",
    "weighted_confidence",
    "missing_agent_count",
    "stale_agent_count",
    "timeframe_sec",
]


def _signal_to_num(signal: Optional[str]) -> int:
    if not signal:
        return 0
    return BUY_SELL_HOLD.get(str(signal).upper(), 0)


def _safe_confidence(value) -> float:
    try:
        c = float(value)
    except Exception:
        return 0.0
    return float(np.clip(c, 0.0, 1.0))


def _parse_iso_ts(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except Exception:
        return None


def _freshness_seconds(last_update: Optional[str], now_utc: datetime, default_if_unknown: int) -> int:
    dt = _parse_iso_ts(last_update)
    if dt is None:
        return int(default_if_unknown)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    diff = int((now_utc - dt).total_seconds())
    return max(0, diff)


def _is_missing(agent_payload: Dict) -> int:
    signal = str(agent_payload.get("signal", "N/A")).upper()
    if signal == "N/A":
        return 1
    if agent_payload.get("error"):
        return 1
    return 0


def _agreement_and_conflict(signal_nums: List[int], weights: List[float]) -> Tuple[float, float]:
    total_w = float(sum(weights))
    if total_w <= 1e-12:
        return 0.0, 1.0

    side_w = {1: 0.0, 0: 0.0, -1: 0.0}
    for s, w in zip(signal_nums, weights):
        side_w[int(np.clip(s, -1, 1))] += max(0.0, float(w))

    agreement_ratio = max(side_w.values()) / total_w
    conflict_index = float(np.clip(1.0 - agreement_ratio, 0.0, 1.0))
    return float(agreement_ratio), conflict_index


def _macro_regime(macro_payload: Dict) -> float:
    sig = _signal_to_num(macro_payload.get("signal"))
    conf = _safe_confidence(macro_payload.get("confidence"))
    return float(sig * conf)


def _macro_event_risk(macro_payload: Dict) -> float:
    expl = macro_payload.get("explanation") or []
    if not isinstance(expl, list):
        return 0.0
    return float(np.clip(len(expl) / 5.0, 0.0, 1.0))


def _sentiment_score(sent_payload: Dict) -> float:
    sig = _signal_to_num(sent_payload.get("signal"))
    conf = _safe_confidence(sent_payload.get("confidence"))
    return float(sig * conf)


def _sentiment_momentum(sent_payload: Dict) -> float:
    # Phase 1 proxy: confidence-weighted direction.
    return _sentiment_score(sent_payload)


def _news_volume_proxy(sent_payload: Dict) -> float:
    expl = sent_payload.get("explanation") or []
    if not isinstance(expl, list):
        return 0.0
    return float(np.clip(len(expl), 0, 20))


def _technical_trend_strength(tech_payload: Dict) -> float:
    sig = _signal_to_num(tech_payload.get("signal"))
    conf = _safe_confidence(tech_payload.get("confidence"))
    return float(abs(sig) * conf)


def _technical_vol_regime(tech_payload: Dict) -> float:
    # Phase 1 proxy: use confidence as a simple stability/vol proxy.
    return _safe_confidence(tech_payload.get("confidence"))


def _timeframe_seconds(timeframe: str) -> int:
    tf = str(timeframe or "1H").upper()
    mapping = {"LIVE": 1, "1S": 1, "1H": 3600, "4H": 14400, "1D": 86400}
    return mapping.get(tf, 3600)


def build_feature_vector(
    technical_payload: Dict,
    macro_payload: Dict,
    sentiment_payload: Dict,
    *,
    timeframe: str,
    now_utc: Optional[datetime] = None,
) -> Tuple[Dict[str, float], Dict]:
    """Build model-ready feature vector plus diagnostics for transparency."""
    now_utc = now_utc or datetime.now(timezone.utc)

    tech_sig = _signal_to_num(technical_payload.get("signal"))
    macro_sig = _signal_to_num(macro_payload.get("signal"))
    sent_sig = _signal_to_num(sentiment_payload.get("signal"))

    tech_conf = _safe_confidence(technical_payload.get("confidence"))
    macro_conf = _safe_confidence(macro_payload.get("confidence"))
    sent_conf = _safe_confidence(sentiment_payload.get("confidence"))

    tech_missing = _is_missing(technical_payload)
    macro_missing = _is_missing(macro_payload)
    sent_missing = _is_missing(sentiment_payload)

    tech_fresh = 0 if not tech_missing else 999999
    macro_fresh = _freshness_seconds(macro_payload.get("last_macro_update"), now_utc, 999999)
    sent_fresh = _freshness_seconds(sentiment_payload.get("last_sentiment_update"), now_utc, 999999)

    weights = [tech_conf * (1 - tech_missing), macro_conf * (1 - macro_missing), sent_conf * (1 - sent_missing)]
    signal_nums = [tech_sig, macro_sig, sent_sig]
    agreement_ratio, conflict_index = _agreement_and_conflict(signal_nums, weights)

    total_weight = float(sum(weights))
    weighted_conf = total_weight / 3.0

    stale_count = int(macro_fresh > 172800) + int(sent_fresh > 7200)
    missing_count = int(tech_missing + macro_missing + sent_missing)

    feats = {
        "technical_signal_num": float(tech_sig),
        "technical_confidence": tech_conf,
        "technical_missing": float(tech_missing),
        "technical_freshness_sec": float(tech_fresh),
        "technical_trend_strength": _technical_trend_strength(technical_payload),
        "technical_volatility_regime": _technical_vol_regime(technical_payload),
        "macro_signal_num": float(macro_sig),
        "macro_confidence": macro_conf,
        "macro_missing": float(macro_missing),
        "macro_freshness_sec": float(macro_fresh),
        "macro_regime": _macro_regime(macro_payload),
        "macro_event_risk_score": _macro_event_risk(macro_payload),
        "sentiment_signal_num": float(sent_sig),
        "sentiment_confidence": sent_conf,
        "sentiment_missing": float(sent_missing),
        "sentiment_freshness_sec": float(sent_fresh),
        "sentiment_score": _sentiment_score(sentiment_payload),
        "news_volume": _news_volume_proxy(sentiment_payload),
        "sentiment_momentum": _sentiment_momentum(sentiment_payload),
        "agreement_ratio": agreement_ratio,
        "conflict_index": conflict_index,
        "weighted_confidence": float(np.clip(weighted_conf, 0.0, 1.0)),
        "missing_agent_count": float(missing_count),
        "stale_agent_count": float(stale_count),
        "timeframe_sec": float(_timeframe_seconds(timeframe)),
    }

    # Enforce deterministic feature order/keys.
    ordered_feats = {k: float(feats.get(k, 0.0)) for k in FEATURE_COLUMNS}

    diagnostics = {
        "agreement_ratio": agreement_ratio,
        "conflict_index": conflict_index,
        "missing_agent_count": missing_count,
        "stale_agent_count": stale_count,
        "feature_columns": FEATURE_COLUMNS,
    }

    return ordered_feats, diagnostics
