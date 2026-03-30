"""
Inference utilities for the Sentiment Agent.

Contract:
    {"signal": "BUY" | "SELL" | "HOLD", "confidence": float, "agent": "Sentiment"}
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Union

import joblib
import numpy as np
import pandas as pd

try:
    from .sentiment_agent_data import TIMEFRAME_RULES, build_latest_feature_row
except ImportError:
    from sentiment_agent_data import TIMEFRAME_RULES, build_latest_feature_row


CLASS_TO_SIGNAL = {1: "BUY", -1: "SELL", 0: "HOLD"}


def _align_feature_columns(pipeline, X: pd.DataFrame) -> pd.DataFrame:
    X_proc = X.select_dtypes(include=[np.number]).copy()
    if X_proc.shape[1] == 0:
        raise ValueError("No numeric features for SentimentAgent prediction.")

    if hasattr(pipeline, "feature_names_in_"):
        expected = list(pipeline.feature_names_in_)
    elif hasattr(pipeline.named_steps.get("scaler", None), "feature_names_in_"):
        expected = list(pipeline.named_steps["scaler"].feature_names_in_)
    else:
        return X_proc

    for col in expected:
        if col not in X_proc.columns:
            X_proc[col] = 0.0

    extra = [c for c in X_proc.columns if c not in expected]
    if extra:
        X_proc = X_proc.drop(columns=extra, errors="ignore")

    return X_proc[expected]


def _top_feature_importances(
    pipeline,
    feature_names: List[str],
    row_values: pd.Series,
    k: int = 5,
) -> List[Dict]:
    rf = pipeline.named_steps.get("rf")
    if rf is None or not hasattr(rf, "feature_importances_"):
        return []

    imp = rf.feature_importances_
    order = np.argsort(imp)[::-1][:k]

    out: List[Dict] = []
    for i in order:
        if i >= len(feature_names):
            continue
        name = feature_names[i]
        out.append(
            {
                "feature": name,
                "importance": float(imp[i]),
                "value": float(row_values.get(name, 0.0)),
            }
        )
    return out


class SentimentAgent:
    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        *,
        symbol: str = "EURUSD",
        timeframe: str = "1H",
    ):
        symbol = symbol.upper()
        timeframe = timeframe.upper()
        if timeframe not in TIMEFRAME_RULES:
            raise ValueError(f"Unsupported timeframe for SentimentAgent: {timeframe}")

        if model_path is None:
            model_path = (
                Path(__file__).resolve().parent
                / f"sentiment_agent_{symbol}_{timeframe}.pkl"
            )

        self.model_path = Path(model_path)
        self.symbol = symbol
        self.timeframe = timeframe

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model not found at {self.model_path}. Run train_sentiment_agent.py first."
            )

        self.pipeline = joblib.load(self.model_path)

    def predict(self, X: Union[pd.DataFrame, dict, pd.Series], explain: bool = False) -> Dict:
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame([X])

        X_proc = _align_feature_columns(self.pipeline, X)

        pred = self.pipeline.predict(X_proc)
        probs = None
        try:
            probs = self.pipeline.predict_proba(X_proc)
        except Exception:
            pass

        cls = int(pred[0])
        signal = CLASS_TO_SIGNAL.get(cls, "HOLD")
        confidence = float(np.max(probs[0])) if probs is not None else 1.0

        out: Dict = {
            "signal": signal,
            "confidence": confidence,
            "agent": "Sentiment",
        }

        if explain:
            names = list(X_proc.columns)
            row = X_proc.iloc[0]
            expl = _top_feature_importances(self.pipeline, names, row)
            if expl:
                out["explanation"] = expl

        return out

    def predict_latest(self, *, explain: bool = False) -> Dict:
        try:
            latest = build_latest_feature_row(self.symbol, self.timeframe)
            return self.predict(latest, explain=explain)
        except Exception as e:
            # Graceful fallback when news/DB is temporarily unavailable.
            if hasattr(self.pipeline, "feature_names_in_"):
                cols = list(self.pipeline.feature_names_in_)
                neutral_row = pd.DataFrame([{c: 0.0 for c in cols}])
                out = self.predict(neutral_row, explain=explain)
            else:
                out = {
                    "signal": "HOLD",
                    "confidence": 0.0,
                    "agent": "Sentiment",
                }
            out["warning"] = f"Fallback inference used: {e}"
            return out


def get_sentiment_signal(
    data: Union[pd.DataFrame, dict, pd.Series],
    *,
    model_path: Optional[Path] = None,
    explain: bool = False,
) -> Dict:
    agent = SentimentAgent(model_path=model_path)
    return agent.predict(data, explain=explain)


if __name__ == "__main__":
    mp = Path(__file__).resolve().parent / "sentiment_agent_EURUSD_1H.pkl"
    if mp.exists():
        agent = SentimentAgent(mp, symbol="EURUSD", timeframe="1H")
        try:
            print(agent.predict_latest(explain=True))
        except Exception as e:
            print(f"predict_latest failed: {e}")
    else:
        print(f"Train first; expected model at {mp}")
