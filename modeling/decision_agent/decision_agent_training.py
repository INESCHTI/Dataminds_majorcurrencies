"""Training pipeline for Phase 1 Meta-Decision Agent.

Phase 1 baseline: Logistic Regression (multiclass BUY/HOLD/SELL).

Expected input CSV:
- Feature columns matching FEATURE_COLUMNS (or subset)
- target column in {-1, 0, 1}
"""
from __future__ import annotations

import json
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .decision_agent_features import FEATURE_COLUMNS

ROOT = Path(__file__).resolve().parent
MODEL_DIR = ROOT / "models"
TRAINING_DIR = ROOT / "training_data"
DEFAULT_INPUT = TRAINING_DIR / "decision_training_data.csv"
DEFAULT_MODEL = MODEL_DIR / "decision_meta_model.pkl"
DEFAULT_META = MODEL_DIR / "decision_meta_model_metadata.json"
DEFAULT_RF_MODEL = MODEL_DIR / "decision_meta_rf_model.pkl"
DEFAULT_RF_META = MODEL_DIR / "decision_meta_rf_model_metadata.json"
DEFAULT_SCHEMA = MODEL_DIR / "decision_feature_schema.json"
DEFAULT_LR_CALIBRATION = MODEL_DIR / "decision_meta_lr_calibration.json"
DEFAULT_RF_CALIBRATION = MODEL_DIR / "decision_meta_rf_calibration.json"


def _chronological_split(X: pd.DataFrame, y: pd.Series, test_size: float = 0.2):
    n = len(X)
    split = max(1, int(n * (1.0 - test_size)))
    return X.iloc[:split], X.iloc[split:], y.iloc[:split], y.iloc[split:]


def _prepare_features(df: pd.DataFrame, feature_cols: List[str]) -> pd.DataFrame:
    X = df.copy()
    for c in feature_cols:
        if c not in X.columns:
            X[c] = 0.0
    X = X[feature_cols]
    X = X.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return X


def _generate_mock_training_data(output_csv: Path, n_rows: int = 3000, seed: int = 42) -> pd.DataFrame:
    """Generate deterministic synthetic Phase 1 training data.

    This is used when historical decision-agent output snapshots are not available yet.
    """
    rng = np.random.default_rng(seed)

    technical_signal_num = rng.choice([-1, 0, 1], size=n_rows, p=[0.36, 0.28, 0.36]).astype(float)
    macro_signal_num = rng.choice([-1, 0, 1], size=n_rows, p=[0.34, 0.32, 0.34]).astype(float)
    sentiment_signal_num = rng.choice([-1, 0, 1], size=n_rows, p=[0.35, 0.30, 0.35]).astype(float)

    technical_confidence = rng.uniform(0.35, 0.98, size=n_rows)
    macro_confidence = rng.uniform(0.30, 0.95, size=n_rows)
    sentiment_confidence = rng.uniform(0.25, 0.92, size=n_rows)

    technical_missing = rng.binomial(1, 0.03, size=n_rows).astype(float)
    macro_missing = rng.binomial(1, 0.06, size=n_rows).astype(float)
    sentiment_missing = rng.binomial(1, 0.07, size=n_rows).astype(float)

    technical_confidence = technical_confidence * (1.0 - technical_missing)
    macro_confidence = macro_confidence * (1.0 - macro_missing)
    sentiment_confidence = sentiment_confidence * (1.0 - sentiment_missing)

    technical_signal_num = technical_signal_num * (1.0 - technical_missing)
    macro_signal_num = macro_signal_num * (1.0 - macro_missing)
    sentiment_signal_num = sentiment_signal_num * (1.0 - sentiment_missing)

    # Recency proxies
    technical_freshness_sec = np.where(technical_missing > 0, 999999.0, rng.integers(0, 20, size=n_rows)).astype(float)
    macro_freshness_sec = np.where(macro_missing > 0, 999999.0, rng.integers(0, 240000, size=n_rows)).astype(float)
    sentiment_freshness_sec = np.where(sentiment_missing > 0, 999999.0, rng.integers(0, 18000, size=n_rows)).astype(float)

    technical_trend_strength = np.abs(technical_signal_num) * technical_confidence
    technical_volatility_regime = technical_confidence

    macro_regime = macro_signal_num * macro_confidence
    macro_event_risk_score = rng.uniform(0.0, 1.0, size=n_rows)

    sentiment_score = sentiment_signal_num * sentiment_confidence
    news_volume = rng.integers(0, 16, size=n_rows).astype(float)
    sentiment_momentum = sentiment_score + rng.normal(0.0, 0.10, size=n_rows)

    weighted_sum = (
        0.45 * technical_signal_num * technical_confidence
        + 0.30 * macro_signal_num * macro_confidence
        + 0.25 * sentiment_signal_num * sentiment_confidence
    )
    total_w = 0.45 * technical_confidence + 0.30 * macro_confidence + 0.25 * sentiment_confidence
    total_w = np.where(total_w <= 1e-8, 1.0, total_w)
    raw_score = weighted_sum / total_w

    agreement_ratio = 1.0 - np.clip(np.abs(technical_signal_num - macro_signal_num) + np.abs(technical_signal_num - sentiment_signal_num), 0, 4) / 4.0
    conflict_index = 1.0 - agreement_ratio
    weighted_confidence = np.clip((technical_confidence + macro_confidence + sentiment_confidence) / 3.0, 0.0, 1.0)

    missing_agent_count = technical_missing + macro_missing + sentiment_missing
    stale_agent_count = (macro_freshness_sec > 172800).astype(float) + (sentiment_freshness_sec > 7200).astype(float)
    timeframe_sec = rng.choice([1.0, 3600.0, 14400.0, 86400.0], size=n_rows, p=[0.05, 0.60, 0.20, 0.15])

    decision_score = (
        1.25 * raw_score
        + 0.35 * (1.0 - conflict_index)
        + 0.20 * (weighted_confidence - 0.5)
        - 0.40 * (missing_agent_count / 3.0)
        - 0.15 * (stale_agent_count / 2.0)
        + rng.normal(0.0, 0.12, size=n_rows)
    )

    target = np.where(decision_score > 0.25, 1, np.where(decision_score < -0.25, -1, 0)).astype(int)

    df = pd.DataFrame(
        {
            "technical_signal_num": technical_signal_num,
            "technical_confidence": technical_confidence,
            "technical_missing": technical_missing,
            "technical_freshness_sec": technical_freshness_sec,
            "technical_trend_strength": technical_trend_strength,
            "technical_volatility_regime": technical_volatility_regime,
            "macro_signal_num": macro_signal_num,
            "macro_confidence": macro_confidence,
            "macro_missing": macro_missing,
            "macro_freshness_sec": macro_freshness_sec,
            "macro_regime": macro_regime,
            "macro_event_risk_score": macro_event_risk_score,
            "sentiment_signal_num": sentiment_signal_num,
            "sentiment_confidence": sentiment_confidence,
            "sentiment_missing": sentiment_missing,
            "sentiment_freshness_sec": sentiment_freshness_sec,
            "sentiment_score": sentiment_score,
            "news_volume": news_volume,
            "sentiment_momentum": sentiment_momentum,
            "agreement_ratio": np.clip(agreement_ratio, 0.0, 1.0),
            "conflict_index": np.clip(conflict_index, 0.0, 1.0),
            "weighted_confidence": weighted_confidence,
            "missing_agent_count": missing_agent_count,
            "stale_agent_count": stale_agent_count,
            "timeframe_sec": timeframe_sec,
            "target": target,
        }
    )

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    return df


