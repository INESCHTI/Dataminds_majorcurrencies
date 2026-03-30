"""
Shared data loading and feature engineering for the Macro Agent.

- Load long-format rows from PostgreSQL `economic_indicators`
- Pivot to wide format (date x series_id)
- Apply chronological feature engineering (ffill, lags, optional rolls)
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
import psycopg2

# Project root: modeling/macro_agent -> modeling -> forex-alpha-data
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_env():
    try:
        from dotenv import load_dotenv

        load_dotenv(PROJECT_ROOT / "config" / ".env", override=True)
    except ImportError:
        pass


def get_postgres_conn_kwargs() -> Dict:
    _load_env()
    return {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
        "dbname": os.getenv("POSTGRES_DB", ""),
        "user": os.getenv("POSTGRES_USER", ""),
        "password": os.getenv("POSTGRES_PASSWORD", ""),
    }


def load_economic_indicators_long(conn=None) -> pd.DataFrame:
    """Load all rows from economic_indicators (long format)."""
    close_own = False
    if conn is None:
        conn = psycopg2.connect(**get_postgres_conn_kwargs())
        close_own = True
    try:
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT date, series_id, indicator_name, value
                FROM economic_indicators
                ORDER BY date ASC, series_id ASC
                """
            )
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
            df = pd.DataFrame(rows, columns=cols)
        finally:
            cur.close()
    finally:
        if close_own:
            conn.close()

    if df.empty:
        raise ValueError("economic_indicators is empty. Run acquire_fred_data.py first.")

    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df


def pivot_indicators(df_long: pd.DataFrame) -> pd.DataFrame:
    """Wide format: index=date, columns=series_id, values=value."""
    piv = df_long.pivot(index="date", columns="series_id", values="value")
    piv = piv.sort_index()
    return piv


def add_lag_features(
    df: pd.DataFrame,
    lag_periods: Tuple[int, ...] = (1, 3, 7),
) -> pd.DataFrame:
    """Add lag_N for each existing numeric column (after copy)."""
    out = df.copy()
    numeric_cols = [c for c in out.columns if pd.api.types.is_numeric_dtype(out[c])]
    for col in numeric_cols:
        for lag in lag_periods:
            out[f"{col}_lag_{lag}"] = out[col].shift(lag)
    return out


def add_rolling_means(df: pd.DataFrame, windows: Tuple[int, ...] = (7,)) -> pd.DataFrame:
    """Optional rolling mean on level columns (exclude already-lagged names)."""
    out = df.copy()
    level_cols = [
        c
        for c in out.columns
        if "_lag_" not in c and pd.api.types.is_numeric_dtype(out[c])
    ]
    for col in level_cols:
        for w in windows:
            out[f"{col}_rollmean_{w}"] = out[col].rolling(window=w, min_periods=1).mean()
    return out


def engineer_macro_features(
    pivoted: pd.DataFrame,
    *,
    add_roll: bool = True,
    lag_periods: Tuple[int, ...] = (1, 3, 7),
) -> pd.DataFrame:
    """
    Chronological feature matrix from pivoted macro levels only (no target).

    - Forward-fill missing values along time (macro releases are irregular)
    - Add lag and optional rolling features
    """
    df = pivoted.sort_index().copy()
    df = df.ffill()

    df = add_lag_features(df, lag_periods=lag_periods)
    if add_roll:
        df = add_rolling_means(df, windows=(7,))

    return df


def create_target_direction(series: pd.Series, threshold: float = 0.0002) -> pd.Series:
    """
    Build next-period directional labels from a target FX series.

    Rule: next value minus current value with 3-way classing:
      +1 if delta > threshold, -1 if delta < -threshold, else 0.
    Last row has no future value and is dropped from training.
    """
    future = series.shift(-1)
    ret = future - series
    target = pd.Series(0, index=series.index, dtype=np.float64)
    target[ret > threshold] = 1
    target[ret < -threshold] = -1
    target[future.isna()] = np.nan
    return target


# EUR/USD FRED series used for labels
TARGET_SERIES_EURUSD = "DEXUSEU"


def build_training_frame(
    df_long: Optional[pd.DataFrame] = None,
    *,
    target_series: str = TARGET_SERIES_EURUSD,
    target_threshold: float = 0.0002,
    **feature_kwargs,
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Full pipeline from long SQL-style frame to (X, y) with aligned index.
    Rows with NaN target are dropped. Feature rows must have no excessive NaN
    after ffill (initial warm-up rows with only NaN lags dropped).
    """
    if df_long is None:
        df_long = load_economic_indicators_long()
    piv = pivot_indicators(df_long)

    if target_series not in piv.columns:
        raise ValueError(
            f"Target series {target_series!r} not in pivot columns {list(piv.columns)}. "
            "Ensure FRED acquisition includes this series."
        )

    y = create_target_direction(piv[target_series], threshold=target_threshold)
    X_wide = engineer_macro_features(piv, **feature_kwargs)

    aligned = X_wide.copy()
    aligned["_target"] = y
    aligned = aligned.dropna(subset=["_target"])
    y_clean = aligned["_target"].astype(np.int64)
    X = aligned.drop(columns=["_target"])

    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.dropna(axis=1, how="all")
    mask = X.notna().any(axis=1)
    X = X.loc[mask].reset_index(drop=True)
    y_clean = y_clean.loc[mask].reset_index(drop=True)

    return X, y_clean
