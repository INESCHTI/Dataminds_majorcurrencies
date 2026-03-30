"""
Inference utilities for the Technical Agent.

Provides `get_technical_signal(data)` which returns a dict:
    {"signal": "BUY"/"SELL"/"HOLD", "confidence": float, "agent": "Technical"}

`data` can be a pandas DataFrame (single-row) or a dict/Series.
"""
from pathlib import Path
from typing import Union, Dict

import joblib
import numpy as np
import pandas as pd


PRICE_COL_PATTERNS = ["open", "high", "low", "close", "bid", "ask", "price", "volume"]


def _drop_price_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols_to_drop = [c for c in df.columns if any(p in c.lower() for p in PRICE_COL_PATTERNS)]
    return df.drop(columns=[c for c in cols_to_drop if c in df.columns], errors="ignore")


class TechnicalAgent:
    def __init__(self, model_path: Union[str, Path] = None):
        if model_path is None:
            model_path = Path(__file__).resolve().parent / "technical_agent_model.pkl"
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found at {self.model_path}. Train the agent first.")
        self.pipeline = joblib.load(self.model_path)

    def predict(self, X: pd.DataFrame) -> Dict:
        # Ensure X is a DataFrame with numeric features, drop price columns
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame([X])
        X_proc = X.select_dtypes(include=[np.number]).copy()
        X_proc = _drop_price_columns(X_proc)
        if X_proc.shape[1] == 0:
            raise ValueError("No numeric features available after dropping price columns.")

        # Align columns to match what the model was trained on
        if hasattr(self.pipeline, "feature_names_in_"):
            expected_cols = self.pipeline.feature_names_in_
            for col in expected_cols:
                if col not in X_proc.columns:
                    X_proc[col] = 0
            # Ensure exact order and drop any extra features unseen at fit time
            X_proc = X_proc[expected_cols]
        elif hasattr(self.pipeline.named_steps.get("scaler", None), "feature_names_in_"):
            expected_cols = self.pipeline.named_steps["scaler"].feature_names_in_
            for col in expected_cols:
                if col not in X_proc.columns:
                    X_proc[col] = 0
            X_proc = X_proc[expected_cols]

        pred = self.pipeline.predict(X_proc)
        probs = None
        try:
            probs = self.pipeline.predict_proba(X_proc)
        except Exception:
            pass

        cls = int(pred[0])
        # map to readable signal
        mapping = {1: "BUY", -1: "SELL", 0: "HOLD"}
        signal = mapping.get(cls, "HOLD")
        confidence = float(np.max(probs[0])) if probs is not None else 1.0
        return {"signal": signal, "confidence": float(confidence), "agent": "Technical"}


def get_technical_signal(data: Union[pd.DataFrame, dict, pd.Series]) -> Dict:
    """Helper wrapper that loads default model and returns signal."""
    agent = TechnicalAgent()
    return agent.predict(data)


if __name__ == "__main__":
    # Demo: load last row from default integrated file (if available)
    demo_csv = Path(__file__).resolve().parent / "../../data_understanding_outputs/integrated/integrated_EURUSD_1H.csv"
    demo_csv = demo_csv.resolve()
    if demo_csv.exists():
        import pandas as pd

        df = pd.read_csv(demo_csv)
        last_row = df.iloc[-1:]
        try:
            signal = get_technical_signal(last_row)
            print(signal)
        except Exception as e:
            print(f"Inference failed: {e}")
    else:
        print(f"Demo CSV not found at {demo_csv}; import and call get_technical_signal(data) in your app.")
