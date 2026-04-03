"""
=====================================
FEATURE ENGINEERING PIPELINE
FX-AlphaLab | Major Currencies
=====================================
Génère 3 familles de features :
  1. Features Techniques   (→ Technical Agent)
  2. Features Macro        (→ Macro Agent)
  3. Features Sentiment    (→ Sentiment Agent)

Sources :
  - InfluxDB  → Prix OHLC (MT5)
  - PostgreSQL → Macro (FRED) + News
"""

import os
import warnings
import numpy as np
import pandas as pd
import psycopg2
from influxdb_client import InfluxDBClient
from dotenv import load_dotenv
from datetime import datetime, timedelta

warnings.filterwarnings("ignore")
load_dotenv()

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────

PAIRS     = ["EURUSD", "USDJPY", "GBPUSD", "USDCHF"]
TIMEFRAME = "1H"   # timeframe principal

PG_DSN = (
    f"host={os.getenv('POSTGRES_HOST')} "
    f"port={os.getenv('POSTGRES_PORT')} "
    f"dbname={os.getenv('POSTGRES_DB')} "
    f"user={os.getenv('POSTGRES_USER')} "
    f"password={os.getenv('POSTGRES_PASSWORD')}"
)

INFLUX_CLIENT = InfluxDBClient(
    url=os.getenv("INFLUXDB_URL"),
    token=os.getenv("INFLUXDB_TOKEN"),
    org=os.getenv("INFLUXDB_ORG")
)

# ─────────────────────────────────────────
# HELPERS — LOAD RAW DATA
# ─────────────────────────────────────────

def load_ohlc(symbol: str, timeframe: str = "1H", days: int = 365*3) -> pd.DataFrame:
    """Charge les prix OHLC depuis InfluxDB."""
    query = f'''
    from(bucket: "{os.getenv("INFLUXDB_BUCKET")}")
      |> range(start: -{days}d)
      |> filter(fn: (r) => r._measurement == "forex_prices")
      |> filter(fn: (r) => r.symbol == "{symbol}")
      |> filter(fn: (r) => r.timeframe == "{timeframe}")
      |> pivot(rowKey:["_time"], columnKey:["_field"], valueColumn:"_value")
      |> sort(columns: ["_time"])
    '''
    tables = INFLUX_CLIENT.query_api().query_data_frame(query)
    if tables.empty:
        return pd.DataFrame()

    df = tables[["_time","open","high","low","close","volume"]].copy()
    df.rename(columns={"_time": "time"}, inplace=True)
    df["time"] = pd.to_datetime(df["time"])
    df.set_index("time", inplace=True)
    df = df.astype(float)
    df.sort_index(inplace=True)
    return df


def load_macro(days: int = 365*3) -> pd.DataFrame:
    """Charge les indicateurs macro depuis PostgreSQL."""
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    conn  = psycopg2.connect(PG_DSN)
    df    = pd.read_sql(
        f"""
        SELECT date, series_id, value
        FROM economic_indicators
        WHERE date >= '{since}'
        ORDER BY date
        """,
        conn
    )
    conn.close()
    df["date"] = pd.to_datetime(df["date"])
    # Pivot : une colonne par indicateur
    df = df.pivot(index="date", columns="series_id", values="value")
    df.sort_index(inplace=True)
    return df


def load_news(days: int = 30) -> pd.DataFrame:
    """Charge les articles de news depuis PostgreSQL."""
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    conn  = psycopg2.connect(PG_DSN)
    df    = pd.read_sql(
        f"""
        SELECT published_at, title, content, currencies
        FROM news_articles
        WHERE published_at >= '{since}'
        ORDER BY published_at
        """,
        conn
    )
    conn.close()
    df["published_at"] = pd.to_datetime(df["published_at"])
    return df


# ─────────────────────────────────────────
# FAMILLE 1 — FEATURES TECHNIQUES
# ─────────────────────────────────────────

