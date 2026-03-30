"""
Shared data loading and feature engineering for the Sentiment Agent.

Data source:
- PostgreSQL news data produced by data_understanding/acquire_news_data.py
- Price feature CSVs from data_understanding_outputs/features

This module builds symbol/timeframe sentiment features and training targets.
"""
from __future__ import annotations

import ast
import os
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd
import psycopg2

try:
    from .nlp_utils import embedding_similarity, get_nlp_signal, map_entities_to_assets
except ImportError:
    from nlp_utils import embedding_similarity, get_nlp_signal, map_entities_to_assets

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FEATURES_DIR = PROJECT_ROOT / "data_understanding_outputs" / "features"

SYMBOLS = ["EURUSD", "USDJPY", "GBPUSD", "USDCHF"]
TIMEFRAME_RULES = {"1H": "1h", "4H": "4h", "1D": "1d"}

POSITIVE_WORDS = {
    "rise", "rises", "rally", "gain", "gains", "strong", "strength", "surge", "bullish",
    "hawkish", "upside", "beat", "beats", "expands", "growth", "optimistic", "rebound",
}
NEGATIVE_WORDS = {
    "fall", "falls", "drop", "drops", "decline", "declines", "weak", "weakness", "bearish",
    "dovish", "downside", "miss", "misses", "contracts", "recession", "risk-off", "selloff",
}

PAIR_TO_CURRENCIES = {
    "EURUSD": {"EUR", "USD"},
    "USDJPY": {"USD", "JPY"},
    "GBPUSD": {"GBP", "USD"},
    "USDCHF": {"USD", "CHF"},
}

NLP_CACHE_MAX = 5000
_NLP_ROW_CACHE: Dict[str, Dict] = {}


def _load_env() -> None:
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


def _normalize_currency_array(raw_value) -> List[str]:
    if raw_value is None:
        return []

    if isinstance(raw_value, (list, tuple)):
        vals = [str(v).upper()[:3] for v in raw_value if v]
        return [v for v in vals if len(v) == 3]

    if isinstance(raw_value, str):
        txt = raw_value.strip()
        if not txt:
            return []
        if txt.startswith("{") and txt.endswith("}"):
            inside = txt[1:-1].strip()
            if not inside:
                return []
            vals = [v.strip().strip('"').upper()[:3] for v in inside.split(",")]
            return [v for v in vals if len(v) == 3]

        try:
            parsed = ast.literal_eval(txt)
            if isinstance(parsed, (list, tuple)):
                vals = [str(v).upper()[:3] for v in parsed if v]
                return [v for v in vals if len(v) == 3]
        except Exception:
            pass

    return []


def _extract_currencies_from_text(text: str) -> List[str]:
    upper = (text or "").upper()
    found = []
    for cc in ["EUR", "USD", "JPY", "GBP", "CHF"]:
        if re.search(rf"\b{cc}\b", upper):
            found.append(cc)
    return found


def _score_text_sentiment(text: str) -> float:
    tokens = re.findall(r"[a-zA-Z\-']+", (text or "").lower())
    if not tokens:
        return 0.0

    pos = sum(1 for t in tokens if t in POSITIVE_WORDS)
    neg = sum(1 for t in tokens if t in NEGATIVE_WORDS)

    if pos == 0 and neg == 0:
        return 0.0

    score = (pos - neg) / max(1, pos + neg)
    return float(np.clip(score, -1.0, 1.0))


def _cached_nlp_for_text(text: str) -> Dict:
    key = str(hash((text or "").strip().lower()))
    payload = _NLP_ROW_CACHE.get(key)
    if payload is not None:
        return payload

    payload = get_nlp_signal(text)
    if len(_NLP_ROW_CACHE) >= NLP_CACHE_MAX:
        _NLP_ROW_CACHE.pop(next(iter(_NLP_ROW_CACHE)))
    _NLP_ROW_CACHE[key] = payload
    return payload


