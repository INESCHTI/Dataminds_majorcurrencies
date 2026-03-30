"""
Train the Technical Agent (RandomForest) using integrated CSVs.

Usage:
    python train_technical_agent.py --input ../../data_understanding_outputs/integrated/integrated_EURUSD_1H.csv

Creates:
    - model file: modeling/technical_agent/technical_agent_model.pkl

Notes:
    - Excludes raw price columns (open/high/low/close/bid/ask/volume) to avoid leakage.
    - Uses chronological 80/20 split.
"""
import argparse
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, f1_score, classification_report


PRICE_COL_PATTERNS = ["open", "high", "low", "close", "bid", "ask", "price", "volume"]


def drop_price_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Drop columns whose name contains any price-related token (case-insensitive)
    cols_to_drop = [c for c in df.columns if any(p in c.lower() for p in PRICE_COL_PATTERNS)]
    return df.drop(columns=[c for c in cols_to_drop if c in df.columns], errors="ignore")


def create_target(df: pd.DataFrame, price_col: str = "close") -> pd.Series:
    # Expect a numeric price column name; default 'close'. If missing, try to infer.
    if price_col not in df.columns:
        # try common names
        for cand in ["Close", "close", "close_price"]:
            if cand in df.columns:
                price_col = cand
                break
    if price_col not in df.columns:
        raise ValueError("No close price column found to create target. Provide a CSV with a close price column.")

    # Compute forward return (next_close - current_close)
    future_close = df[price_col].shift(-1)
    ret = future_close - df[price_col]

    # Thresholds provided in task: > 0.0002 => 1, < -0.0002 => -1, else 0
    target = pd.Series(0, index=df.index)
    target[ret > 0.0002] = 1
    target[ret < -0.0002] = -1
    return target


def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=True)
    return df


def chronological_split(X: pd.DataFrame, y: pd.Series, train_frac: float = 0.8):
    n = len(X)
    split = int(n * train_frac)
    X_train = X.iloc[:split].reset_index(drop=True)
    X_test = X.iloc[split:].reset_index(drop=True)
    y_train = y.iloc[:split].reset_index(drop=True)
    y_test = y.iloc[split:].reset_index(drop=True)
    return X_train, X_test, y_train, y_test


def main():
    script_dir = Path(__file__).resolve().parent
    pairs = ["EURUSD", "USDJPY", "GBPUSD", "USDCHF"]
    
    for symbol in pairs:
        print(f"\n{'='*50}\nTraining Technical Agent for {symbol}\n{'='*50}")
        input_file = f"../../data_understanding_outputs/features/features_{symbol}_1H.csv"
        input_path = (script_dir / input_file).resolve()
        
        if not input_path.exists():
            print(f"File not found: {input_path} - Skipping {symbol}")
            continue
            
        print(f"Loading data from {input_path}")
        df = load_data(input_path)
        
        close_candidates = [c for c in df.columns if c.lower() == "close" or c.lower().endswith("_close") or c.lower().endswith("close_price")]
        close_col = close_candidates[0] if close_candidates else "close"
        if close_col not in df.columns:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if len(numeric_cols) == 0:
                print(f"No numeric columns for {symbol}, skipping.")
                continue
            close_col = numeric_cols[0]

        print(f"Using '{close_col}' as price column to build target.")
        target = create_target(df, price_col=close_col)

        valid_idx = target.dropna().index
        df = df.loc[valid_idx].reset_index(drop=True)
        target = target.loc[valid_idx].reset_index(drop=True)

        X = df.select_dtypes(include=[np.number]).copy()
        X = drop_price_columns(X)

        if X.shape[1] == 0:
            print(f"No numeric features for {symbol}, skipping.")
            continue

        X_train, X_test, y_train, y_test = chronological_split(X, target, train_frac=0.8)

        pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("rf", RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1))
        ])

        print(f"Training RandomForestClassifier ({symbol} 100 trees)...")
        pipeline.fit(X_train, y_train)

        y_pred = pipeline.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average="macro")
        print("Evaluation on test set:")
        print(f"  Accuracy: {acc:.4f}")
        print(f"  F1 (macro): {f1:.4f}")

        out_path = script_dir / f"technical_agent_{symbol}.pkl"
        joblib.dump(pipeline, out_path)
        print(f"✅ Saved trained distinct model to {out_path}")

if __name__ == "__main__":
    main()
