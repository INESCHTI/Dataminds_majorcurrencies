"""
Train Sentiment Agent models for all symbols and timeframes.

Outputs:
    modeling/sentiment_agent/sentiment_agent_{SYMBOL}_{TIMEFRAME}.pkl

Usage:
    python train_sentiment_agent.py
"""
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from sentiment_agent_data import SYMBOLS, TIMEFRAME_RULES, build_training_frame


def chronological_split(X, y, train_frac: float = 0.8):
    n = len(X)
    split = int(n * train_frac)
    X_train = X.iloc[:split].reset_index(drop=True)
    X_test = X.iloc[split:].reset_index(drop=True)
    y_train = y.iloc[:split].reset_index(drop=True)
    y_test = y.iloc[split:].reset_index(drop=True)
    return X_train, X_test, y_train, y_test


def trim_leading_flat_rows(X, y, eps: float = 1e-12):
    """Drop early rows where all sentiment features are effectively zero.

    This avoids training on long flat windows before news features become informative.
    """
    if X.empty:
        return X, y, 0

    row_energy = X.abs().sum(axis=1)
    informative_mask = row_energy > eps
    if not informative_mask.any():
        return X, y, 0

    first_idx = int(informative_mask.idxmax())
    if first_idx <= 0:
        return X, y, 0

    return X.iloc[first_idx:].reset_index(drop=True), y.iloc[first_idx:].reset_index(drop=True), first_idx


def train_one(symbol: str, timeframe: str, script_dir: Path) -> bool:
    out_path = script_dir / f"sentiment_agent_{symbol}_{timeframe}.pkl"

    print()
    print("=" * 72)
    print(f"Training sentiment model for {symbol} {timeframe}")
    print("=" * 72)

    try:
        X, y = build_training_frame(symbol, timeframe)
    except Exception as e:
        print(f"  Skipped: {e}")
        return False

    X, y, trimmed = trim_leading_flat_rows(X, y)
    if trimmed > 0:
        print(f"  Trimmed leading flat rows: {trimmed}")

    if len(X) < 50:
        print(f"  Skipped: not enough rows ({len(X)})")
        return False

    print(f"  Feature matrix: {X.shape[0]} rows x {X.shape[1]} columns")
    print(f"  Target distribution:\n{y.value_counts().sort_index()}")

    X_train, X_test, y_train, y_test = chronological_split(X, y, train_frac=0.8)

    pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "rf",
                RandomForestClassifier(
                    n_estimators=150,
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )

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
    return True


def main():
    script_dir = Path(__file__).resolve().parent
    saved = 0

    for symbol in SYMBOLS:
        for timeframe in TIMEFRAME_RULES.keys():
            ok = train_one(symbol, timeframe, script_dir)
            saved += int(ok)

    print()
    print(f"Training complete. Models saved: {saved}")


if __name__ == "__main__":
    main()