def load_news_rows(conn=None) -> pd.DataFrame:
    """Load and normalize rows from available news tables."""
    close_own = False
    empty_df = pd.DataFrame(columns=["published_at", "title", "body", "source", "currencies", "url"])
    if conn is None:
        try:
            conn = psycopg2.connect(**get_postgres_conn_kwargs())
            close_own = True
        except Exception:
            return empty_df

    frames: List[pd.DataFrame] = []
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name IN ('news_articles', 'forex_news')
            """
        )
        tables = {r[0] for r in cur.fetchall()}

        if "news_articles" in tables:
            cur.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'news_articles'
                """
            )
            news_articles_cols = {r[0] for r in cur.fetchall()}
            source_col = "source_name" if "source_name" in news_articles_cols else "source"
            cur.execute(
                f"""
                SELECT published_at, title, content, {source_col}, currencies, url
                FROM news_articles
                WHERE published_at IS NOT NULL
                ORDER BY published_at ASC
                """
            )
            rows = cur.fetchall()
            if rows:
                df = pd.DataFrame(rows, columns=["published_at", "title", "body", "source", "currencies", "url"])
                frames.append(df)

        if "forex_news" in tables:
            cur.execute(
                """
                SELECT published_at, title, description, source, url
                FROM forex_news
                WHERE published_at IS NOT NULL
                ORDER BY published_at ASC
                """
            )
            rows = cur.fetchall()
            if rows:
                df = pd.DataFrame(rows, columns=["published_at", "title", "body", "source", "url"])
                df["currencies"] = None
                frames.append(df)
    finally:
        cur.close()
        if close_own:
            conn.close()

    if not frames:
        return empty_df

    out = pd.concat(frames, ignore_index=True)
    out["published_at"] = pd.to_datetime(out["published_at"], utc=True, errors="coerce")
    out = out.dropna(subset=["published_at"]).copy()
    out["title"] = out["title"].fillna("").astype(str)
    out["body"] = out["body"].fillna("").astype(str)
    out["text"] = (out["title"].str.strip() + " " + out["body"].str.strip()).str.strip()
    out["currencies"] = out["currencies"].apply(_normalize_currency_array)

    # De-duplicate with URL when available, otherwise by (time, title)
    with_url = out[out["url"].notna() & (out["url"].astype(str).str.len() > 0)]
    no_url = out[~out.index.isin(with_url.index)]
    with_url = with_url.drop_duplicates(subset=["url"], keep="last")
    no_url = no_url.drop_duplicates(subset=["published_at", "title"], keep="last")
    out = pd.concat([with_url, no_url], ignore_index=True).sort_values("published_at")

    out["rule_sentiment_score"] = out["text"].apply(_score_text_sentiment)
    out["word_count"] = out["text"].str.split().str.len().fillna(0).astype(int)
    out["impact_weight"] = np.log1p(out["word_count"].clip(lower=0))

    # Fill currencies from text if missing in DB row.
    mask_empty = out["currencies"].apply(len) == 0
    out.loc[mask_empty, "currencies"] = out.loc[mask_empty, "text"].apply(_extract_currencies_from_text)

    nlp_payloads = out["text"].apply(_cached_nlp_for_text)
    out["sentiment_positive"] = nlp_payloads.apply(lambda d: float(d.get("sentiment_positive", 0.0)))
    out["sentiment_negative"] = nlp_payloads.apply(lambda d: float(d.get("sentiment_negative", 0.0)))
    out["sentiment_neutral"] = nlp_payloads.apply(lambda d: float(d.get("sentiment_neutral", 1.0)))
    out["sentiment_score"] = nlp_payloads.apply(lambda d: float(d.get("sentiment_score", 0.0)))
    out["entities"] = nlp_payloads.apply(lambda d: d.get("entities", {}))
    out["assets"] = nlp_payloads.apply(lambda d: d.get("assets", []))
    out["embedding"] = nlp_payloads.apply(lambda d: d.get("embedding", np.zeros(384, dtype=np.float32)))

    novelty = []
    duplicate = []
    prev_emb = None
    for emb in out["embedding"].tolist():
        sim = embedding_similarity(prev_emb, emb) if prev_emb is not None else 0.0
        novelty.append(float(max(0.0, 1.0 - sim)))
        duplicate.append(float(sim >= 0.92))
        prev_emb = emb
    out["narrative_novelty"] = novelty
    out["duplicate_flag"] = duplicate

    return out.reset_index(drop=True)