def add_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Log-returns sur différentes fenêtres."""
    df["return_1h"]  = np.log(df["close"] / df["close"].shift(1))
    df["return_4h"]  = np.log(df["close"] / df["close"].shift(4))
    df["return_1d"]  = np.log(df["close"] / df["close"].shift(24))
    df["return_1w"]  = np.log(df["close"] / df["close"].shift(168))
    return df


def add_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """SMA et EMA."""
    for w in [10, 20, 50]:
        df[f"sma_{w}"]  = df["close"].rolling(w).mean()
        df[f"ema_{w}"]  = df["close"].ewm(span=w, adjust=False).mean()

    # Croisements
    df["sma_cross_10_20"] = (df["sma_10"] > df["sma_20"]).astype(int)
    df["sma_cross_20_50"] = (df["sma_20"] > df["sma_50"]).astype(int)
    df["price_vs_sma50"]  = (df["close"] - df["sma_50"]) / df["sma_50"]
    return df


def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """RSI — Relative Strength Index."""
    delta = df["close"].diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / (loss + 1e-10)
    df["rsi"] = 100 - (100 / (1 + rs))
    # Zones RSI
    df["rsi_oversold"]   = (df["rsi"] < 30).astype(int)
    df["rsi_overbought"] = (df["rsi"] > 70).astype(int)
    return df


def add_macd(df: pd.DataFrame) -> pd.DataFrame:
    """MACD (12, 26, 9)."""
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"]        = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"]   = df["macd"] - df["macd_signal"]
    # Croisement MACD
    df["macd_cross"]  = (
        (df["macd"] > df["macd_signal"]) &
        (df["macd"].shift(1) <= df["macd_signal"].shift(1))
    ).astype(int)
    return df


def add_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """ATR — Average True Range (volatilité)."""
    hl   = df["high"] - df["low"]
    hc   = (df["high"] - df["close"].shift(1)).abs()
    lc   = (df["low"]  - df["close"].shift(1)).abs()
    tr   = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    df["atr"]            = tr.rolling(period).mean()
    df["atr_normalized"] = df["atr"] / df["close"]   # normalisé par le prix
    return df


def add_bollinger_bands(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    """Bollinger Bands."""
    mid           = df["close"].rolling(period).mean()
    std           = df["close"].rolling(period).std()
    df["bb_upper"] = mid + 2 * std
    df["bb_lower"] = mid - 2 * std
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / mid
    # Position dans les bandes : 0 = lower, 1 = upper
    df["bb_pct"]   = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"] + 1e-10)
    df["bb_squeeze"] = (df["bb_width"] < df["bb_width"].rolling(50).mean()).astype(int)
    return df


def add_volatility(df: pd.DataFrame) -> pd.DataFrame:
    """Volatilité rolling."""
    df["volatility_14h"] = df["return_1h"].rolling(14).std()
    df["volatility_24h"] = df["return_1h"].rolling(24).std()
    df["volatility_1w"]  = df["return_1h"].rolling(168).std()
    # Volatility regime : haute ou basse
    df["high_vol_regime"] = (
        df["volatility_24h"] > df["volatility_24h"].rolling(168).mean()
    ).astype(int)
    return df


def add_volume_features(df: pd.DataFrame) -> pd.DataFrame:
    """Features sur le volume."""
    df["volume_sma20"]    = df["volume"].rolling(20).mean()
    df["volume_ratio"]    = df["volume"] / (df["volume_sma20"] + 1e-10)
    df["volume_spike"]    = (df["volume_ratio"] > 2.0).astype(int)
    df["volume_change"]   = df["volume"].pct_change()
    return df


def add_candlestick_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """Patterns de bougies japonaises simples."""
    body      = (df["close"] - df["open"]).abs()
    candle_rng = df["high"] - df["low"]

    # Doji : body très petit par rapport au range
    df["doji"]     = (body < 0.1 * candle_rng).astype(int)
    # Marubozu : body = presque tout le range
    df["marubozu"] = (body > 0.9 * candle_rng).astype(int)
    # Bullish / Bearish engulfing (simplifié)
    df["bullish_candle"] = (df["close"] > df["open"]).astype(int)
    df["bearish_candle"] = (df["close"] < df["open"]).astype(int)
    return df


def build_technical_features(symbol: str, timeframe: str = "1H") -> pd.DataFrame:
    """Pipeline complète des features techniques."""
    print(f"\n[TECHNICAL] Building features for {symbol} {timeframe}...")
    df = load_ohlc(symbol, timeframe)
    if df.empty:
        print(f"   [WARN] No data for {symbol}")
        return pd.DataFrame()

    df = add_returns(df)
    df = add_moving_averages(df)
    df = add_rsi(df)
    df = add_macd(df)
    df = add_atr(df)
    df = add_bollinger_bands(df)
    df = add_volatility(df)
    df = add_volume_features(df)
    df = add_candlestick_patterns(df)

    # TARGET : direction du prix dans 4H
    df["target"] = (df["close"].shift(-4) > df["close"]).astype(int)

    df["symbol"] = symbol
    print(f"   [OK] {len(df)} rows | {df.shape[1]} features")
    return df


# ─────────────────────────────────────────
# FAMILLE 2 — FEATURES MACRO
# ─────────────────────────────────────────

def build_macro_features(df_price: pd.DataFrame) -> pd.DataFrame:
    """
    Aligne les indicateurs macro sur le timeframe du prix.
    Forward-fill car les données macro sont basse fréquence (mensuel/hebdo).
    """
    print("\n[MACRO] Building macro features...")
    macro = load_macro()
    if macro.empty:
        print("   [WARN] No macro data")
        return df_price

    # Harmonisation timezone avant reindex
    macro.index = pd.to_datetime(macro.index).tz_localize(None)
    price_index  = df_price.index.tz_localize(None) if df_price.index.tzinfo else df_price.index

    # Reindex sur l'index du prix (forward fill)
    macro_aligned = macro.reindex(price_index, method="ffill")
    macro_aligned.index = df_price.index  # restaure l'index original

    # Features dérivées
    if "CPIAUCSL" in macro_aligned.columns:
        macro_aligned["cpi_delta"]    = macro_aligned["CPIAUCSL"].pct_change()
        macro_aligned["cpi_yoy"]      = macro_aligned["CPIAUCSL"].pct_change(12)

    if "FEDFUNDS" in macro_aligned.columns and "CPIAUCSL" in macro_aligned.columns:
        macro_aligned["real_rate"]    = (
            macro_aligned["FEDFUNDS"] - macro_aligned["CPIAUCSL"].pct_change(12) * 100
        )

    if "UNRATE" in macro_aligned.columns:
        macro_aligned["unemployment_delta"] = macro_aligned["UNRATE"].diff()

    if "DGS10" in macro_aligned.columns:
        macro_aligned["yield_10y_delta"] = macro_aligned["DGS10"].diff()

    if "T10YIE" in macro_aligned.columns and "DGS10" in macro_aligned.columns:
        macro_aligned["real_yield_10y"] = (
            macro_aligned["DGS10"] - macro_aligned["T10YIE"]
        )

    # Renommage pour clarté
    rename_map = {
        "CPIAUCSL": "cpi",
        "FEDFUNDS": "fed_funds_rate",
        "UNRATE":   "unemployment",
        "DGS10":    "yield_10y",
        "T10YIE":   "inflation_expectations",
        "GDP":      "gdp",
    }
    macro_aligned.rename(columns=rename_map, inplace=True)

    # Merge avec le prix
    df_merged = df_price.join(macro_aligned, how="left")
    print(f"   [OK] Added {macro_aligned.shape[1]} macro features")
    return df_merged


# ─────────────────────────────────────────
# FAMILLE 3 — FEATURES SENTIMENT
# ─────────────────────────────────────────

def simple_sentiment_score(text: str) -> float:
    """
    Score de sentiment basique par dictionnaire.
    Remplacé par FinBERT dans l'Agent Sentiment (Phase 3).
    """
    bullish_words = [
        "rise","rally","gain","bullish","surge","strong","positive",
        "growth","recovery","boost","up","higher","beat","exceed"
    ]
    bearish_words = [
        "fall","drop","decline","bearish","weak","negative","loss",
        "recession","crash","down","lower","miss","disappoint","fear"
    ]
    text = text.lower()
    bull = sum(1 for w in bullish_words if w in text)
    bear = sum(1 for w in bearish_words if w in text)
    total = bull + bear
    if total == 0:
        return 0.0
    return (bull - bear) / total


def build_sentiment_features(df_price: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Calcule les features de sentiment et les aligne sur le prix.
    Le symbole sert à filtrer les news pertinentes (ex: EUR pour EURUSD).
    """
    print(f"\n[SENTIMENT] Building sentiment features for {symbol}...")
    news = load_news(days=90)
    if news.empty:
        print("   [WARN] No news data")
        return df_price

    # Filtre par devise pertinente
    currencies_for_symbol = {
        "EURUSD": ["EUR", "USD"],
        "USDJPY": ["USD", "JPY"],
        "GBPUSD": ["GBP", "USD"],
        "USDCHF": ["USD", "CHF"],
    }
    relevant_currencies = currencies_for_symbol.get(symbol, [])

    def is_relevant(currencies_list):
        if not currencies_list:
            return False
        return any(c in currencies_list for c in relevant_currencies)

    news["is_relevant"] = news["currencies"].apply(is_relevant)
    news = news[news["is_relevant"]].copy()

    if news.empty:
        print(f"   [WARN] No relevant news for {symbol}")
        return df_price

    # Score de sentiment par article
    news["sentiment"] = (news["title"] + " " + news["content"].fillna("")).apply(
        simple_sentiment_score
    )
    news.set_index("published_at", inplace=True)
    news.sort_index(inplace=True)

    # Resampler par heure
    sent_hourly = news["sentiment"].resample("1h").mean().fillna(0)

    # Features rolling
    sent_df = pd.DataFrame(index=sent_hourly.index)
    sent_df["sentiment_raw"]        = sent_hourly
    sent_df["sentiment_roll_3h"]    = sent_hourly.rolling(3,  min_periods=1).mean()
    sent_df["sentiment_roll_24h"]   = sent_hourly.rolling(24, min_periods=1).mean()
    sent_df["sentiment_roll_72h"]   = sent_hourly.rolling(72, min_periods=1).mean()
    sent_df["news_volume_1h"]       = news["sentiment"].resample("1h").count().reindex(sent_df.index, fill_value=0)
    sent_df["news_volume_24h"]      = sent_df["news_volume_1h"].rolling(24).sum()
    sent_df["bullish_ratio_24h"]    = (
        news["sentiment"].clip(lower=0).resample("1h").sum()
        .rolling(24).sum()
        .reindex(sent_df.index, fill_value=0)
    )
    sent_df["sentiment_momentum"]   = sent_df["sentiment_roll_3h"] - sent_df["sentiment_roll_24h"]
    sent_df["high_impact_news"]     = (sent_df["news_volume_1h"] > sent_df["news_volume_1h"].quantile(0.90)).astype(int)

    # Aligner sur l'index du prix
    sent_aligned = sent_df.reindex(df_price.index, method="ffill").fillna(0)
    df_merged    = df_price.join(sent_aligned, how="left")

    print(f"   [OK] Added {sent_df.shape[1]} sentiment features")
    return df_merged


