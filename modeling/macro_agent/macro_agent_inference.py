"""
Inference utilities for the Macro Agent.

Same contract as TechnicalAgent.predict:
    {"signal": "BUY" | "SELL" | "HOLD", "confidence": float, "agent": "Macro"}

Optional keys (bonus):
    "explanation": list of {feature, importance} for top macro drivers
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Union

import joblib
import numpy as np
import pandas as pd

try:
    from .macro_agent_data import (
        TARGET_SERIES_EURUSD,
        engineer_macro_features,
        load_economic_indicators_long,
        pivot_indicators,
    )
except ImportError:
    from macro_agent_data import (
        TARGET_SERIES_EURUSD,
        engineer_macro_features,
        load_economic_indicators_long,
        pivot_indicators,
    )


CLASS_TO_SIGNAL = {1: "BUY", -1: "SELL", 0: "HOLD"}

TARGET_SERIES_BY_SYMBOL = {
    "EURUSD": "DEXUSEU",
    "GBPUSD": "DEXUSUK",
    "USDJPY": "DEXJPUS",
    "USDCHF": "DEXSZUS",
}


def _align_feature_columns(pipeline, X: pd.DataFrame) -> pd.DataFrame:
    X_proc = X.select_dtypes(include=[np.number]).copy()
    if X_proc.shape[1] == 0:
        raise ValueError("No numeric features for MacroAgent prediction.")

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


def _top_feature_importances(pipeline, feature_names: List[str], k: int = 5) -> List[Dict]:
    rf = pipeline.named_steps.get("rf")
    if rf is None or not hasattr(rf, "feature_importances_"):
        return []
    imp = rf.feature_importances_
    order = np.argsort(imp)[::-1][:k]
    return [{"feature": feature_names[i], "importance": float(imp[i])} for i in order if i < len(feature_names)]


class MacroAgent:
    """
    Load macro_agent_EURUSD.pkl and predict from a single-row feature DataFrame
    or build the latest row from PostgreSQL.
    """

    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        *,
        symbol: str = "EURUSD",
    ):
        if model_path is None:
            model_path = Path(__file__).resolve().parent / f"macro_agent_{symbol.upper()}.pkl"
        self.model_path = Path(model_path)
        self.symbol = symbol.upper()
        self.target_series = TARGET_SERIES_BY_SYMBOL.get(self.symbol, TARGET_SERIES_EURUSD)
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model not found at {self.model_path}. Run train_macro_agent.py first."
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
            "agent": "Macro",
        }
        if explain:
            names = list(X_proc.columns)
            expl = _top_feature_importances(self.pipeline, names)
            if expl:
                out["explanation"] = expl
        return out

    def predict_latest(
        self,
        *,
        explain: bool = False,
        df_long: Optional[pd.DataFrame] = None,
    ) -> Dict:
        """
        Load latest macro data from PostgreSQL, engineer features, use last valid row.
        """
        if df_long is None:
            df_long = load_economic_indicators_long()
        piv = pivot_indicators(df_long)
        if self.target_series not in piv.columns:
            raise ValueError(
                f"Missing {self.target_series} in economic data for {self.symbol} macro agent."
            )

        X_full = engineer_macro_features(piv)
        X_full = X_full.replace([np.inf, -np.inf], np.nan)
        X_num = X_full.select_dtypes(include=[np.number])
        last = X_num.iloc[[-1]].copy()
        return self.predict(last, explain=explain)


def get_macro_signal(
    data: Union[pd.DataFrame, dict, pd.Series],
    *,
    model_path: Optional[Path] = None,
    explain: bool = False,
) -> Dict:
    agent = MacroAgent(model_path)
    return agent.predict(data, explain=explain)


if __name__ == "__main__":
    mp = Path(__file__).resolve().parent / "macro_agent_EURUSD.pkl"
    if mp.exists():
        agent = MacroAgent(mp, symbol="EURUSD")
        try:
            print(agent.predict_latest(explain=True))
        except Exception as e:
            print(f"predict_latest failed: {e}")
    else:
        print(f"Train first; expected model at {mp}")