def _symbols_for_row(currencies: Iterable[str], text: str) -> List[str]:
    cset = {str(c).upper() for c in (currencies or [])}
    upper = (text or "").upper()
    out: List[str] = []

    for symbol, pair_ccy in PAIR_TO_CURRENCIES.items():
        token = symbol
        token_slash = f"{symbol[:3]}/{symbol[3:]}"
        ccy_overlap = len(pair_ccy.intersection(cset))
        has_fx_context = ("FOREX" in upper) or ("CURRENCY" in upper) or ("EXCHANGE RATE" in upper)
        if (
            pair_ccy.issubset(cset)
            or token in upper
            or token_slash in upper
            or (ccy_overlap >= 1 and has_fx_context)
        ):
            out.append(symbol)

    return out


def build_symbol_news_frame(news_df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    symbol = symbol.upper()
    if symbol not in SYMBOLS:
        raise ValueError(f"Unsupported symbol: {symbol}")

    if news_df.empty:
        return pd.DataFrame(
            columns=[
                "published_at",
                "sentiment_score",
                "impact_weight",
                "sentiment_positive",
                "sentiment_negative",
                "sentiment_neutral",
                "entity_relevance",
                "narrative_novelty",
                "duplicate_flag",
                "symbol",
            ]
        )

    temp = news_df.copy()
    temp["symbols"] = temp.apply(lambda r: _symbols_for_row(r["currencies"], r["text"]), axis=1)
    temp = temp[temp["symbols"].apply(lambda lst: symbol in lst)]
    if temp.empty:
        return pd.DataFrame(
            columns=[
                "published_at",
                "sentiment_score",
                "impact_weight",
                "sentiment_positive",
                "sentiment_negative",
                "sentiment_neutral",
                "entity_relevance",
                "narrative_novelty",
                "duplicate_flag",
                "symbol",
            ]
        )

    def _entity_relevance(row) -> float:
        entities = row.get("entities", {}) or {}
        assets = row.get("assets", []) or map_entities_to_assets(entities)
        direct = 1.0 if symbol in assets else 0.0
        pair_ccy = PAIR_TO_CURRENCIES.get(symbol, set())
        ccy_boost = sum(0.25 for cc in entities.get("currencies", []) if cc in pair_ccy)
        return float(min(1.5, direct + ccy_boost))

    temp = temp[
        [
            "published_at",
            "sentiment_score",
            "impact_weight",
            "sentiment_positive",
            "sentiment_negative",
            "sentiment_neutral",
            "narrative_novelty",
            "duplicate_flag",
            "entities",
            "assets",
            "symbols",
        ]
    ].copy()
    temp["entity_relevance"] = temp.apply(_entity_relevance, axis=1)
    temp["symbol"] = symbol
    return temp[
        [
            "published_at",
            "sentiment_score",
            "impact_weight",
            "sentiment_positive",
            "sentiment_negative",
            "sentiment_neutral",
            "entity_relevance",
            "narrative_novelty",
            "duplicate_flag",
            "symbol",
        ]
    ].reset_index(drop=True)


def aggregate_sentiment(news_symbol_df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    timeframe = timeframe.upper()
    rule = TIMEFRAME_RULES.get(timeframe)
    if rule is None:
        raise ValueError(f"Unsupported timeframe: {timeframe}")

    if news_symbol_df.empty:
        return pd.DataFrame(
            columns=[
                "sentiment_mean",
                "sentiment_weighted",
                "article_count",
                "entity_sentiment_weighted",
                "sentiment_skew",
                "positive_ratio",
                "negative_ratio",
                "sentiment_std",
                "sent_pos_mean",
                "sent_neg_mean",
                "sent_neu_mean",
                "narrative_novelty_mean",
                "duplicate_ratio",
            ]
        )

    df = news_symbol_df.copy()
    df = df.set_index(pd.to_datetime(df["published_at"], utc=True)).sort_index()

    grouped = pd.DataFrame(index=df.resample(rule).size().index)
    grouped["sentiment_mean"] = df["sentiment_score"].resample(rule).mean()
    grouped["article_count"] = df["sentiment_score"].resample(rule).size().astype(float)

    weighted_num = (df["sentiment_score"] * df["impact_weight"]).resample(rule).sum()
    weighted_den = df["impact_weight"].resample(rule).sum().replace(0, np.nan)
    grouped["sentiment_weighted"] = (weighted_num / weighted_den).fillna(0.0)

    entity_num = (df["sentiment_score"] * df["entity_relevance"]).resample(rule).sum()
    entity_den = df["entity_relevance"].resample(rule).sum().replace(0, np.nan)
    grouped["entity_sentiment_weighted"] = (entity_num / entity_den).fillna(0.0)

    grouped["positive_ratio"] = (df["sentiment_score"] > 0.05).resample(rule).mean().fillna(0.0)
    grouped["negative_ratio"] = (df["sentiment_score"] < -0.05).resample(rule).mean().fillna(0.0)
    grouped["sentiment_std"] = df["sentiment_score"].resample(rule).std().fillna(0.0)
    # Some pandas builds do not expose `.skew()` directly on resampler objects.
    grouped["sentiment_skew"] = (
        df["sentiment_score"].resample(rule).apply(lambda s: float(s.skew())).fillna(0.0)
    )
    grouped["sent_pos_mean"] = df["sentiment_positive"].resample(rule).mean().fillna(0.0)
    grouped["sent_neg_mean"] = df["sentiment_negative"].resample(rule).mean().fillna(0.0)
    grouped["sent_neu_mean"] = df["sentiment_neutral"].resample(rule).mean().fillna(0.0)
    grouped["narrative_novelty_mean"] = df["narrative_novelty"].resample(rule).mean().fillna(0.0)
    grouped["duplicate_ratio"] = df["duplicate_flag"].resample(rule).mean().fillna(0.0)

    grouped = grouped.fillna(0.0)
    grouped.index.name = "time"
    return grouped


def add_temporal_sentiment_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy().sort_index()
    base_cols = [
        "sentiment_mean",
        "sentiment_weighted",
        "article_count",
        "entity_sentiment_weighted",
        "sentiment_skew",
        "positive_ratio",
        "negative_ratio",
        "sentiment_std",
        "sent_pos_mean",
        "sent_neg_mean",
        "sent_neu_mean",
        "narrative_novelty_mean",
        "duplicate_ratio",
    ]
    for col in base_cols:
        if col not in out.columns:
            out[col] = 0.0

    for col in base_cols:
        out[f"{col}_lag_1"] = out[col].shift(1)
        out[f"{col}_lag_2"] = out[col].shift(2)
        out[f"{col}_roll3"] = out[col].rolling(window=3, min_periods=1).mean()

    out = out.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return out


def _load_price_series(symbol: str, timeframe: str) -> pd.Series:
    path = FEATURES_DIR / f"features_{symbol}_{timeframe.upper()}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Price feature file not found: {path}")

    raw = pd.read_csv(path)
    if raw.empty:
        raise ValueError(f"Price feature file is empty: {path}")

    dt_col = None
    for cand in ["time", "date", "datetime", "timestamp"]:
        if cand in raw.columns:
            dt_col = cand
            break

    if dt_col is not None:
        idx = pd.to_datetime(raw[dt_col], utc=True, errors="coerce")
    else:
        idx = pd.to_datetime(raw.iloc[:, 0], utc=True, errors="coerce")

    raw = raw.copy()
    raw.index = idx
    raw = raw[~raw.index.isna()].sort_index()

    close_col = None
    for c in raw.columns:
        cl = c.lower()
        if cl == "close" or cl.endswith("_close") or cl.endswith("close_price"):
            close_col = c
            break

    if close_col is None:
        numeric_cols = raw.select_dtypes(include=[np.number]).columns.tolist()
        if not numeric_cols:
            raise ValueError(f"No numeric columns in {path}")
        close_col = numeric_cols[0]

    out = pd.to_numeric(raw[close_col], errors="coerce").dropna()
    out.name = "close"
    return out


def create_direction_target(close_series: pd.Series, threshold: float = 0.0002) -> pd.Series:
    future = close_series.shift(-1)
    ret = future - close_series
    y = pd.Series(0, index=close_series.index, dtype=np.float64)
    y[ret > threshold] = 1
    y[ret < -threshold] = -1
    y[future.isna()] = np.nan
    return y


def build_training_frame(
    symbol: str,
    timeframe: str,
    *,
    target_threshold: float = 0.0002,
) -> Tuple[pd.DataFrame, pd.Series]:
    symbol = symbol.upper()
    timeframe = timeframe.upper()

    close = _load_price_series(symbol, timeframe)

    news = load_news_rows()
    news_symbol = build_symbol_news_frame(news, symbol)
    if news_symbol.empty:
        sentiment_tf = pd.DataFrame(
            index=close.index,
            data={
                "sentiment_mean": 0.0,
                "sentiment_weighted": 0.0,
                "article_count": 0.0,
                "entity_sentiment_weighted": 0.0,
                "sentiment_skew": 0.0,
                "positive_ratio": 0.0,
                "negative_ratio": 0.0,
                "sentiment_std": 0.0,
                "sent_pos_mean": 0.0,
                "sent_neg_mean": 0.0,
                "sent_neu_mean": 0.0,
                "narrative_novelty_mean": 0.0,
                "duplicate_ratio": 0.0,
            },
        )
    else:
        sentiment_tf = aggregate_sentiment(news_symbol, timeframe)
    sentiment_feat = add_temporal_sentiment_features(sentiment_tf)

    # Align sentiment buckets to price timestamps.
    X = sentiment_feat.reindex(close.index, method="ffill").fillna(0.0)
    y = create_direction_target(close, threshold=target_threshold)

    aligned = X.copy()
    aligned["_target"] = y
    aligned = aligned.dropna(subset=["_target"]).copy()
    if aligned.empty:
        raise ValueError(f"No aligned rows for sentiment training: {symbol} {timeframe}")

    y_clean = aligned["_target"].astype(np.int64)
    X_clean = aligned.drop(columns=["_target"])

    # Drop columns that are entirely missing after alignment.
    X_clean = X_clean.dropna(axis=1, how="all").fillna(0.0)
    if X_clean.shape[1] == 0:
        raise ValueError(f"No sentiment features available for training: {symbol} {timeframe}")

    return X_clean.reset_index(drop=True), y_clean.reset_index(drop=True)


def build_latest_feature_row(symbol: str, timeframe: str) -> pd.DataFrame:
    """Create one latest feature row from currently available news data."""
    symbol = symbol.upper()
    timeframe = timeframe.upper()

    news = load_news_rows()
    news_symbol = build_symbol_news_frame(news, symbol)
    if news_symbol.empty:
        raise ValueError(f"No symbol-specific news rows available for {symbol}")

    sentiment_tf = aggregate_sentiment(news_symbol, timeframe)
    sentiment_feat = add_temporal_sentiment_features(sentiment_tf)
    if sentiment_feat.empty:
        raise ValueError(f"No aggregated sentiment features for {symbol} {timeframe}")

    latest = sentiment_feat.iloc[[-1]].copy()
    return latest
