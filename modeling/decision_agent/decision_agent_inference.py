"""Inference pipeline for the Meta-Decision Agent (Phase 1).

Phase 1 uses a Logistic Regression baseline when model artifacts are available,
with deterministic fallback synthesis otherwise.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

from .decision_agent_fallback import fallback_decision
from .decision_agent_features import FEATURE_COLUMNS, build_feature_vector

ROOT = Path(__file__).resolve().parent
MODEL_DIR = ROOT / "models"
LR_MODEL_PATH = MODEL_DIR / "decision_meta_model.pkl"
LR_METADATA_PATH = MODEL_DIR / "decision_meta_model_metadata.json"
RF_MODEL_PATH = MODEL_DIR / "decision_meta_rf_model.pkl"
RF_METADATA_PATH = MODEL_DIR / "decision_meta_rf_model_metadata.json"
LR_CALIBRATION_PATH = MODEL_DIR / "decision_meta_lr_calibration.json"
RF_CALIBRATION_PATH = MODEL_DIR / "decision_meta_rf_calibration.json"

_CLASS_TO_SIGNAL = {1: "BUY", 0: "HOLD", -1: "SELL"}
_SIGNAL_TO_CLASS = {"BUY": 1, "HOLD": 0, "SELL": -1}


class DecisionMetaAgent:
    def __init__(
        self,
        model_path: Optional[Path] = None,
        metadata_path: Optional[Path] = None,
        *,
        min_confidence: float = 0.55,
        primary_model: str = "auto",
    ):
        self.model_path = Path(model_path) if model_path else LR_MODEL_PATH
        self.metadata_path = Path(metadata_path) if metadata_path else LR_METADATA_PATH
        self.min_confidence = float(min_confidence)
        self.primary_model = str(primary_model or "auto").lower()

        self.model = None
        self.metadata: Dict = {}

        self.model_registry: Dict[str, object] = {}
        self.metadata_registry: Dict[str, Dict] = {}
        self.calibration_registry: Dict[str, Dict] = {}
        self.feature_columns = list(FEATURE_COLUMNS)
        self.active_model_key = "logistic_regression"

        self._load_artifacts()

    @property
    def model_loaded(self) -> bool:
        return self.model is not None

    def _load_artifacts(self):
        # Load Logistic Regression artifacts.
        if self.metadata_path.exists():
            try:
                lr_meta = json.loads(self.metadata_path.read_text(encoding="utf-8"))
                self.metadata_registry["logistic_regression"] = lr_meta
                cols = lr_meta.get("feature_columns")
                if isinstance(cols, list) and cols:
                    self.feature_columns = [str(c) for c in cols]
            except Exception:
                pass

        if self.model_path.exists():
            try:
                self.model_registry["logistic_regression"] = joblib.load(self.model_path)
            except Exception:
                pass

        if LR_CALIBRATION_PATH.exists():
            try:
                self.calibration_registry["logistic_regression"] = json.loads(
                    LR_CALIBRATION_PATH.read_text(encoding="utf-8")
                )
            except Exception:
                pass

        # Load Random Forest artifacts.
        if RF_METADATA_PATH.exists():
            try:
                rf_meta = json.loads(RF_METADATA_PATH.read_text(encoding="utf-8"))
                self.metadata_registry["random_forest"] = rf_meta
                if not self.feature_columns:
                    cols = rf_meta.get("feature_columns")
                    if isinstance(cols, list) and cols:
                        self.feature_columns = [str(c) for c in cols]
            except Exception:
                pass

        if RF_MODEL_PATH.exists():
            try:
                self.model_registry["random_forest"] = joblib.load(RF_MODEL_PATH)
            except Exception:
                pass

        if RF_CALIBRATION_PATH.exists():
            try:
                self.calibration_registry["random_forest"] = json.loads(
                    RF_CALIBRATION_PATH.read_text(encoding="utf-8")
                )
            except Exception:
                pass

        # Select active model.
        pref = self.primary_model
        if pref == "auto":
            pref = "random_forest" if "random_forest" in self.model_registry else "logistic_regression"

        if pref in self.model_registry:
            self.active_model_key = pref
        elif "logistic_regression" in self.model_registry:
            self.active_model_key = "logistic_regression"
        elif "random_forest" in self.model_registry:
            self.active_model_key = "random_forest"

        self.model = self.model_registry.get(self.active_model_key)
        self.metadata = self.metadata_registry.get(self.active_model_key, {})

    def _resolve_model_key(self, model_override: Optional[str]) -> str:
        if not model_override:
            return self.active_model_key

        raw = str(model_override).strip().lower()
        aliases = {
            "auto": "auto",
            "rf": "random_forest",
            "random_forest": "random_forest",
            "lr": "logistic_regression",
            "logistic": "logistic_regression",
            "logistic_regression": "logistic_regression",
        }
        normalized = aliases.get(raw)
        if normalized is None:
            return self.active_model_key
        if normalized == "auto":
            return self.active_model_key
        if normalized in self.model_registry:
            return normalized
        return self.active_model_key

    def _align_features(self, features: Dict[str, float]) -> pd.DataFrame:
        row = {c: float(features.get(c, 0.0)) for c in self.feature_columns}
        return pd.DataFrame([row], columns=self.feature_columns)

    def _calibrate_confidence(self, model_key: str, raw_confidence: float) -> Tuple[float, Optional[Dict]]:
        """Map raw confidence to calibrated confidence using held-out reliability table."""
        raw = float(np.clip(raw_confidence, 0.0, 1.0))
        calib = self.calibration_registry.get(model_key)
        if not calib:
            return raw, None

        table = calib.get("table") if isinstance(calib, dict) else None
        if not isinstance(table, list) or not table:
            return raw, None

        for row in table:
            try:
                lo = float(row.get("low", 0.0))
                hi = float(row.get("high", 1.0))
                acc = row.get("empirical_accuracy")
                if acc is None:
                    continue
                hit = (raw >= lo and raw < hi) or (raw == 1.0 and hi >= 1.0)
                if hit:
                    return float(np.clip(float(acc), 0.0, 1.0)), {
                        "method": str(calib.get("method", "bin_accuracy_mapping")),
                        "bin_low": round(lo, 6),
                        "bin_high": round(hi, 6),
                    }
            except Exception:
                continue

        return raw, None

    def _predict_with_model(
        self,
        model_obj,
        model_key: str,
        X: pd.DataFrame,
    ) -> Tuple[str, float, Dict[str, float], List[Dict]]:
        probs = model_obj.predict_proba(X)
        classes = [int(c) for c in list(model_obj.classes_)]
        p = [float(v) for v in probs[0].tolist()]
        class_to_prob = dict(zip(classes, p))

        best_class = max(class_to_prob.items(), key=lambda kv: kv[1])[0]
        final_signal = _CLASS_TO_SIGNAL.get(best_class, "HOLD")
        confidence = float(class_to_prob.get(best_class, 0.0))

        prob_payload = {
            "buy": float(class_to_prob.get(1, 0.0)),
            "hold": float(class_to_prob.get(0, 0.0)),
            "sell": float(class_to_prob.get(-1, 0.0)),
        }

        feature_importance = self._local_feature_importance(model_obj, model_key, X, best_class)
        return final_signal, confidence, prob_payload, feature_importance

    def _local_feature_importance(self, model_obj, model_key: str, X: pd.DataFrame, selected_class: int) -> List[Dict]:
        # For Logistic Regression, use |coef * value| as local contribution proxy.
        # For Random Forest, use feature_importances_ weighted by current feature values.
        est = model_obj
        if hasattr(est, "named_steps"):
            for _, step in est.named_steps.items():
                if hasattr(step, "coef_") or hasattr(step, "feature_importances_"):
                    est = step
                    break

        values = X.iloc[0].to_numpy(dtype=float)
        cols = list(X.columns)

        contrib = None
        if hasattr(est, "coef_") and hasattr(est, "classes_"):
            classes = [int(c) for c in list(est.classes_)]
            if selected_class not in classes:
                return []

            class_idx = classes.index(selected_class)
            coefs = np.asarray(est.coef_[class_idx], dtype=float)
            contrib = np.abs(coefs * values)
        elif hasattr(est, "feature_importances_"):
            importances = np.asarray(est.feature_importances_, dtype=float)
            if importances.shape[0] != values.shape[0]:
                return []
            contrib = np.abs(importances * values)
        else:
            return []

        order = np.argsort(contrib)[::-1][:8]
        out = []
        for i in order:
            out.append(
                {
                    "feature": cols[i],
                    "importance": float(contrib[i]),
                    "value": float(values[i]),
                }
            )
        return out

    def _risk_flags(self, diagnostics: Dict, technical: Dict, macro: Dict, sentiment: Dict) -> List[str]:
        flags: List[str] = []

        if int(diagnostics.get("missing_agent_count", 0)) > 0:
            flags.append("missing_agent")
        if int(diagnostics.get("stale_agent_count", 0)) > 0:
            flags.append("stale_agent")
        if float(diagnostics.get("conflict_index", 0.0)) >= 0.65:
            flags.append("high_conflict")

        for payload in (technical, macro, sentiment):
            if payload.get("warning"):
                flags.append("agent_warning")
            if payload.get("error"):
                flags.append("agent_error")

        return sorted(set(flags))

    def predict(
        self,
        symbol: str,
        timeframe: str,
        technical_payload: Dict,
        macro_payload: Dict,
        sentiment_payload: Dict,
        model_override: Optional[str] = None,
    ) -> Dict:
        t0 = time.perf_counter()

        features, diagnostics = build_feature_vector(
            technical_payload,
            macro_payload,
            sentiment_payload,
            timeframe=timeframe,
            now_utc=datetime.now(timezone.utc),
        )

        risk_flags = self._risk_flags(diagnostics, technical_payload, macro_payload, sentiment_payload)

        fallback_reason = None
        fallback_needed = False

        selected_model_key = self._resolve_model_key(model_override)
        selected_model = self.model_registry.get(selected_model_key)
        selected_meta = self.metadata_registry.get(selected_model_key, self.metadata)

        if selected_model is None:
            fallback_needed = True
            fallback_reason = "meta_model_not_loaded"
        elif int(diagnostics.get("missing_agent_count", 0)) >= 2:
            fallback_needed = True
            fallback_reason = "too_many_missing_agents"

        if fallback_needed:
            resp = fallback_decision(
                symbol,
                timeframe,
                technical_payload,
                macro_payload,
                sentiment_payload,
                reason=fallback_reason,
                risk_flags=risk_flags,
            )
            resp["conflict_index"] = float(diagnostics.get("conflict_index", 0.0))
            resp["latency_ms"] = int((time.perf_counter() - t0) * 1000)
            return resp

        X = self._align_features(features)
        primary_model = selected_model
        primary_key = selected_model_key
        final_signal, confidence, probs, feature_importance = self._predict_with_model(primary_model, primary_key, X)
        calibrated_confidence, calibration_info = self._calibrate_confidence(primary_key, confidence)

        model_comparison = None
        shadow_key = "random_forest" if primary_key == "logistic_regression" else "logistic_regression"
        shadow_model = self.model_registry.get(shadow_key)
        if shadow_model is not None:
            shadow_signal, shadow_conf, shadow_probs, _ = self._predict_with_model(shadow_model, shadow_key, X)
            model_comparison = {
                "primary_model": primary_key,
                "primary_signal": final_signal,
                "primary_confidence": round(float(confidence), 6),
                "shadow_model": shadow_key,
                "shadow_signal": shadow_signal,
                "shadow_confidence": round(float(shadow_conf), 6),
                "shadow_probabilities": {k: round(v, 6) for k, v in shadow_probs.items()},
                "agreement": bool(shadow_signal == final_signal),
                "confidence_delta": round(float(confidence - shadow_conf), 6),
            }

        if calibrated_confidence < self.min_confidence:
            resp = fallback_decision(
                symbol,
                timeframe,
                technical_payload,
                macro_payload,
                sentiment_payload,
                reason=f"low_ai_confidence<{self.min_confidence}",
                risk_flags=sorted(set(risk_flags + ["low_ai_confidence"])),
            )
            resp["conflict_index"] = float(diagnostics.get("conflict_index", 0.0))
            resp["latency_ms"] = int((time.perf_counter() - t0) * 1000)
            return resp

        contributing_agents = {
            "technical": {
                "signal": technical_payload.get("signal", "N/A"),
                "confidence": float(technical_payload.get("confidence", 0.0) or 0.0),
                "warning": technical_payload.get("warning"),
                "error": technical_payload.get("error"),
            },
            "macro": {
                "signal": macro_payload.get("signal", "N/A"),
                "confidence": float(macro_payload.get("confidence", 0.0) or 0.0),
                "warning": macro_payload.get("warning"),
                "error": macro_payload.get("error"),
                "last_update": macro_payload.get("last_macro_update"),
            },
            "sentiment": {
                "signal": sentiment_payload.get("signal", "N/A"),
                "confidence": float(sentiment_payload.get("confidence", 0.0) or 0.0),
                "warning": sentiment_payload.get("warning"),
                "error": sentiment_payload.get("error"),
                "last_update": sentiment_payload.get("last_sentiment_update"),
            },
        }

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "final_signal": final_signal,
            "global_confidence": round(float(calibrated_confidence), 6),
            "raw_global_confidence": round(float(confidence), 6),
            "confidence_calibration": calibration_info,
            "model_type": str(selected_meta.get("model_type", primary_key)),
            "model_version": str(selected_meta.get("model_version", "decision_meta_v1")),
            "probabilities": {k: round(v, 6) for k, v in probs.items()},
            "feature_importance": feature_importance,
            "conflict_index": float(diagnostics.get("conflict_index", 0.0)),
            "contributing_agents": contributing_agents,
            "model_comparison": model_comparison,
            "risk_flags": risk_flags,
            "fallback_used": False,
            "fallback_reason": None,
            "decision_timestamp": datetime.now(timezone.utc).isoformat(),
            "latency_ms": int((time.perf_counter() - t0) * 1000),
        }