# ─────────────────────────────────────────
# PIPELINE PRINCIPALE
# ─────────────────────────────────────────

def build_full_feature_matrix(symbol: str, timeframe: str = "1H") -> pd.DataFrame:
    """
    Construit la matrice complète de features pour un symbole.
    Combine : Technique + Macro + Sentiment
    """
    print(f"\n{'='*55}")
    print(f"  FEATURE ENGINEERING - {symbol} {timeframe}")
    print(f"{'='*55}")

    # 1. Features techniques (base)
    df = build_technical_features(symbol, timeframe)
    if df.empty:
        return pd.DataFrame()

    # 2. Features macro (alignées sur le prix)
    df = build_macro_features(df)

    # 3. Features sentiment (alignées sur le prix)
    df = build_sentiment_features(df, symbol)

    # 4. Nettoyage final
    df.dropna(subset=["target"], inplace=True)  # supprimer lignes sans target
    df.dropna(thresh=int(0.7 * len(df.columns)), inplace=True)  # garder lignes avec ≥ 70% de features

    # Forward fill puis fill 0 pour le reste
    df.ffill(inplace=True)
    df.fillna(0, inplace=True)

    print(f"\n[OK] Feature matrix built:")
    print(f"   Rows    : {len(df):,}")
    print(f"   Features: {df.shape[1] - 2}")  # -2 : symbol + target
    print(f"   Period  : {df.index.min()} -> {df.index.max()}")
    print(f"   Target  : BUY={df['target'].sum():,} | SELL={(df['target']==0).sum():,}")

    return df


def build_all_pairs(timeframe: str = "1H") -> dict:
    """Construit les features pour toutes les paires."""
    all_features = {}
    for symbol in PAIRS:
        df = build_full_feature_matrix(symbol, timeframe)
        if not df.empty:
            all_features[symbol] = df
            # Sauvegarde CSV
            path = f"features/{symbol}_{timeframe}_features.csv"
            os.makedirs("features", exist_ok=True)
            df.to_csv(path)
            print(f"   Saved to {path}")
    return all_features


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  FEATURE ENGINEERING PIPELINE")
    print("  FX-AlphaLab | Major Currencies")
    print("=" * 55)

    features = build_all_pairs(timeframe="1H")

    print(f"\n{'='*55}")
    print(f"  SUMMARY")
    print(f"{'='*55}")
    for symbol, df in features.items():
        print(f"  {symbol}: {len(df):,} rows x {df.shape[1]} features")

    INFLUX_CLIENT.close()
    print("\n[OK] Feature Engineering Complete!")