def _save_feature_schema(schema_path: Path, feature_cols: List[str], target_col: str) -> None:
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "decision_meta_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "feature_columns": feature_cols,
        "feature_count": len(feature_cols),
        "target_column": target_col,
        "target_labels": {"SELL": -1, "HOLD": 0, "BUY": 1},
    }
    schema_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _load_or_create_training_df(input_csv: Path, target_col: str) -> pd.DataFrame:
    if not input_csv.exists():
        print(f"Training dataset not found at {input_csv}; generating deterministic mock dataset for Phase 1/2.")
        df = _generate_mock_training_data(input_csv)
    else:
        df = pd.read_csv(input_csv)

    if target_col not in df.columns:
        raise ValueError(f"Missing target column '{target_col}' in {input_csv}")
    return df


def _build_confidence_calibration(y_true: pd.Series, y_pred: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> Dict:
    """Build a simple confidence-to-accuracy calibration table from held-out data."""
    max_prob = np.max(y_prob, axis=1)
    correct = (np.asarray(y_pred) == np.asarray(y_true)).astype(float)

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    table = []
    ece = 0.0

    for i in range(n_bins):
        lo = float(bins[i])
        hi = float(bins[i + 1])
        if i < n_bins - 1:
            mask = (max_prob >= lo) & (max_prob < hi)
        else:
            mask = (max_prob >= lo) & (max_prob <= hi)

        count = int(np.sum(mask))
        if count == 0:
            acc = None
            conf = None
        else:
            acc = float(np.mean(correct[mask]))
            conf = float(np.mean(max_prob[mask]))
            ece += abs(acc - conf) * (count / max(1, len(max_prob)))

        table.append(
            {
                "low": round(lo, 6),
                "high": round(hi, 6),
                "count": count,
                "empirical_accuracy": None if acc is None else round(acc, 6),
                "avg_confidence": None if conf is None else round(conf, 6),
            }
        )

    return {
        "method": "bin_accuracy_mapping",
        "n_bins": int(n_bins),
        "expected_calibration_error": round(float(ece), 6),
        "table": table,
    }


def train_phase1(
    input_csv: Path = DEFAULT_INPUT,
    model_path: Path = DEFAULT_MODEL,
    metadata_path: Path = DEFAULT_META,
    schema_path: Path = DEFAULT_SCHEMA,
    *,
    target_col: str = "target",
    test_size: float = 0.2,
) -> None:
    df = _load_or_create_training_df(input_csv, target_col)

    y = pd.to_numeric(df[target_col], errors="coerce").fillna(0).astype(int)
    y = y.clip(-1, 1)

    feature_cols = list(FEATURE_COLUMNS)
    X = _prepare_features(df, feature_cols)

    if len(X) < 100:
        raise ValueError(f"Not enough rows for training ({len(X)}). Need at least 100.")

    X_train, X_test, y_train, y_test = _chronological_split(X, y, test_size=test_size)

    model = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "lr",
                LogisticRegression(
                    solver="lbfgs",
                    max_iter=1200,
                    random_state=42,
                ),
            ),
        ]
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)
    acc = float(accuracy_score(y_test, y_pred))
    f1m = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
    calibration = _build_confidence_calibration(y_test, y_pred, y_prob, n_bins=10)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    DEFAULT_LR_CALIBRATION.write_text(json.dumps(calibration, indent=2), encoding="utf-8")

    metadata = {
        "model_type": "logistic_regression",
        "model_version": "decision_meta_lr_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "feature_columns": feature_cols,
        "target_column": target_col,
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "accuracy": acc,
        "f1_macro": f1m,
        "classes": [int(v) for v in sorted(pd.unique(y).tolist())],
        "input_csv": str(input_csv),
        "calibration_artifact": str(DEFAULT_LR_CALIBRATION),
        "calibration_method": calibration.get("method"),
        "expected_calibration_error": calibration.get("expected_calibration_error"),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    _save_feature_schema(schema_path, feature_cols, target_col)

    print("=" * 72)
    print("Decision Agent Phase 1 training complete")
    print("=" * 72)
    print(f"Train rows: {len(X_train)} | Test rows: {len(X_test)}")
    print(f"Accuracy: {acc:.4f}")
    print(f"F1 macro: {f1m:.4f}")
    print(classification_report(y_test, y_pred, zero_division=0))
    print(f"Saved model: {model_path}")
    print(f"Saved metadata: {metadata_path}")
    print(f"Saved schema: {schema_path}")


def train_phase2_random_forest(
    input_csv: Path = DEFAULT_INPUT,
    model_path: Path = DEFAULT_RF_MODEL,
    metadata_path: Path = DEFAULT_RF_META,
    schema_path: Path = DEFAULT_SCHEMA,
    *,
    target_col: str = "target",
    test_size: float = 0.2,
) -> None:
    """Train Random Forest Phase 2 model artifact."""
    df = _load_or_create_training_df(input_csv, target_col)

    y = pd.to_numeric(df[target_col], errors="coerce").fillna(0).astype(int)
    y = y.clip(-1, 1)

    feature_cols = list(FEATURE_COLUMNS)
    X = _prepare_features(df, feature_cols)

    if len(X) < 100:
        raise ValueError(f"Not enough rows for training ({len(X)}). Need at least 100.")

    X_train, X_test, y_train, y_test = _chronological_split(X, y, test_size=test_size)

    rf = RandomForestClassifier(
        n_estimators=300,
        max_depth=10,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
        class_weight="balanced_subsample",
    )
    rf.fit(X_train, y_train)

    y_pred = rf.predict(X_test)
    y_prob = rf.predict_proba(X_test)
    acc = float(accuracy_score(y_test, y_pred))
    f1m = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
    calibration = _build_confidence_calibration(y_test, y_pred, y_prob, n_bins=10)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(rf, model_path)
    DEFAULT_RF_CALIBRATION.write_text(json.dumps(calibration, indent=2), encoding="utf-8")

    metadata = {
        "model_type": "random_forest",
        "model_version": "decision_meta_rf_v2",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "feature_columns": feature_cols,
        "target_column": target_col,
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "accuracy": acc,
        "f1_macro": f1m,
        "classes": [int(v) for v in sorted(pd.unique(y).tolist())],
        "input_csv": str(input_csv),
        "calibration_artifact": str(DEFAULT_RF_CALIBRATION),
        "calibration_method": calibration.get("method"),
        "expected_calibration_error": calibration.get("expected_calibration_error"),
        "hyperparameters": {
            "n_estimators": 300,
            "max_depth": 10,
            "min_samples_leaf": 3,
            "class_weight": "balanced_subsample",
        },
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    _save_feature_schema(schema_path, feature_cols, target_col)

    print("=" * 72)
    print("Decision Agent Phase 2 Random Forest training complete")
    print("=" * 72)
    print(f"Train rows: {len(X_train)} | Test rows: {len(X_test)}")
    print(f"Accuracy: {acc:.4f}")
    print(f"F1 macro: {f1m:.4f}")
    print(classification_report(y_test, y_pred, zero_division=0))
    print(f"Saved model: {model_path}")
    print(f"Saved metadata: {metadata_path}")
    print(f"Saved schema: {schema_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train decision meta models (LR and/or RF).")
    parser.add_argument("--model", choices=["lr", "rf", "all"], default="all")
    args = parser.parse_args()

    if args.model in ("lr", "all"):
        train_phase1()
    if args.model in ("rf", "all"):
        train_phase2_random_forest()
