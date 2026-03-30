"""
Train Macro Agent models (RandomForest) for all FX symbols using PostgreSQL economic_indicators.

Mirrors technical_agent training style:
- sklearn Pipeline: SimpleImputer -> StandardScaler -> RandomForestClassifier
- Chronological 80/20 split (no shuffle)
- Target: next-day direction (1 / -1 / 0) for each pair-specific FRED series

Outputs:
    modeling/macro_agent/macro_agent_EURUSD.pkl
    modeling/macro_agent/macro_agent_GBPUSD.pkl
    modeling/macro_agent/macro_agent_USDJPY.pkl
    modeling/macro_agent/macro_agent_USDCHF.pkl

Usage:
    python train_macro_agent.py
"""
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from macro_agent_data import build_training_frame, load_economic_indicators_long


TARGET_SERIES_BY_SYMBOL = {
    "EURUSD": "DEXUSEU",
    "GBPUSD": "DEXUSUK",
    "USDJPY": "DEXJPUS",
    "USDCHF": "DEXSZUS",
}


def chronological_split(X, y, train_frac: float = 0.8):
    n = len(X)
    split = int(n * train_frac)
    X_train = X.iloc[:split].reset_index(drop=True)
    X_test = X.iloc[split:].reset_index(drop=True)
    y_train = y.iloc[:split].reset_index(drop=True)
    y_test = y.iloc[split:].reset_index(drop=True)
    return X_train, X_test, y_train, y_test


def train_one_symbol(df_long, script_dir: Path, symbol: str, target_series: str):
    out_path = script_dir / f"macro_agent_{symbol}.pkl"
    print()
    print("=" * 72)
    print(f"Training macro model for {symbol} (target series: {target_series})")
    print("=" * 72)

    X, y = build_training_frame(df_long, target_series=target_series)
    X = X.select_dtypes(include=[np.number])

    if X.shape[1] == 0:
        raise RuntimeError(f"No numeric feature columns after macro feature engineering for {symbol}.")

    print(f"  Feature matrix: {X.shape[0]} rows x {X.shape[1]} columns")
    _y_show = y.copy()
    _y_show.name = None
    print(f"  Target distribution:\n{_y_show.value_counts().sort_index()}")

    X_train, X_test, y_train, y_test = chronological_split(X, y, train_frac=0.8)

    pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "rf",
                RandomForestClassifier(
                    n_estimators=100,
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    print("  Training RandomForestClassifier (100 trees)...")
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)
    print("  Evaluation on chronological test set:")
    print(f"    Accuracy: {acc:.4f}")
    print(f"    F1 (macro): {f1:.4f}")
    print(classification_report(y_test, y_pred, zero_division=0))

    joblib.dump(pipeline, out_path)
    print(f"  Saved model to {out_path}")


def main():
    script_dir = Path(__file__).resolve().parent

    print("Loading economic_indicators from PostgreSQL...")
    df_long = load_economic_indicators_long()
    print(f"  Rows (long): {len(df_long):,}")

    for symbol, target_series in TARGET_SERIES_BY_SYMBOL.items():
        train_one_symbol(df_long, script_dir, symbol, target_series)


if __name__ == "__main__":
    main()
