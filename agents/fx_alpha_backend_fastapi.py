from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from influxdb_client import InfluxDBClient
from dotenv import load_dotenv
import os
from typing import Any, Dict, List

load_dotenv()

app = FastAPI(title="Forex Alpha API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Environment config
# -----------------------------
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "forex_metadata")
POSTGRES_USER = os.getenv("POSTGRES_USER", "forex_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "forex_pass_2026")

INFLUXDB_URL = os.getenv("INFLUXDB_URL")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET")

DATABASE_URL = (
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

engine = create_engine(DATABASE_URL, future=True)
influx_client = InfluxDBClient(
    url=INFLUXDB_URL,
    token=INFLUXDB_TOKEN,
    org=INFLUXDB_ORG,
)
query_api = influx_client.query_api()


# -----------------------------
# Helpers
# -----------------------------
def safe_float(value: Any):
    try:
        return float(value)
    except Exception:
        return None


def fetch_prices(symbol: str = "EURUSD", tf: str = "1H", limit: int = 100) -> List[Dict[str, Any]]:
    flux = f'''
from(bucket: "{INFLUXDB_BUCKET}")
  |> range(start: -30d)
  |> filter(fn: (r) => r["_measurement"] == "forex_prices")
  |> filter(fn: (r) => r["symbol"] == "{symbol}")
  |> filter(fn: (r) => r["timeframe"] == "{tf}")
  |> filter(fn: (r) => r["_field"] == "open" or r["_field"] == "high" or r["_field"] == "low" or r["_field"] == "close" or r["_field"] == "volume")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> sort(columns:["_time"])
  |> tail(n:{limit})
'''
    df = query_api.query_data_frame(flux)

    if isinstance(df, list):
        import pandas as pd
        df = pd.concat(df, ignore_index=True) if df else pd.DataFrame()

    if getattr(df, "empty", True):
        return []

    keep = [c for c in ["_time", "open", "high", "low", "close", "volume"] if c in df.columns]
    df = df[keep].copy()
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "time": r["_time"].isoformat() if hasattr(r["_time"], "isoformat") else str(r["_time"]),
            "open": safe_float(r.get("open")),
            "high": safe_float(r.get("high")),
            "low": safe_float(r.get("low")),
            "close": safe_float(r.get("close")),
            "volume": int(r.get("volume")) if r.get("volume") is not None else None,
        })
    return rows


# -----------------------------
# API endpoints used by the HTML page
# -----------------------------
@app.get("/api/overview")
def overview():
    return {
        "market_source": "MT5 via InfluxDB",
        "macro_source": "PostgreSQL",
        "news_source": "PostgreSQL",
        "events_source": "PostgreSQL",
        "system_status": "online",
        "last_update": __import__("datetime").datetime.utcnow().isoformat() + "Z",
    }


@app.get("/api/prices")
def prices(symbol: str = Query("EURUSD"), tf: str = Query("1H"), limit: int = Query(100)):
    return fetch_prices(symbol=symbol, tf=tf, limit=limit)


@app.get("/api/macro")
def macro(limit: int = Query(100)):
    sql = text("""
        SELECT date, COALESCE(country, '') AS country, series_id, indicator_name, value, COALESCE(source, 'FRED') AS source
        FROM economic_indicators
        ORDER BY date DESC
        LIMIT :limit
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, {"limit": limit}).mappings().all()
    return [dict(r) for r in rows]


@app.get("/api/news")
def news(limit: int = Query(50)):
    sql = text("""
        SELECT published_at, source, title,
               COALESCE(sentiment_score, 0) AS sentiment_score,
               COALESCE(currency_tag, '') AS currency_tag,
               COALESCE(currencies::text, '') AS currencies,
               url
        FROM news_articles
        ORDER BY published_at DESC
        LIMIT :limit
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, {"limit": limit}).mappings().all()
    out = []
    for r in rows:
        d = dict(r)
        if d.get("currency_tag") == "" and d.get("currencies"):
            d["currency_tag"] = d["currencies"]
        out.append(d)
    return out


@app.get("/api/events")
def events(limit: int = Query(50)):
    sql = text("""
        SELECT event_date, currency,
               COALESCE(importance, impact, '') AS impact,
               event_name,
               forecast AS expected,
               actual,
               previous
        FROM economic_events
        ORDER BY event_date DESC
        LIMIT :limit
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, {"limit": limit}).mappings().all()
    return [dict(r) for r in rows]


@app.get("/api/signal/latest")
def signal_latest(symbol: str = Query("EURUSD"), tf: str = Query("1H")):
    prices = fetch_prices(symbol=symbol, tf=tf, limit=30)
    if len(prices) < 2:
        return {
            "signal": "HOLD",
            "confidence": 0.5,
            "reasons": ["Pas assez de données prix pour calculer une synthèse simple."]
        }

    closes = [p["close"] for p in prices if p.get("close") is not None]
    latest = closes[-1]
    prev = closes[-2]
    sma_5 = sum(closes[-5:]) / min(5, len(closes))
    sma_20 = sum(closes[-20:]) / min(20, len(closes))

    if latest > sma_5 > sma_20 and latest > prev:
        signal = "BUY"
        confidence = 0.72
        reasons = [
            f"Le dernier close ({latest:.4f}) est au-dessus de la moyenne courte et de la moyenne longue.",
            "Le mouvement récent reste haussier sur les dernières bougies.",
            "Signal calculé automatiquement à partir des données réelles InfluxDB."
        ]
    elif latest < sma_5 < sma_20 and latest < prev:
        signal = "SELL"
        confidence = 0.72
        reasons = [
            f"Le dernier close ({latest:.4f}) est en dessous de la moyenne courte et de la moyenne longue.",
            "Le mouvement récent reste baissier sur les dernières bougies.",
            "Signal calculé automatiquement à partir des données réelles InfluxDB."
        ]
    else:
        signal = "HOLD"
        confidence = 0.55
        reasons = [
            "Le marché est mitigé ou sans alignement clair entre tendance courte et longue.",
            "Aucune direction forte n'est détectée sur les dernières bougies.",
            "Le système préfère rester neutre dans ce cas."
        ]

    return {
        "signal": signal,
        "confidence": confidence,
        "reasons": reasons,
    }


@app.get("/")
def root():
    return {"message": "Forex Alpha API is running."}

# Run with:
# uvicorn fx_alpha_backend_fastapi:app --reload --host 0.0.0.0 --port 8000
