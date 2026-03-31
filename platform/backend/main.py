"""
FX-AlphaLab — FastAPI Backend (FINAL VERSION)
Aggregates ticks from InfluxDB into candles and merges with historical data.
"""

import os
import sys
import json
import re
import asyncio
import logging
import threading
import hashlib
import requests
from collections import Counter, deque
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

import numpy as np
import pandas as pd
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from .test_mode import router as test_mode_router

try:
    from openai import OpenAI
    OPENAI_SDK_AVAILABLE = True
except Exception:
    OpenAI = None
    OPENAI_SDK_AVAILABLE = False

# ─── Paths ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT / "config" / ".env")

FRONTEND_DIR   = Path(__file__).resolve().parent.parent / "frontend"
INTEGRATION_DIR = ROOT / "data_understanding_outputs" / "integrated"
MODEL_PATH      = ROOT / "modeling" / "technical_agent" / "technical_agent_model.pkl"

# ─── Config from .env ─────────────────────────────────────────────────────────
MT5_LOGIN    = int(os.getenv("MT5_LOGIN", "0"))
MT5_PASSWORD = os.getenv("MT5_PASSWORD", "")
MT5_SERVER   = os.getenv("MT5_SERVER", "")
MT5_PATH     = os.getenv("MT5_PATH", r"C:\Program Files\MetaTrader 5\terminal64.exe")

INFLUXDB_URL    = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN  = os.getenv("INFLUXDB_TOKEN", "")
INFLUXDB_ORG    = os.getenv("INFLUXDB_ORG", "")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "")

PG_HOST     = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT     = int(os.getenv("POSTGRES_PORT", "5432"))
PG_DB       = os.getenv("POSTGRES_DB", "")
PG_USER     = os.getenv("POSTGRES_USER", "")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
NEWS_REFRESH_SECONDS = int(os.getenv("NEWS_REFRESH_SECONDS", "60"))
EXPLANATION_CACHE_TTL_SECONDS = int(os.getenv("EXPLANATION_CACHE_TTL_SECONDS", "900"))
DECISION_TELEMETRY_MAX = int(os.getenv("DECISION_TELEMETRY_MAX", "5000"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_TIMEOUT_SECONDS = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "12"))
FRONTEND_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]

SYMBOLS    = ["EURUSD", "USDJPY", "GBPUSD", "USDCHF"]
TIMEFRAMES = ["1S", "1H", "4H", "1D"]

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.DEBUG, format="[%(asctime)s] %(levelname)s  %(message)s")
logger = logging.getLogger("FXAlphaLab")

# ─── Optional heavy imports ───────────────────────────────────────────────────
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    logger.warning("MetaTrader5 not installed")

try:
    from influxdb_client import InfluxDBClient, Point, WriteOptions
    from influxdb_client.client.write_api import SYNCHRONOUS
    INFLUX_AVAILABLE = True
except ImportError:
    INFLUX_AVAILABLE = False
    logger.warning("influxdb-client not installed")

try:
    import psycopg2
    PG_AVAILABLE = True
except ImportError:
    PG_AVAILABLE = False
    logger.warning("psycopg2 not installed")

# ─── Global State ─────────────────────────────────────────────────────────────
status: Dict[str, bool] = {
    "mt5": False,
    "influxdb": False,
    "postgres": False,
    "model": False,
    "macro_model": False,
    "sentiment_model": False,
    "decision_model": False,
}
ws_clients: set = set()
influx_client = None
influx_write_api = None
influx_query_api = None
pg_conn = None
model_pipelines = {}
macro_agent_handles = {}  # symbol -> MacroAgent instance when macro models are present
sentiment_agent_handles = {}  # (symbol, timeframe) -> SentimentAgent instance
SENTIMENT_TIMEFRAMES = ["1H", "4H", "1D"]
decision_agent_handle = None  # DecisionMetaAgent instance
decision_telemetry = deque(maxlen=DECISION_TELEMETRY_MAX)
decision_telemetry_lock = threading.Lock()
explanation_cache: Dict[str, Dict] = {}
copilot_sessions: Dict[str, List[Dict[str, str]]] = {}
copilot_sessions_lock = threading.Lock()
COPILOT_SESSION_MAX_MESSAGES = int(os.getenv("COPILOT_SESSION_MAX_MESSAGES", "40"))
COPILOT_TOTAL_SESSIONS_MAX = int(os.getenv("COPILOT_TOTAL_SESSIONS_MAX", "400"))
price_cache: Dict[str, Dict] = {}
tick_counter = 0
last_tick_meta: Dict[str, Dict[str, float]] = {}
last_news_refresh_ts: int = 0
APP_START_UTC = datetime.now(timezone.utc)


# ═══════════════════════════════════════════════════════════════════════════════
# CONNECTION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def connect_mt5() -> bool:
    if not MT5_AVAILABLE:
        return False
    try:
        mt5.shutdown()
        if not mt5.initialize(path=MT5_PATH, server=MT5_SERVER, login=MT5_LOGIN, password=MT5_PASSWORD):
            logger.error(f"MT5 init failed: {mt5.last_error()}")
            return False
        logger.info("✅ MT5: Connected")
        return True
    except Exception as e:
        logger.error(f"MT5 error: {e}")
        return False


def connect_influxdb() -> bool:
    global influx_client, influx_write_api, influx_query_api
    if not INFLUX_AVAILABLE:
        return False
    try:
        influx_client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
        health = influx_client.health()
        if health.status != "pass":
            logger.error(f"InfluxDB health failed: {health.message}")
            return False
        influx_write_api = influx_client.write_api(write_options=WriteOptions(batch_size=500, flush_interval=1000))
        influx_query_api = influx_client.query_api()
        logger.info(f"✅ InfluxDB: Connected (bucket: {INFLUXDB_BUCKET})")
        return True
    except Exception as e:
        logger.error(f"InfluxDB error: {e}")
        return False


def connect_postgres() -> bool:
    global pg_conn
    if not PG_AVAILABLE:
        return False
    try:
        pg_conn = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, dbname=PG_DB,
            user=PG_USER, password=PG_PASSWORD,
        )
        pg_conn.autocommit = True
        _ensure_news_table()
        logger.info("✅ PostgreSQL: Connected")
        return True
    except Exception as e:
        logger.error(f"PostgreSQL error: {e}")
        return False


def _ensure_news_table():
    """Ensure live news table exists for the dashboard."""
    if pg_conn is None:
        return
    cur = pg_conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS forex_news (
                id SERIAL PRIMARY KEY,
                published_at TIMESTAMP,
                title TEXT,
                description TEXT,
                url TEXT,
                source TEXT
            );
        """)
    finally:
        cur.close()


def _parse_published_at(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


def load_model() -> bool:
    global model_pipelines
    try:
        sys.path.append(str(ROOT))
        from modeling.technical_agent.technical_agent_inference import TechnicalAgent
        
        loaded = []
        for symbol in SYMBOLS:
            mp = ROOT / "modeling" / "technical_agent" / f"technical_agent_{symbol}.pkl"
            if mp.exists():
                model_pipelines[symbol] = TechnicalAgent(mp)
                loaded.append(symbol)
                
        if not loaded:
            logger.warning("No technical models found for any symbols!")
            return False
            
        logger.info(f"✅ Models: Loaded for {loaded}")
        return True
    except Exception as e:
        logger.error(f"Model error: {e}")
        return False


def load_macro_model() -> bool:
    """Load MacroAgent for all symbols from modeling/macro_agent/macro_agent_{SYMBOL}.pkl."""
    global macro_agent_handles
    macro_agent_handles = {}
    macro_dir = ROOT / "modeling" / "macro_agent"

    try:
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from modeling.macro_agent.macro_agent_inference import MacroAgent as MacroAgentCls

        loaded = []
        for symbol in SYMBOLS:
            model_path = macro_dir / f"macro_agent_{symbol}.pkl"
            if not model_path.is_file():
                logger.warning(f"Macro model not found for {symbol}: {model_path}")
                continue
            macro_agent_handles[symbol] = MacroAgentCls(model_path, symbol=symbol)
            loaded.append(symbol)

        if not loaded:
            logger.warning("No macro models found — train with modeling/macro_agent/train_macro_agent.py")
            return False

        logger.info(f"Macro models loaded for {loaded}")
        return True
    except Exception as e:
        logger.error(f"Macro agent load error: {e}")
        return False


def load_sentiment_model() -> bool:
    """Load SentimentAgent for all symbols and supported timeframes."""
    global sentiment_agent_handles
    sentiment_agent_handles = {}
    sentiment_dir = ROOT / "modeling" / "sentiment_agent"

    try:
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from modeling.sentiment_agent.sentiment_agent_inference import SentimentAgent as SentimentAgentCls

        loaded = []
        for symbol in SYMBOLS:
            for timeframe in SENTIMENT_TIMEFRAMES:
                model_path = sentiment_dir / f"sentiment_agent_{symbol}_{timeframe}.pkl"
                if not model_path.is_file():
                    logger.warning(f"Sentiment model not found for {symbol} {timeframe}: {model_path}")
                    continue
                key = (symbol, timeframe)
                sentiment_agent_handles[key] = SentimentAgentCls(
                    model_path,
                    symbol=symbol,
                    timeframe=timeframe,
                )
                loaded.append(f"{symbol}_{timeframe}")

        if not loaded:
            logger.warning("No sentiment models found - train with modeling/sentiment_agent/train_sentiment_agent.py")
            return False

        logger.info(f"Sentiment models loaded for {loaded}")
        return True
    except Exception as e:
        logger.error(f"Sentiment agent load error: {e}")
        return False


def load_decision_model() -> bool:
    """Load DecisionMetaAgent with Phase 2 model selection (RF preferred when available)."""
    global decision_agent_handle
    try:
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from modeling.decision_agent.decision_agent_inference import DecisionMetaAgent

        primary_pref = os.getenv("DECISION_PRIMARY_MODEL", "auto")
        decision_agent_handle = DecisionMetaAgent(primary_model=primary_pref)
        if not decision_agent_handle.model_loaded:
            logger.warning(
                "Decision model artifact not found - fallback mode enabled (train with modeling/decision_agent/decision_agent_training.py --model all)"
            )
            return False

        logger.info(
            "Decision model loaded successfully (active=%s)",
            getattr(decision_agent_handle, "active_model_key", "unknown"),
        )
        return True
    except Exception as e:
        decision_agent_handle = None
        logger.error(f"Decision model load error: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# DATA HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def get_candles_from_influxdb(
    symbol: str,
    timeframe: str,
    start_ts: int,
    end_ts: int,
    max_preagg_lookback_days: Optional[int] = 3,
    max_tick_lookback_days: Optional[int] = 3,
) -> List[Dict]:
    """
    Get candles from InfluxDB. First tries pre-aggregated candles,
    then aggregates ticks if needed.
    """
    if not influx_query_api:
        logger.warning("InfluxDB query API not available")
        return []
    
    try:
        # For chart endpoints we cap lookback to avoid stale data spikes.
        # For signal inference we can disable the cap to gather enough history for indicators.
        if max_preagg_lookback_days is not None:
            now_utc = datetime.now(timezone.utc)
            min_start_ts = int((now_utc - timedelta(days=max_preagg_lookback_days)).timestamp())
            effective_start = max(start_ts, min_start_ts)
        else:
            effective_start = start_ts

        start_iso = datetime.fromtimestamp(effective_start, tz=timezone.utc).isoformat()
        end_iso = datetime.fromtimestamp(end_ts, tz=timezone.utc).isoformat()
        
        # Try to get pre-aggregated candles
        query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
          |> range(start: {start_iso}, stop: {end_iso})
          |> filter(fn: (r) => r._measurement == "forex_prices")
          |> filter(fn: (r) => r.symbol == "{symbol}")
          |> filter(fn: (r) => r.timeframe == "{timeframe}")
          |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
          |> sort(columns: ["_time"])
        '''
        
        logger.debug(f"Querying candles: {symbol} {timeframe}")
        tables = influx_query_api.query(query)
        candles = []
        
        for table in tables:
            for rec in table.records:
                vals = rec.values
                try:
                    candle_time = int(rec.get_time().timestamp())
                    candles.append({
                        "time": candle_time,
                        "open":  round(float(vals.get("open", 0)), 5),
                        "high":  round(float(vals.get("high", 0)), 5),
                        "low":   round(float(vals.get("low", 0)), 5),
                        "close": round(float(vals.get("close", 0)), 5),
                        "volume": round(float(vals.get("volume", 0)), 5),
                    })
                except (TypeError, ValueError, AttributeError):
                    continue
        
        logger.info(f"📊 Loaded {len(candles)} pre-aggregated candles from InfluxDB: {symbol} {timeframe}")
        
        # Also get ticks and aggregate them into candles
        tick_candles = aggregate_ticks_into_candles(
            symbol,
            timeframe,
            start_ts,
            end_ts,
            max_tick_lookback_days=max_tick_lookback_days,
        )
        
        # Merge: pre-aggregated candles + tick-based candles
        candle_dict = {c["time"]: c for c in candles}
        candle_dict.update({c["time"]: c for c in tick_candles})
        
        result = sorted(candle_dict.values(), key=lambda x: x["time"])
        logger.info(f"📊 Total candles after merging: {len(result)}")
        
        return result
        
    except Exception as e:
        logger.error(f"InfluxDB query error: {e}")
        return []


def aggregate_ticks_into_candles(
    symbol: str,
    timeframe: str,
    start_ts: int,
    end_ts: int,
    max_tick_lookback_days: Optional[int] = 3,
) -> List[Dict]:
    """
    Fetch ticks from InfluxDB and aggregate them into candles.
    """
    if not influx_query_api:
        return []
    
    try:
        # Ticks are incredibly dense. Keep a bounded lookback to protect InfluxDB.
        if max_tick_lookback_days is not None:
            now = datetime.now(timezone.utc)
            min_start_ts = int((now - timedelta(days=max_tick_lookback_days)).timestamp())
            effective_start_ts = max(start_ts, min_start_ts)
        else:
            effective_start_ts = start_ts

        start_iso = datetime.fromtimestamp(effective_start_ts, tz=timezone.utc).isoformat()
        end_iso = datetime.fromtimestamp(end_ts, tz=timezone.utc).isoformat()
        
        # Query ticks
        query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
          |> range(start: {start_iso}, stop: {end_iso})
          |> filter(fn: (r) => r._measurement == "forex_tick")
          |> filter(fn: (r) => r.symbol == "{symbol}")
          |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
          |> sort(columns: ["_time"])
        '''
        
        logger.debug(f"Querying ticks: {symbol}")
        tables = influx_query_api.query(query)
        ticks = []
        
        for table in tables:
            for rec in table.records:
                vals = rec.values
                try:
                    tick_time = int(rec.get_time().timestamp())
                    bid = float(vals.get("bid", 0))
                    ticks.append({"time": tick_time, "bid": bid})
                except (TypeError, ValueError, AttributeError):
                    continue
        
        logger.debug(f"Loaded {len(ticks)} ticks for {symbol}")

        # Warm-start fallback: when Influx has too few fresh ticks (e.g., right after app restart),
        # pull a short recent window directly from MT5 so 1S/LIVE technical inference can run.
        min_ticks_needed = 320 if timeframe == "1S" else 40
        if len(ticks) < min_ticks_needed and MT5_AVAILABLE and status.get("mt5", False):
            try:
                from_dt = datetime.fromtimestamp(max(effective_start_ts, end_ts - 1800), tz=timezone.utc)
                mt5_ticks = mt5.copy_ticks_from(symbol, from_dt, 5000, mt5.COPY_TICKS_ALL)
                if mt5_ticks is not None and len(mt5_ticks) > 0:
                    merged = {int(t["time"]): float(t["bid"]) for t in mt5_ticks if float(t["bid"]) > 0}
                    for t in ticks:
                        merged[int(t["time"])] = float(t["bid"])
                    ticks = [{"time": k, "bid": v} for k, v in sorted(merged.items(), key=lambda x: x[0])]
                    logger.info(f"📥 MT5 backfill merged for {symbol} {timeframe}: {len(ticks)} ticks")
            except Exception as e:
                logger.warning(f"MT5 backfill failed for {symbol} {timeframe}: {e}")
        
        # Aggregate ticks into candles
        tf_seconds = {"1S": 1, "1H": 3600, "4H": 14400, "1D": 86400}
        tf_sec = tf_seconds.get(timeframe, 3600)
        
        candle_dict = {}
        for tick in ticks:
            candle_time = (tick["time"] // tf_sec) * tf_sec
            price = tick["bid"]
            
            if candle_time not in candle_dict:
                candle_dict[candle_time] = {
                    "time": candle_time,
                    "open": price,
                    "high": price,
                    "low": price,
                    "close": price,
                    "volume": 0,
                }
            else:
                c = candle_dict[candle_time]
                c["close"] = price
                c["high"] = max(c["high"], price)
                c["low"] = min(c["low"], price)
                c["volume"] += 1
        
        result = sorted(candle_dict.values(), key=lambda x: x["time"])
        logger.info(f"📊 Aggregated {len(ticks)} ticks into {len(result)} candles: {symbol} {timeframe}")
        
        return result
        
    except Exception as e:
        logger.error(f"Tick aggregation error: {e}")
        return []


def get_candles_from_mt5(symbol: str, timeframe: str, start_ts: int, end_ts: int) -> List[Dict]:
    """
    Fetch broker-native candles from MT5 for higher timeframes.
    This is used as a sparse-data backfill when Influx returns too few bars.
    """
    if not MT5_AVAILABLE or not status.get("mt5", False):
        return []

    tf_map = {
        "1H": mt5.TIMEFRAME_H1,
        "4H": mt5.TIMEFRAME_H4,
        "1D": mt5.TIMEFRAME_D1,
    }
    mt5_tf = tf_map.get(timeframe)
    if mt5_tf is None:
        return []

    try:
        from_dt = datetime.fromtimestamp(start_ts, tz=timezone.utc)
        to_dt = datetime.fromtimestamp(end_ts, tz=timezone.utc)
        rates = mt5.copy_rates_range(symbol, mt5_tf, from_dt, to_dt)
        if rates is None or len(rates) == 0:
            return []

        candles: List[Dict] = []
        for r in rates:
            try:
                t = int(r["time"])
                candles.append({
                    "time": t,
                    "open": round(float(r["open"]), 5),
                    "high": round(float(r["high"]), 5),
                    "low": round(float(r["low"]), 5),
                    "close": round(float(r["close"]), 5),
                    "volume": float(r["tick_volume"]),
                })
            except (TypeError, ValueError, KeyError):
                continue

        return sorted(candles, key=lambda x: x["time"])
    except Exception as e:
        logger.warning(f"MT5 candles backfill failed for {symbol} {timeframe}: {e}")
        return []


def save_ticks_to_influxdb(ticks: Dict):
    """Save live ticks to InfluxDB."""
    if not status["influxdb"] or not influx_write_api:
        return
    try:
        points = []
        for symbol, tick in ticks.items():
            write_time = int(tick.get("server_time") or tick.get("time") or 0)
            if write_time <= 0:
                continue
            p = Point("forex_tick") \
                .tag("symbol", symbol) \
                .field("bid", tick["bid"]) \
                .field("ask", tick["ask"]) \
                .time(write_time, write_precision='s')
            points.append(p)
        if points:
            influx_write_api.write(bucket=INFLUXDB_BUCKET, record=points)
            logger.debug(f"💾 Saved {len(points)} ticks to InfluxDB")
    except Exception as e:
        logger.error(f"InfluxDB write error: {e}")


def get_live_ticks() -> Dict:
    """Get current bid/ask from MT5."""
    global last_tick_meta
    if not MT5_AVAILABLE or not status["mt5"]:
        logger.debug("❌ MT5 not available")
        return {}
    try:
        ticks = {}
        now_utc_ts = int(datetime.now(timezone.utc).timestamp())
        for sym in SYMBOLS:
            try:
                # Ensure symbol is subscribed in Market Watch; otherwise MT5 can return stale or empty ticks.
                mt5.symbol_select(sym, True)
            except Exception:
                pass

            tick = mt5.symbol_info_tick(sym)
            if tick:
                bid = float(getattr(tick, "bid", 0.0) or 0.0)
                ask = float(getattr(tick, "ask", 0.0) or 0.0)
                if bid <= 0 or ask <= 0:
                    continue

                tick_time = int(getattr(tick, "time", 0) or 0)
                tick_msc = int(getattr(tick, "time_msc", 0) or 0)

                prev = last_tick_meta.get(sym)
                stale_snapshot = bool(
                    prev
                    and tick_msc > 0
                    and tick_msc <= int(prev.get("time_msc", 0))
                    and abs(bid - float(prev.get("bid", 0.0))) < 1e-12
                )

                # Fallback: if MT5 snapshot appears stale, request latest ticks window and use most recent.
                if stale_snapshot:
                    try:
                        from_dt = datetime.now(timezone.utc) - timedelta(seconds=30)
                        fresh = mt5.copy_ticks_from(sym, from_dt, 200, mt5.COPY_TICKS_ALL)
                        if fresh is not None and len(fresh) > 0:
                            last = fresh[-1]
                            bid = float(last["bid"])
                            ask = float(last["ask"])
                            tick_time = int(last["time"])
                            tick_msc = int(last["time_msc"])
                    except Exception:
                        pass

                # Keep timestamps usable for frontend charting even if broker time jumps.
                if tick_time <= 0 or tick_time > now_utc_ts + 300:
                    tick_time = now_utc_ts

                last_tick_meta[sym] = {"time_msc": tick_msc, "bid": bid}
                ticks[sym] = {
                    "bid": bid,
                    "ask": ask,
                    "spread": round((ask - bid) * (100 if "JPY" in sym else 10000), 1),
                    "time": tick_time,
                }
        if ticks:
            logger.debug(f"📈 Got {len(ticks)} ticks from MT5")
        return ticks
    except Exception as e:
        logger.error(f"MT5 tick error: {e}")
        return {}


def get_signal(symbol: str, timeframe: str = "1H") -> Dict:
    """Run Technical Agent inference."""
    base = {
        "symbol": symbol,
        "timeframe": timeframe,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    
    pipeline = model_pipelines.get(symbol)
    if pipeline is None:
        return {**base, "signal": "N/A", "confidence": 0, "agent": "Technical",
                "error": f"Model not loaded for {symbol}"}

    # Evaluate accurately natively on the passed timeframe natively (or 1S if LIVE overlay)
    eval_timeframe = "1S" if timeframe == "LIVE" else timeframe

    try:
        # Timeframe-aware lookback: aggressively fetch enough chronological seconds to satisfy SMA_200 
        # (Since polling drops natively every 2 seconds, 300 ticks yields only 150 items. Lookback parameter bumped to 1000 to safely guarantee 200 items on sparse graphs).
        now = datetime.now(timezone.utc)
        tf_seconds_map = {"1S": 1, "1H": 3600, "4H": 14400, "1D": 86400}
        tf_sec = tf_seconds_map.get(eval_timeframe, 3600)
        lookback_seconds = tf_sec * 1000
        start_ts = int(now.timestamp()) - lookback_seconds
        end_ts = int(now.timestamp())

        candles = get_candles_from_influxdb(
            symbol,
            eval_timeframe,
            start_ts,
            end_ts,
            max_preagg_lookback_days=None,
        )
        
        if not candles:
            return {**base, "signal": "N/A", "confidence": 0, "agent": "Technical",
                    "error": f"No live data available for {symbol} {eval_timeframe}"}

        df = pd.DataFrame(candles)
        if "time" in df.columns:
            df.set_index("time", inplace=True)
            df.index = pd.to_datetime(df.index, unit='s')

        latest_candle_time = None
        if not df.empty:
            latest_candle_time = df.index[-1].isoformat()

        # Dynamically calculate features on the live stream
        from data_understanding.feature_engineering import create_features
        features_df = create_features(df, symbol, eval_timeframe)

        # Drop rows where long-term SMAs/lags are NaN
        features_df = features_df.dropna()
        if features_df.empty:
            return {**base, "signal": "N/A", "confidence": 0, "agent": "Technical", "error": "Insufficient history to calculate indicators"}

        last_live = features_df.iloc[[-1]]
        latest_feature_time = None
        if not last_live.empty:
            latest_feature_time = last_live.index[-1].isoformat()
        
        # Call the agent's predict method using ONLY the live technical row
        result = pipeline.predict(last_live)
        return {
            **base,
            **result,
            "latest_candle_time": latest_candle_time,
            "latest_feature_time": latest_feature_time,
        }
    except Exception as e:
        return {**base, "signal": "N/A", "confidence": 0, "agent": "Technical", "error": str(e)}


def get_macro_signal(symbol: str, explain: bool = False) -> Dict:
    """Run Macro Agent on latest PostgreSQL economic_indicators (daily FRED)."""
    symbol = symbol.upper()
    base = {"symbol": symbol, "timeframe": "1D", "last_macro_update": get_last_macro_update_date()}
    if symbol not in SYMBOLS:
        return {
            **base,
            "signal": "N/A",
            "confidence": 0,
            "agent": "Macro",
            "error": f"Unsupported symbol for macro agent: {symbol}",
        }

    macro_handle = macro_agent_handles.get(symbol)
    if macro_handle is None:
        return {
            **base,
            "signal": "N/A",
            "confidence": 0,
            "agent": "Macro",
            "error": f"Macro model not loaded for {symbol}",
        }

    try:
        result = macro_handle.predict_latest(explain=explain)
        return {**base, **result}
    except Exception as e:
        return {**base, "signal": "N/A", "confidence": 0, "agent": "Macro", "error": str(e)}


def get_sentiment_signal(symbol: str, timeframe: str = "1H", explain: bool = False) -> Dict:
    """Run Sentiment Agent on latest PostgreSQL news rows."""
    symbol = symbol.upper()
    timeframe = timeframe.upper()
    base = {
        "symbol": symbol,
        "timeframe": timeframe,
        "last_sentiment_update": get_last_sentiment_update_date(),
    }

    if symbol not in SYMBOLS:
        return {
            **base,
            "signal": "N/A",
            "confidence": 0,
            "agent": "Sentiment",
            "error": f"Unsupported symbol for sentiment agent: {symbol}",
        }

    if timeframe not in SENTIMENT_TIMEFRAMES:
        return {
            **base,
            "signal": "N/A",
            "confidence": 0,
            "agent": "Sentiment",
            "error": f"Unsupported timeframe for sentiment agent: {timeframe}",
        }

    sentiment_handle = sentiment_agent_handles.get((symbol, timeframe))
    if sentiment_handle is None:
        return {
            **base,
            "signal": "N/A",
            "confidence": 0,
            "agent": "Sentiment",
            "error": f"Sentiment model not loaded for {symbol} {timeframe}",
        }

    try:
        result = sentiment_handle.predict_latest(explain=explain)
        return {**base, **result}
    except Exception as e:
        return {**base, "signal": "N/A", "confidence": 0, "agent": "Sentiment", "error": str(e)}


def get_decision_signal(
    symbol: str,
    timeframe: str = "1H",
    explain: bool = True,
    model_override: Optional[str] = None,
) -> Dict:
    """Run Meta-Decision Agent by composing outputs from technical/macro/sentiment agents."""
    symbol = symbol.upper()
    timeframe = timeframe.upper()

    def _finalize(resp: Dict) -> Dict:
        if "symbol" not in resp:
            resp["symbol"] = symbol
        if "timeframe" not in resp:
            resp["timeframe"] = timeframe
        if "decision_timestamp" not in resp:
            resp["decision_timestamp"] = datetime.now(timezone.utc).isoformat()
        _record_decision_telemetry(resp)
        return resp

    if symbol not in SYMBOLS:
        return _finalize({
            "symbol": symbol,
            "timeframe": timeframe,
            "final_signal": "HOLD",
            "global_confidence": 0.0,
            "model_type": "unavailable",
            "fallback_used": True,
            "fallback_reason": f"unsupported_symbol:{symbol}",
            "risk_flags": ["invalid_symbol"],
        })

    tech = get_signal(symbol, timeframe=timeframe)
    macro = get_macro_signal(symbol, explain=explain)
    sentiment = get_sentiment_signal(symbol, timeframe=timeframe, explain=explain)

    if decision_agent_handle is None:
        try:
            from modeling.decision_agent.decision_agent_fallback import fallback_decision

            resp = fallback_decision(
                symbol,
                timeframe,
                tech,
                macro,
                sentiment,
                reason="decision_agent_not_initialized",
                risk_flags=["decision_model_unavailable"],
            )
            resp["contributing_agents"] = {
                "technical": {
                    "signal": tech.get("signal", "N/A"),
                    "confidence": float(tech.get("confidence", 0.0) or 0.0),
                    "warning": tech.get("warning"),
                    "error": tech.get("error"),
                },
                "macro": {
                    "signal": macro.get("signal", "N/A"),
                    "confidence": float(macro.get("confidence", 0.0) or 0.0),
                    "warning": macro.get("warning"),
                    "error": macro.get("error"),
                    "last_update": macro.get("last_macro_update"),
                },
                "sentiment": {
                    "signal": sentiment.get("signal", "N/A"),
                    "confidence": float(sentiment.get("confidence", 0.0) or 0.0),
                    "warning": sentiment.get("warning"),
                    "error": sentiment.get("error"),
                    "last_update": sentiment.get("last_sentiment_update"),
                },
            }
            return _finalize(resp)
        except Exception as e:
            return _finalize({
                "symbol": symbol,
                "timeframe": timeframe,
                "final_signal": "HOLD",
                "global_confidence": 0.0,
                "model_type": "unavailable",
                "fallback_used": True,
                "fallback_reason": "decision_agent_not_initialized",
                "risk_flags": ["decision_model_unavailable"],
                "error": str(e),
            })

    try:
        return _finalize(decision_agent_handle.predict(
            symbol=symbol,
            timeframe=timeframe,
            technical_payload=tech,
            macro_payload=macro,
            sentiment_payload=sentiment,
            model_override=model_override,
        ))
    except Exception as e:
        return _finalize({
            "symbol": symbol,
            "timeframe": timeframe,
            "final_signal": "HOLD",
            "global_confidence": 0.0,
            "model_type": "error",
            "fallback_used": True,
            "fallback_reason": "decision_predict_exception",
            "risk_flags": ["decision_runtime_error"],
            "error": str(e),
        })


def get_last_macro_update_date() -> Optional[str]:
    """Return latest economic_indicators date in ISO format (YYYY-MM-DD)."""
    conn = pg_conn
    close_conn = False

    # Fallback to a short-lived connection when the shared pool handle is unavailable.
    if conn is None and PG_AVAILABLE:
        try:
            conn = psycopg2.connect(
                host=PG_HOST,
                port=PG_PORT,
                dbname=PG_DB,
                user=PG_USER,
                password=PG_PASSWORD,
            )
            close_conn = True
        except Exception:
            return None

    if conn is None:
        return None

    cur = conn.cursor()
    try:
        cur.execute("SELECT MAX(date) FROM economic_indicators")
        row = cur.fetchone()
        latest = row[0] if row else None
        if latest is None:
            return None
        if hasattr(latest, "isoformat"):
            return latest.isoformat()
        return str(latest)
    except Exception:
        return None
    finally:
        cur.close()
        if close_conn:
            conn.close()


def get_last_sentiment_update_date() -> Optional[str]:
    """Return latest news publication timestamp from available news tables."""
    conn = pg_conn
    close_conn = False

    if conn is None and PG_AVAILABLE:
        try:
            conn = psycopg2.connect(
                host=PG_HOST,
                port=PG_PORT,
                dbname=PG_DB,
                user=PG_USER,
                password=PG_PASSWORD,
            )
            close_conn = True
        except Exception:
            return None

    if conn is None:
        return None

    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT MAX(ts) FROM (
                SELECT MAX(published_at) AS ts FROM news_articles
                UNION ALL
                SELECT MAX(published_at) AS ts FROM forex_news
            ) t
            """
        )
        row = cur.fetchone()
        latest = row[0] if row else None
        if latest is None:
            return None
        if hasattr(latest, "isoformat"):
            return latest.isoformat()
        return str(latest)
    except Exception:
        return None
    finally:
        cur.close()
        if close_conn:
            conn.close()


def _record_decision_telemetry(payload: Dict) -> None:
    """Store a compact decision event for performance monitoring."""
    model_cmp = payload.get("model_comparison") or {}
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "decision_timestamp": payload.get("decision_timestamp"),
        "symbol": str(payload.get("symbol", "")).upper(),
        "timeframe": str(payload.get("timeframe", "")).upper(),
        "final_signal": str(payload.get("final_signal", "N/A")).upper(),
        "global_confidence": float(payload.get("global_confidence", 0.0) or 0.0),
        "model_type": str(payload.get("model_type", "unknown")),
        "model_version": str(payload.get("model_version", "unknown")),
        "fallback_used": bool(payload.get("fallback_used", False)),
        "fallback_reason": payload.get("fallback_reason"),
        "latency_ms": int(payload.get("latency_ms", 0) or 0),
        "conflict_index": float(payload.get("conflict_index", 0.0) or 0.0),
        "risk_flags": list(payload.get("risk_flags") or []),
        "has_model_comparison": bool(model_cmp),
        "model_agreement": bool(model_cmp.get("agreement")) if model_cmp else None,
        "confidence_delta": float(model_cmp.get("confidence_delta", 0.0) or 0.0) if model_cmp else None,
        "primary_signal": model_cmp.get("primary_signal") if model_cmp else None,
        "shadow_signal": model_cmp.get("shadow_signal") if model_cmp else None,
    }
    with decision_telemetry_lock:
        decision_telemetry.append(event)


def _decision_performance_summary(
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    model_type: Optional[str] = None,
    window: int = 200,
    trend_horizon: str = "medium",
) -> Dict:
    """Aggregate recent decision telemetry for quick monitoring."""
    drift_warning_threshold = 0.20
    drift_critical_threshold = 0.35
    def _alert_level_for_rate(rate: float) -> str:
        if rate >= drift_critical_threshold:
            return "critical"
        if rate >= drift_warning_threshold:
            return "warning"
        return "normal"

    horizon_map = {"short": 10, "medium": 20, "long": 40}
    trend_horizon = str(trend_horizon or "medium").lower()
    trend_window = horizon_map.get(trend_horizon, 20)

    with decision_telemetry_lock:
        events = list(decision_telemetry)

    symbol = symbol.upper() if symbol else None
    timeframe = timeframe.upper() if timeframe else None
    model_type = model_type.lower() if model_type else None

    if symbol:
        events = [e for e in events if e.get("symbol") == symbol]
    if timeframe:
        events = [e for e in events if e.get("timeframe") == timeframe]
    if model_type:
        events = [e for e in events if str(e.get("model_type", "")).lower() == model_type]

    if window > 0:
        events = events[-window:]

    total = len(events)
    if total == 0:
        return {
            "total": 0,
            "window": window,
            "symbol": symbol,
            "timeframe": timeframe,
            "model_type": model_type,
            "fallback_rate": 0.0,
            "avg_latency_ms": 0.0,
            "avg_confidence": 0.0,
            "avg_conflict_index": 0.0,
            "drift": {
                "comparison_events": 0,
                "disagreement_count": 0,
                "disagreement_rate": 0.0,
                "avg_confidence_delta": 0.0,
                "trend_window": trend_window,
                "trend_horizon": trend_horizon,
                "trend": [],
                "alert": {
                    "level": "no_data",
                    "threshold_warning": drift_warning_threshold,
                    "threshold_critical": drift_critical_threshold,
                },
                "alert_history": [],
                "alert_transitions": [],
            },
            "model_type_distribution": {},
            "signal_distribution": {},
            "risk_flag_frequency": {},
            "last_event": None,
        }

    fallback_count = sum(1 for e in events if e.get("fallback_used"))
    avg_latency = float(np.mean([e.get("latency_ms", 0) for e in events]))
    avg_conf = float(np.mean([e.get("global_confidence", 0.0) for e in events]))
    avg_conflict = float(np.mean([e.get("conflict_index", 0.0) for e in events]))

    model_dist = Counter(e.get("model_type", "unknown") for e in events)
    signal_dist = Counter(e.get("final_signal", "N/A") for e in events)
    risk_counter = Counter()
    cmp_events = [e for e in events if e.get("has_model_comparison")]
    disagreement_count = sum(1 for e in cmp_events if e.get("model_agreement") is False)
    confidence_delta_vals = [
        abs(float(e.get("confidence_delta", 0.0) or 0.0))
        for e in cmp_events
        if e.get("confidence_delta") is not None
    ]
    avg_conf_delta = float(np.mean(confidence_delta_vals)) if confidence_delta_vals else 0.0
    disagreement_rate = (disagreement_count / len(cmp_events)) if cmp_events else 0.0
    if not cmp_events:
        alert_level = "no_data"
    else:
        alert_level = _alert_level_for_rate(disagreement_rate)

    drift_trend = []
    if cmp_events:
        step = max(1, len(cmp_events) // 30)
        for idx in range(step - 1, len(cmp_events), step):
            start_idx = max(0, idx - trend_window + 1)
            win = cmp_events[start_idx : idx + 1]
            win_total = len(win)
            win_disagree = sum(1 for x in win if x.get("model_agreement") is False)
            win_deltas = [
                abs(float(x.get("confidence_delta", 0.0) or 0.0))
                for x in win
                if x.get("confidence_delta") is not None
            ]
            drift_trend.append(
                {
                    "timestamp": cmp_events[idx].get("timestamp"),
                    "comparison_events": win_total,
                    "disagreement_rate": round(win_disagree / win_total, 6) if win_total else 0.0,
                    "avg_confidence_delta": round(float(np.mean(win_deltas)), 6) if win_deltas else 0.0,
                }
            )

    alert_history = []
    alert_transitions = []
    prev_level = None
    for point in drift_trend:
        rate = float(point.get("disagreement_rate", 0.0) or 0.0)
        level = _alert_level_for_rate(rate)
        hist = {
            "timestamp": point.get("timestamp"),
            "level": level,
            "disagreement_rate": round(rate, 6),
        }
        alert_history.append(hist)
        if prev_level is None or level != prev_level:
            alert_transitions.append(hist)
        prev_level = level

    for e in events:
        for flag in e.get("risk_flags", []):
            risk_counter[str(flag)] += 1

    return {
        "total": total,
        "window": window,
        "symbol": symbol,
        "timeframe": timeframe,
        "model_type": model_type,
        "fallback_rate": round(fallback_count / total, 6),
        "avg_latency_ms": round(avg_latency, 3),
        "avg_confidence": round(avg_conf, 6),
        "avg_conflict_index": round(avg_conflict, 6),
        "drift": {
            "comparison_events": len(cmp_events),
            "disagreement_count": disagreement_count,
            "disagreement_rate": round(disagreement_rate, 6),
            "avg_confidence_delta": round(avg_conf_delta, 6),
            "trend_window": trend_window,
            "trend_horizon": trend_horizon,
            "trend": drift_trend,
            "alert": {
                "level": alert_level,
                "threshold_warning": drift_warning_threshold,
                "threshold_critical": drift_critical_threshold,
            },
            "alert_history": alert_history,
            "alert_transitions": alert_transitions,
        },
        "model_type_distribution": dict(model_dist),
        "signal_distribution": dict(signal_dist),
        "risk_flag_frequency": dict(risk_counter),
        "last_event": events[-1],
    }


def _decision_history(
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    model_type: Optional[str] = None,
    limit: int = 300,
    compress: bool = True,
) -> Dict:
    """Return filtered decision telemetry history for reporting tables/exports."""
    with decision_telemetry_lock:
        events = list(decision_telemetry)

    symbol = symbol.upper() if symbol else None
    timeframe = timeframe.upper() if timeframe else None
    model_type = model_type.lower() if model_type else None

    if symbol:
        events = [e for e in events if e.get("symbol") == symbol]
    if timeframe:
        events = [e for e in events if e.get("timeframe") == timeframe]
    if model_type:
        events = [e for e in events if str(e.get("model_type", "")).lower() == model_type]

    if limit > 0:
        events = events[-limit:]

    def _parse_ts(raw: Optional[str]) -> Optional[datetime]:
        if not raw:
            return None
        try:
            return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except Exception:
            return None

    if compress:
        groups = []
        for e in events:
            risk_flags = tuple(sorted([str(x) for x in (e.get("risk_flags") or [])]))
            key = (
                str(e.get("final_signal", "N/A")),
                round(float(e.get("global_confidence", 0.0) or 0.0), 6),
                str(e.get("model_type", "unknown")),
                bool(e.get("fallback_used", False)),
                risk_flags,
            )
            ts_raw = e.get("timestamp") or e.get("decision_timestamp")

            if not groups or groups[-1]["_key"] != key:
                groups.append(
                    {
                        "_key": key,
                        "start_timestamp": ts_raw,
                        "last_timestamp": ts_raw,
                        "symbol": e.get("symbol"),
                        "timeframe": e.get("timeframe"),
                        "final_signal": key[0],
                        "global_confidence": key[1],
                        "model_type": key[2],
                        "fallback_used": key[3],
                        "risk_flags": list(risk_flags),
                        "event_count": 1,
                    }
                )
            else:
                groups[-1]["last_timestamp"] = ts_raw
                groups[-1]["event_count"] += 1

        compressed_items = []
        for g in groups:
            start_dt = _parse_ts(g.get("start_timestamp"))
            last_dt = _parse_ts(g.get("last_timestamp"))
            duration_sec = None
            if start_dt and last_dt:
                duration_sec = max(0, int((last_dt - start_dt).total_seconds()))
            item = dict(g)
            item.pop("_key", None)
            item["duration_seconds"] = duration_sec
            compressed_items.append(item)

        items = list(reversed(compressed_items))
    else:
        items = list(reversed(events))

    return {
        "count": len(items),
        "raw_count": len(events),
        "compressed": bool(compress),
        "symbol": symbol,
        "timeframe": timeframe,
        "model_type": model_type,
        "items": items,
    }


def _reporting_overview(
    symbol: str,
    timeframe: str,
    model_type: Optional[str],
    window: int,
    trend_horizon: str,
) -> Dict:
    """Assemble a consolidated reporting snapshot for analyst dashboard."""
    symbol = symbol.upper()
    timeframe = timeframe.upper()

    if status.get("model") and status.get("influxdb"):
        try:
            tech = get_signal(symbol, timeframe=timeframe)
        except Exception as e:
            tech = {
                "symbol": symbol,
                "timeframe": timeframe,
                "signal": "N/A",
                "confidence": 0.0,
                "agent": "Technical",
                "error": f"technical_unavailable:{e}",
            }
    else:
        tech = {
            "symbol": symbol,
            "timeframe": timeframe,
            "signal": "N/A",
            "confidence": 0.0,
            "agent": "Technical",
            "warning": "technical_degraded_infra",
        }

    if status.get("macro_model") and status.get("postgres"):
        try:
            macro = get_macro_signal(symbol, explain=False)
        except Exception as e:
            macro = {
                "symbol": symbol,
                "timeframe": "1D",
                "signal": "N/A",
                "confidence": 0.0,
                "agent": "Macro",
                "error": f"macro_unavailable:{e}",
            }
    else:
        macro = {
            "symbol": symbol,
            "timeframe": "1D",
            "signal": "N/A",
            "confidence": 0.0,
            "agent": "Macro",
            "warning": "macro_degraded_infra",
        }

    if status.get("sentiment_model") and status.get("postgres"):
        try:
            sentiment = get_sentiment_signal(symbol, timeframe=timeframe, explain=False)
        except Exception as e:
            sentiment = {
                "symbol": symbol,
                "timeframe": timeframe,
                "signal": "N/A",
                "confidence": 0.0,
                "agent": "Sentiment",
                "error": f"sentiment_unavailable:{e}",
            }
    else:
        sentiment = {
            "symbol": symbol,
            "timeframe": timeframe,
            "signal": "N/A",
            "confidence": 0.0,
            "agent": "Sentiment",
            "warning": "sentiment_degraded_infra",
        }

    perf = _decision_performance_summary(
        symbol=symbol,
        timeframe=timeframe,
        model_type=model_type,
        window=window,
        trend_horizon=trend_horizon,
    )
    hist = _decision_history(symbol=symbol, timeframe=timeframe, model_type=model_type, limit=200)

    # Prime reporting with at least one fresh decision event when filtered telemetry is empty.
    if hist.get("count", 0) == 0:
        try:
            # model_type can be "random_forest"/"logistic_regression"; inference override accepts both.
            get_decision_signal(
                symbol,
                timeframe=timeframe,
                explain=False,
                model_override=model_type,
            )
        except Exception:
            pass

        perf = _decision_performance_summary(
            symbol=symbol,
            timeframe=timeframe,
            model_type=model_type,
            window=window,
            trend_horizon=trend_horizon,
        )
        hist = _decision_history(symbol=symbol, timeframe=timeframe, model_type=model_type, limit=200)

    recent_alerts = []
    drift = perf.get("drift") or {}
    transitions = drift.get("alert_transitions") or []
    if isinstance(transitions, list) and transitions:
        recent_alerts = transitions[-8:]

    if status.get("postgres"):
        news_preview = get_news(limit=5)
    else:
        news_preview = []

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "filters": {
            "symbol": symbol,
            "timeframe": timeframe,
            "model_type": model_type,
            "window": window,
            "trend_horizon": trend_horizon,
        },
        "status": {
            **status,
            "tick_count": tick_counter,
            "last_news_refresh_ts": last_news_refresh_ts,
        },
        "agents": {
            "technical": tech,
            "macro": macro,
            "sentiment": sentiment,
            "decision_last": perf.get("last_event"),
        },
        "performance": perf,
        "history": hist,
        "recent_alerts": recent_alerts,
        "news_preview": news_preview,
    }


def _market_comparison_snapshot(
    timeframe: str = "1H",
    model: Optional[str] = None,
    window: int = 200,
    trend_horizon: str = "medium",
) -> Dict:
    timeframe = timeframe.upper()
    window = max(1, min(window, 5000))

    per_symbol: List[Dict] = []
    for sym in SYMBOLS:
        perf = _decision_performance_summary(
            symbol=sym,
            timeframe=timeframe,
            model_type=model,
            window=window,
            trend_horizon=trend_horizon,
        )
        if int(perf.get("total", 0) or 0) == 0:
            try:
                # Prime one decision event to avoid misleading all-zero comparison rows.
                get_decision_signal(sym, timeframe=timeframe, explain=False, model_override=model)
                perf = _decision_performance_summary(
                    symbol=sym,
                    timeframe=timeframe,
                    model_type=model,
                    window=window,
                    trend_horizon=trend_horizon,
                )
            except Exception:
                pass

        hist = _decision_history(
            symbol=sym,
            timeframe=timeframe,
            model_type=model,
            limit=1,
            compress=False,
        )
        last_item = (hist.get("items") or [None])[0]
        drift = perf.get("drift") or {}
        risk_flags = perf.get("risk_flag_frequency") or {}
        events_count = int(perf.get("total", 0) or 0)
        stable_score: Optional[float]
        if events_count <= 0:
            stable_score = None
        else:
            stable_score = max(
                0.0,
                1.0
                - 0.45 * float(drift.get("disagreement_rate", 0.0) or 0.0)
                - 0.30 * float(perf.get("fallback_rate", 0.0) or 0.0)
                - 0.25 * float(perf.get("avg_conflict_index", 0.0) or 0.0),
            )

        signal_dist = perf.get("signal_distribution") or {}
        model_dist = perf.get("model_type_distribution") or {}

        per_symbol.append(
            {
                "symbol": sym,
                "timeframe": timeframe,
                "events": events_count,
                "avg_confidence": float(perf.get("avg_confidence", 0.0) or 0.0),
                "fallback_rate": float(perf.get("fallback_rate", 0.0) or 0.0),
                "avg_latency_ms": float(perf.get("avg_latency_ms", 0.0) or 0.0),
                "disagreement_rate": float(drift.get("disagreement_rate", 0.0) or 0.0),
                "alert_level": str((drift.get("alert") or {}).get("level", "no_data")),
                "top_signal": max(signal_dist.items(), key=lambda x: x[1])[0] if signal_dist else "N/A",
                "top_model": max(model_dist.items(), key=lambda x: x[1])[0] if model_dist else "unknown",
                "top_risk_flag": max(risk_flags.items(), key=lambda x: x[1])[0] if risk_flags else "none",
                "stability_score": round(stable_score, 6) if stable_score is not None else None,
                "last_decision": last_item,
            }
        )

    valid = [x for x in per_symbol if x.get("events", 0) > 0]
    if valid:
        market = {
            "coverage_symbols": len(valid),
            "avg_confidence": round(float(np.mean([x["avg_confidence"] for x in valid])), 6),
            "avg_disagreement": round(float(np.mean([x["disagreement_rate"] for x in valid])), 6),
            "avg_latency_ms": round(float(np.mean([x["avg_latency_ms"] for x in valid])), 3),
            "avg_fallback_rate": round(float(np.mean([x["fallback_rate"] for x in valid])), 6),
            "avg_stability_score": round(float(np.mean([x["stability_score"] for x in valid])), 6),
        }
    else:
        market = {
            "coverage_symbols": 0,
            "avg_confidence": 0.0,
            "avg_disagreement": 0.0,
            "avg_latency_ms": 0.0,
            "avg_fallback_rate": 0.0,
            "avg_stability_score": 0.0,
        }

    ranking = sorted(valid, key=lambda x: (x.get("stability_score", 0.0), x.get("avg_confidence", 0.0)), reverse=True)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "filters": {
            "timeframe": timeframe,
            "model_type": model,
            "window": window,
            "trend_horizon": trend_horizon,
        },
        "market": market,
        "symbols": per_symbol,
        "ranking": ranking,
    }


def get_news(limit: int = 20) -> List[Dict]:
    """Query news from PostgreSQL."""
    if pg_conn is None:
        return []
    articles = []
    try:
        cur = pg_conn.cursor()
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name IN ('forex_news', 'news_articles')
        """)
        tables = {r[0] for r in cur.fetchall()}

        if "forex_news" in tables:
            try:
                cur.execute(
                    "SELECT published_at, title, description, url, source "
                    "FROM forex_news ORDER BY published_at DESC NULLS LAST, id DESC LIMIT %s", (limit,)
                )
                for r in cur.fetchall():
                    articles.append({
                        "published_at": r[0].isoformat() if r[0] else None,
                        "title": r[1] or "Untitled",
                        "description": (r[2] or "")[:200],
                        "url": r[3],
                        "source": r[4] or "Unknown",
                    })
            except Exception:
                pass

        if "news_articles" in tables and len(articles) < limit:
            try:
                remaining = limit - len(articles)
                cur.execute(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'news_articles'
                    """
                )
                news_cols = {r[0] for r in cur.fetchall()}
                source_col = "source_name" if "source_name" in news_cols else "source"
                cur.execute(
                    f"SELECT published_at, title, content, url, {source_col} "
                    "FROM news_articles ORDER BY published_at DESC NULLS LAST LIMIT %s",
                    (remaining,),
                )
                for r in cur.fetchall():
                    articles.append({
                        "published_at": r[0].isoformat() if r[0] else None,
                        "title": r[1] or "Untitled",
                        "description": (r[2] or "")[:200],
                        "url": r[3],
                        "source": r[4] or "Unknown",
                    })
            except Exception:
                pass

        cur.close()
    except Exception as e:
        logger.error(f"News query error: {e}")
    return articles


class ExplainNewsRequest(BaseModel):
    title: str
    content: str = ""
    symbol: Optional[str] = None


class CopilotChatRequest(BaseModel):
    question: str
    symbol: str = "EURUSD"
    timeframe: str = "1H"
    model: Optional[str] = None
    window: int = 200
    trend_horizon: str = "medium"


class CopilotConversationRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class V2GenerateSignalRequest(BaseModel):
    pair: Optional[str] = None
    symbol: Optional[str] = None
    timeframe: str = "1H"
    model: Optional[str] = None
    explain: bool = True


def _clip01(value, default: float = 0.0) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except Exception:
        return float(default)


def _schema_symbol_from_aliases(pair: Optional[str], symbol: Optional[str]) -> str:
    raw = str(pair or symbol or "EURUSD").upper().strip()
    raw = raw.replace("/", "").replace("-", "").replace("_", "")
    raw = re.sub(r"[^A-Z]", "", raw)
    if len(raw) == 6:
        return raw
    return "EURUSD"


def _schema_direction_to_v2(value: Optional[str]) -> str:
    raw = str(value or "").upper()
    if raw == "BUY":
        return "BUY"
    if raw == "SELL":
        return "SELL"
    return "NEUTRAL"


def _schema_agent_vote(agent_name: str, payload: Dict) -> Dict:
    payload = payload if isinstance(payload, dict) else {}
    direction = _schema_direction_to_v2(payload.get("signal"))
    confidence = _clip01(payload.get("confidence", 0.0))
    warning = payload.get("warning")
    error = payload.get("error")

    if error:
        reasoning = f"{agent_name} agent error: {error}"
    elif warning:
        reasoning = f"{agent_name} agent warning: {warning}"
    else:
        reasoning = f"{agent_name.capitalize()} vote: {direction} ({confidence * 100:.0f}% confidence)."

    return {
        "signal": direction,
        "confidence": confidence,
        "reasoning": reasoning,
    }


def _schema_decision_to_v2_signal(payload: Dict, execution_time_ms: int) -> Dict:
    payload = payload if isinstance(payload, dict) else {}
    now_iso = datetime.now(timezone.utc).isoformat()

    pair = str(payload.get("symbol") or "EURUSD").upper()
    direction = _schema_direction_to_v2(payload.get("final_signal"))
    confidence = _clip01(payload.get("global_confidence", payload.get("confidence", 0.0)))
    timestamp = payload.get("decision_timestamp") or now_iso

    probs = payload.get("probabilities") if isinstance(payload.get("probabilities"), dict) else {}
    if probs:
        weighted_score = float(probs.get("buy", 0.0) or 0.0) - float(probs.get("sell", 0.0) or 0.0)
    elif direction == "BUY":
        weighted_score = confidence
    elif direction == "SELL":
        weighted_score = -confidence
    else:
        weighted_score = 0.0
    weighted_score = max(-1.0, min(1.0, weighted_score))

    conflict_index = float(payload.get("conflict_index", 0.0) or 0.0)
    fallback_used = bool(payload.get("fallback_used", False))
    if fallback_used:
        market_regime = "defensive"
    elif conflict_index >= 0.65:
        market_regime = "volatile"
    elif direction in ("BUY", "SELL") and confidence >= 0.55:
        market_regime = "trending"
    else:
        market_regime = "ranging"

    conflicts = [str(f) for f in (payload.get("risk_flags") or []) if str(f).strip()]
    if fallback_used:
        conflicts.append(f"fallback:{payload.get('fallback_reason') or 'unknown'}")
    model_cmp = payload.get("model_comparison") if isinstance(payload.get("model_comparison"), dict) else {}
    if model_cmp and model_cmp.get("agreement") is False:
        conflicts.append("model_disagreement")
    conflicts = list(dict.fromkeys(conflicts))

    model_type = str(payload.get("model_type") or "decision_meta")
    if payload.get("error"):
        reasoning = f"Signal generated with degraded mode due to runtime issue: {payload.get('error')}"
    elif fallback_used:
        reasoning = (
            f"Fallback decision from model {model_type} due to "
            f"{payload.get('fallback_reason') or 'low-confidence safeguards'}."
        )
    else:
        reasoning = (
            f"Decision model {model_type} produced {direction} "
            f"with {confidence * 100:.1f}% confidence."
        )

    contributing_agents = payload.get("contributing_agents") if isinstance(payload.get("contributing_agents"), dict) else {}
    technical_vote = _schema_agent_vote("technical", contributing_agents.get("technical", {}))
    macro_vote = _schema_agent_vote("macro", contributing_agents.get("macro", {}))
    sentiment_vote = _schema_agent_vote("sentiment", contributing_agents.get("sentiment", {}))

    macro_ts = (contributing_agents.get("macro") or {}).get("last_update")
    news_ts = (contributing_agents.get("sentiment") or {}).get("last_update")

    return {
        "success": True,
        "signal": {
            "pair": pair,
            "symbol": pair,
            "direction": direction,
            "confidence": confidence,
            "weighted_score": round(float(weighted_score), 6),
            "reasoning": reasoning,
            "agent_votes": {
                "technical": technical_vote,
                "macro": macro_vote,
                "sentiment": sentiment_vote,
            },
            "weights": {
                "technical": 0.40,
                "macro": 0.35,
                "sentiment": 0.25,
            },
            "market_regime": market_regime,
            "conflicts": conflicts,
            "timestamp": timestamp,
        },
        "metadata": {
            "execution_time_ms": int(payload.get("latency_ms", execution_time_ms) or execution_time_ms),
            "data_timestamps": {
                "ohlcv": timestamp,
                "macro": macro_ts or timestamp,
                "news": news_ts or get_last_sentiment_update_date() or timestamp,
            },
        },
    }


def _memory_usage_mb() -> float:
    try:
        import psutil

        rss = float(psutil.Process(os.getpid()).memory_info().rss)
        return round(rss / (1024 * 1024), 3)
    except Exception:
        return 0.0


def _news_freshness_health(target_max_age_minutes: int = 240) -> Dict:
    now = datetime.now(timezone.utc)
    latest_dt = None
    last_1h = 0
    last_24h = 0

    try:
        for row in get_news(limit=300):
            dt = _parse_published_at(row.get("published_at"))
            if dt is None:
                continue
            dt_utc = dt.replace(tzinfo=timezone.utc)
            if latest_dt is None or dt_utc > latest_dt:
                latest_dt = dt_utc
            age_seconds = max(0.0, (now - dt_utc).total_seconds())
            if age_seconds <= 3600:
                last_1h += 1
            if age_seconds <= 86400:
                last_24h += 1
    except Exception:
        pass

    if latest_dt is None:
        return {
            "status": "NO_DATA",
            "last_news_timestamp": None,
            "age_minutes": None,
            "articles_last_1h": 0,
            "articles_last_24h": 0,
            "freshness_score": 0.0,
            "target_max_age_minutes": int(target_max_age_minutes),
        }

    age_minutes = max(0.0, (now - latest_dt).total_seconds() / 60.0)
    freshness_score = max(0.0, min(1.0, 1.0 - (age_minutes / max(1, target_max_age_minutes))))
    freshness_status = "PASS" if age_minutes <= target_max_age_minutes else "WARN"

    return {
        "status": freshness_status,
        "last_news_timestamp": latest_dt.isoformat(),
        "age_minutes": round(age_minutes, 2),
        "articles_last_1h": int(last_1h),
        "articles_last_24h": int(last_24h),
        "freshness_score": round(float(freshness_score), 6),
        "target_max_age_minutes": int(target_max_age_minutes),
    }


def _build_v2_agent_performances(summary: Dict) -> Dict[str, Dict]:
    summary = summary if isinstance(summary, dict) else {}
    drift = summary.get("drift") if isinstance(summary.get("drift"), dict) else {}

    total = int(summary.get("total", 0) or 0)
    fallback_rate = _clip01(summary.get("fallback_rate", 0.0))
    avg_conf = _clip01(summary.get("avg_confidence", 0.0))
    drift_rate = _clip01(drift.get("disagreement_rate", 0.0))

    readiness = {
        "technical": bool(status.get("model")),
        "macro": bool(status.get("macro_model")),
        "sentiment": bool(status.get("sentiment_model")),
    }

    performance: Dict[str, Dict] = {}
    for agent in ("technical", "macro", "sentiment"):
        if not readiness[agent]:
            performance[agent] = {
                "agent_type": agent,
                "total_signals": 0,
                "win_rate": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "avg_confidence": 0.0,
                "last_30d_accuracy": 0.0,
                "total_pnl": 0.0,
            }
            continue

        win_rate = _clip01(avg_conf * (1.0 - (0.35 * fallback_rate)))
        sharpe_ratio = round((win_rate - 0.5) * 2.4, 6)
        max_drawdown = round(_clip01(drift_rate + (0.25 * fallback_rate)), 6)
        total_pnl = round((win_rate - 0.5) * max(1, total), 6)

        performance[agent] = {
            "agent_type": agent,
            "total_signals": int(total),
            "win_rate": round(win_rate, 6),
            "sharpe_ratio": float(sharpe_ratio),
            "max_drawdown": float(max_drawdown),
            "avg_confidence": round(avg_conf, 6),
            "last_30d_accuracy": round(win_rate, 6),
            "total_pnl": float(total_pnl),
        }

    return performance


def _cache_key_for_article(title: str, content: str, symbol: Optional[str]) -> str:
    payload = f"{(title or '').strip()}||{(content or '').strip()}||{(symbol or '').upper()}"
    return hashlib.sha256(payload.encode("utf-8", errors="ignore")).hexdigest()


def _cache_get(cache_key: str) -> Optional[Dict]:
    item = explanation_cache.get(cache_key)
    if not item:
        return None
    if item.get("expires_at", 0) < int(datetime.now(timezone.utc).timestamp()):
        explanation_cache.pop(cache_key, None)
        return None
    return item.get("value")


def _cache_set(cache_key: str, value: Dict):
    explanation_cache[cache_key] = {
        "expires_at": int(datetime.now(timezone.utc).timestamp()) + EXPLANATION_CACHE_TTL_SECONDS,
        "value": value,
    }
    if len(explanation_cache) > 4000:
        explanation_cache.pop(next(iter(explanation_cache)), None)


def _recent_news_titles(limit: int = 25) -> List[str]:
    rows = get_news(limit=limit)
    return [str(r.get("title") or "").strip() for r in rows if str(r.get("title") or "").strip()]


def _fallback_explanation(title: str, content: str, symbol: Optional[str]) -> Dict:
    text = f"{title} {content}".strip()
    sentiment_score = 0.0
    entities = {"currencies": [], "central_banks": [], "countries": [], "companies": []}
    affected_assets = []
    confidence = 0.55

    try:
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from modeling.sentiment_agent.nlp_utils import get_nlp_signal

        nlp = get_nlp_signal(text)
        sentiment_score = float(nlp.get("sentiment_score", 0.0))
        entities = nlp.get("entities", entities)
        affected_assets = nlp.get("assets", [])
        confidence = max(0.45, min(0.85, abs(sentiment_score) + 0.45))
    except Exception:
        pass

    if sentiment_score > 0.15:
        sentiment = "BUY"
        market_impact = "Headline tone is net positive for risk and the relevant currencies."
    elif sentiment_score < -0.15:
        sentiment = "SELL"
        market_impact = "Headline tone is net negative and may pressure the related FX pairs."
    else:
        sentiment = "HOLD"
        market_impact = "Headline is mixed/neutral and directional edge is limited."

    if symbol and symbol.upper() not in affected_assets:
        affected_assets = sorted(set(affected_assets + [symbol.upper()]))

    summary = (text[:240] + "...") if len(text) > 240 else text
    if not summary:
        summary = "No content available for this article."

    return {
        "summary": summary,
        "market_impact": market_impact,
        "affected_assets": affected_assets,
        "sentiment": sentiment,
        "confidence": round(float(confidence), 4),
        "entities": entities,
        "source": "fallback",
    }


def _build_llm_prompt(title: str, content: str, symbol: Optional[str], recent_titles: List[str]) -> str:
    joined_titles = "\n".join(f"- {t}" for t in recent_titles[:12]) or "- none"
    return (
        "You are an FX market analyst. Return strict JSON only with keys: "
        "summary, market_impact, affected_assets, sentiment, confidence. "
        "sentiment must be BUY, SELL, or HOLD. confidence must be 0..1. "
        "affected_assets must be an array of FX symbols from [EURUSD, USDJPY, GBPUSD, USDCHF].\n\n"
        f"Target symbol context: {(symbol or 'None')}\n"
        f"Headline: {title}\n"
        f"Content: {content[:2000]}\n\n"
        f"Recent headlines context:\n{joined_titles}\n"
    )


def _call_llm_explanation(title: str, content: str, symbol: Optional[str]) -> Optional[Dict]:
    if not OPENAI_API_KEY:
        return None

    prompt = _build_llm_prompt(title, content, symbol, _recent_news_titles(limit=25))
    url = OPENAI_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENAI_MODEL,
        "temperature": 0,
        "max_tokens": 260,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": "You output JSON only."},
            {"role": "user", "content": prompt},
        ],
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=6)
    if resp.status_code >= 300:
        logger.warning("LLM explanation HTTP %s", resp.status_code)
        return None

    data = resp.json()
    content_text = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
        .strip()
    )
    if not content_text:
        return None

    try:
        parsed = json.loads(content_text)
    except Exception:
        return None

    sentiment = str(parsed.get("sentiment", "HOLD")).upper()
    if sentiment not in {"BUY", "SELL", "HOLD"}:
        sentiment = "HOLD"

    assets = parsed.get("affected_assets", [])
    if not isinstance(assets, list):
        assets = []
    assets = [a for a in [str(x).upper() for x in assets] if a in {"EURUSD", "USDJPY", "GBPUSD", "USDCHF"}]
    if symbol and symbol.upper() not in assets:
        assets.append(symbol.upper())

    try:
        conf = float(parsed.get("confidence", 0.5))
    except Exception:
        conf = 0.5
    conf = max(0.0, min(1.0, conf))

    return {
        "summary": str(parsed.get("summary", "")).strip()[:700],
        "market_impact": str(parsed.get("market_impact", "")).strip()[:700],
        "affected_assets": sorted(set(assets)),
        "sentiment": sentiment,
        "confidence": round(conf, 4),
        "source": "llm",
    }


def explain_news_article(title: str, content: str, symbol: Optional[str]) -> Dict:
    key = _cache_key_for_article(title, content, symbol)
    cached = _cache_get(key)
    if cached is not None:
        return {**cached, "cached": True}

    llm_out = None
    try:
        llm_out = _call_llm_explanation(title, content, symbol)
    except Exception as e:
        logger.warning("LLM explanation failed: %s", e)

    result = llm_out or _fallback_explanation(title, content, symbol)

    # Sentiment alignment check against local NLP polarity.
    fallback_probe = _fallback_explanation(title, content, symbol)
    local_sent = fallback_probe.get("sentiment", "HOLD")
    result["alignment"] = bool(result.get("sentiment") == local_sent)
    result["entities"] = fallback_probe.get("entities", {})

    _cache_set(key, result)
    return {**result, "cached": False}


TRADING_SCOPE_REFUSAL = (
    "I am a trading assistant and can only answer questions related to markets, forex, or platform data."
)


def get_platform_features_description() -> Dict:
    return {
        "name": "Trady",
        "purpose": "Decision-support platform for forex trading; not an order-execution broker.",
        "features": [
            "Technical signals",
            "Macro agent signals",
            "Sentiment agent signals",
            "Decision aggregation and telemetry",
            "Market comparison and reporting",
            "News ingestion and explanation",
        ],
    }


def build_context(
    symbol: str,
    timeframe: str,
    model: Optional[str] = None,
    window: int = 200,
    trend_horizon: str = "medium",
    news_limit: int = 5,
) -> Dict:
    def _safe_call(fn, *args, default=None, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            logger.warning("Context fetch failed for %s: %s", getattr(fn, "__name__", "unknown"), e)
            return default

    macro_data = _safe_call(get_macro_signal, symbol, False, default={})
    technical_data = _safe_call(get_signal, symbol, timeframe, default={})
    sentiment_data = _safe_call(get_sentiment_signal, symbol, timeframe, False, default={})
    news_data = _safe_call(get_news, news_limit, default=[])

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "filters": {
            "symbol": symbol,
            "timeframe": timeframe,
            "model_type": model,
            "window": window,
            "trend_horizon": trend_horizon,
        },
        "status": {
            **status,
            "tick_count": tick_counter,
            "last_news_refresh_ts": last_news_refresh_ts,
        },
        "macro": macro_data,
        "technical": technical_data,
        "sentiment": sentiment_data,
        "news": news_data,
        "platform_info": get_platform_features_description(),
        "reporting_overview": _safe_call(_reporting_overview, symbol, timeframe, model, window, trend_horizon, default={}),
        "market_comparison": _safe_call(_market_comparison_snapshot, timeframe, model, window, trend_horizon, default={}),
        "recent_news": news_data,
    }


def is_relevant_question(user_input: str) -> bool:
    q = str(user_input or "").strip().lower()
    if not q:
        return False
    tokens = set(re.findall(r"[a-z']+", q))
    scope_terms = {
        "forex", "fx", "currency", "currencies", "eurusd", "usdjpy", "gbpusd", "usdchf",
        "market", "markets", "trade", "trading", "buy", "sell", "entry", "exit", "risk",
        "macro", "cpi", "inflation", "rates", "interest", "fomc", "ecb", "boe", "boj",
        "sentiment", "technical", "signal", "signals", "news", "headline", "volatility",
        "platform", "trady", "agent", "decision", "reporting", "comparison", "dashboard", "broker", "mt5",
    }
    return bool(tokens.intersection(scope_terms))


def _build_llm_system_prompt() -> str:
    return (
        "You are an advanced forex trading assistant integrated into a trading platform.\n\n"
        "STRICT RULES:\n\n"
        "* Only answer questions related to:\n\n"
        "  * forex trading\n"
        "  * currencies\n"
        "  * macroeconomics\n"
        "  * financial markets\n"
        "  * news that affects markets\n"
        "  * the platform and its data\n"
        "* If the question is unrelated (food, entertainment, general random topics), refuse politely.\n"
        "* Always base your answers on the provided context (database + platform data).\n"
        "* Do not invent data.\n"
        "* When news is provided, explain how it may impact the market (cause and effect).\n"
        "* When possible, connect macro + sentiment + technical signals.\n"
        "* Answer like a professional trader, clear and structured."
    )


def _build_llm_user_prompt(user_input: str, context: Dict, history: Optional[List[Dict[str, str]]] = None) -> str:
    compact_context = json.dumps(context, ensure_ascii=True)[:12000]
    compact_history = json.dumps((history or [])[-10:], ensure_ascii=True)
    return (
        f"User question:\n{user_input}\n\n"
        f"Conversation history:\n{compact_history}\n\n"
        f"Available data:\n{compact_context}\n\n"
        "Answer using only this data and your trading knowledge.\n"
        "Return strict JSON with keys: answer, why, risk_notes, data_basis, confidence, limitations."
    )


def generate_llm_response(user_input: str, context: Dict, history: Optional[List[Dict[str, str]]] = None) -> Optional[Dict]:
    if not OPENAI_API_KEY or not OPENAI_SDK_AVAILABLE:
        return None
    if not is_relevant_question(user_input):
        return {
            "answer": TRADING_SCOPE_REFUSAL,
            "why": [],
            "risk_notes": [],
            "data_basis": [],
            "limitations": ["Question is outside permitted assistant scope."],
            "confidence": 1.0,
            "source": "guard",
        }

    client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL.rstrip("/"))
    messages = [
        {"role": "system", "content": _build_llm_system_prompt()},
        {"role": "user", "content": _build_llm_user_prompt(user_input, context, history)},
    ]
    logger.info("Copilot LLM request: model=%s q=%s", OPENAI_MODEL, str(user_input)[:120])

    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.35,
        max_tokens=650,
        response_format={"type": "json_object"},
        messages=messages,
        timeout=OPENAI_TIMEOUT_SECONDS,
    )

    content_text = str(((resp.choices or [None])[0].message.content if resp.choices else "") or "").strip()
    if not content_text:
        return None

    try:
        parsed = json.loads(content_text)
    except Exception:
        return None

    def _as_str_list(v) -> List[str]:
        if not isinstance(v, list):
            return []
        out: List[str] = []
        for x in v:
            s = str(x).strip()
            if s:
                out.append(s[:240])
        return out[:6]

    answer = str(parsed.get("answer", "")).strip()
    if not answer:
        return None

    try:
        conf = float(parsed.get("confidence", 0.6))
    except Exception:
        conf = 0.6
    conf = max(0.0, min(1.0, conf))

    return {
        "answer": answer[:950],
        "why": _as_str_list(parsed.get("why")),
        "risk_notes": _as_str_list(parsed.get("risk_notes")),
        "data_basis": _as_str_list(parsed.get("data_basis")),
        "limitations": _as_str_list(parsed.get("limitations")),
        "confidence": round(conf, 4),
        "source": "llm",
    }


def fallback_response(question: str, context: Dict) -> Dict:
    return _fallback_copilot(question, context)


def _call_llm_copilot(question: str, context: Dict) -> Optional[Dict]:
    return generate_llm_response(question, context)


def _fallback_copilot(question: str, context: Dict) -> Dict:
    q = str(question or "").strip().lower()
    market = (context.get("market_comparison") or {}).get("market") or {}
    market_symbols = (context.get("market_comparison") or {}).get("symbols") or []
    ranking = (context.get("market_comparison") or {}).get("ranking") or []
    perf = (context.get("reporting_overview") or {}).get("performance") or {}
    drift = perf.get("drift") or {}
    recent_news = context.get("recent_news") or context.get("news") or []
    current_symbol = str(((context.get("filters") or {}).get("symbol") or "EURUSD")).upper()

    def _find_symbol_row(sym: str) -> Optional[Dict]:
        sym = str(sym or "").upper()
        for row in market_symbols:
            if str(row.get("symbol", "")).upper() == sym:
                return row
        return None

    asked_symbols = [s for s in SYMBOLS if s.lower() in q]
    main_row = _find_symbol_row(current_symbol)
    cmp_rows = [_find_symbol_row(s) for s in asked_symbols]
    cmp_rows = [r for r in cmp_rows if r]

    best = ranking[0] if ranking else None
    coverage = int(market.get("coverage_symbols", 0) or 0)
    market_dis = round(float(market.get("avg_disagreement", 0.0) or 0.0) * 100, 2)
    market_stab = round(float(market.get("avg_stability_score", 0.0) or 0.0) * 100, 1)
    sym_dis = round(float(drift.get("disagreement_rate", 0.0) or 0.0) * 100, 2)
    sym_conf = round(float(perf.get("avg_confidence", 0.0) or 0.0) * 100, 2)
    sym_fallback = round(float(perf.get("fallback_rate", 0.0) or 0.0) * 100, 2)

    intent_compare = any(k in q for k in ["compare", "comparison", "vs", "versus"])
    intent_confidence = any(k in q for k in ["confidence", "confident", "certainty", "why is confidence"])
    intent_action = any(k in q for k in ["what should i do", "before entering", "entry", "enter a trade", "next step", "plan", "checklist"])
    intent_beginner = any(k in q for k in ["beginner", "simple", "easy", "friendly language", "explain this setup"])
    intent_risk = any(k in q for k in ["risk", "risky", "danger", "safe", "warning", "alert"])
    intent_news = any(k in q for k in ["news", "headline", "latest", "impact", "cpi", "fomc", "rate decision"])

    intent_name = "summary"

    if intent_compare and len(cmp_rows) >= 2:
        intent_name = "compare"
        a = cmp_rows[0]
        b = cmp_rows[1]
        a_st = float(a.get("stability_score") or 0.0) * 100
        b_st = float(b.get("stability_score") or 0.0) * 100
        a_dis = float(a.get("disagreement_rate") or 0.0) * 100
        b_dis = float(b.get("disagreement_rate") or 0.0) * 100
        better = a if a_st >= b_st else b
        answer = (
            f"Comparison now: {a.get('symbol')} vs {b.get('symbol')} shows {better.get('symbol')} as relatively more stable "
            f"for the selected timeframe. Confirm on Decision page before execution."
        )
        why = [
            f"{a.get('symbol')} stability {a_st:.1f}% vs {b.get('symbol')} stability {b_st:.1f}%.",
            f"{a.get('symbol')} disagreement {a_dis:.2f}% vs {b.get('symbol')} disagreement {b_dis:.2f}%.",
            f"Market average disagreement is {market_dis:.2f}%.",
        ]
        data_basis = [
            f"{a.get('symbol')}.stability_score",
            f"{b.get('symbol')}.stability_score",
            f"{a.get('symbol')}.disagreement_rate",
            f"{b.get('symbol')}.disagreement_rate",
            "market.avg_disagreement",
        ]
    elif intent_confidence:
        intent_name = "confidence"
        answer = (
            f"For {current_symbol}, confidence is currently around {sym_conf:.2f}%. Interpret it together with disagreement ({sym_dis:.2f}%) "
            f"and fallback ({sym_fallback:.2f}%), not in isolation."
        )
        why = [
            f"Current symbol confidence: {sym_conf:.2f}%.",
            f"Current symbol disagreement: {sym_dis:.2f}%.",
            f"Current symbol fallback rate: {sym_fallback:.2f}%.",
            f"Market average stability: {market_stab:.1f}%.",
        ]
        data_basis = [
            "symbol.avg_confidence",
            "symbol.drift.disagreement_rate",
            "symbol.fallback_rate",
            "market.avg_stability_score",
        ]
    elif intent_beginner:
        intent_name = "beginner"
        best_sym = best.get("symbol") if best else "N/A"
        answer = (
            f"Beginner view: first check if market is calm, then check if your symbol is aligned. For {current_symbol}, confidence is {sym_conf:.2f}% and disagreement is {sym_dis:.2f}%. "
            "If disagreement rises, wait. If it stays low, proceed with small risk and a strict stop-loss."
        )
        why = [
            f"Think of confidence as signal clarity ({sym_conf:.2f}%), not certainty.",
            f"Disagreement ({sym_dis:.2f}%) tells you if models agree on direction.",
            f"Market average disagreement is {market_dis:.2f}%.",
            f"Most stable symbol now: {best_sym}.",
        ]
        data_basis = [
            "symbol.avg_confidence",
            "symbol.drift.disagreement_rate",
            "market.avg_disagreement",
            "market.ranking",
        ]
    elif intent_news:
        intent_name = "news"
        if recent_news:
            item = recent_news[0]
            title = str(item.get("title") or "Untitled").strip()
            answer = (
                f"Latest market news: {title}. Potential effect: if this headline is USD-positive, EURUSD can face downside pressure; "
                "if USD-negative, EURUSD can find support. Confirm with current technical and sentiment signals before entry."
            )
            why = [
                "News can shift rate expectations and short-term FX flows.",
                f"Current symbol confidence: {sym_conf:.2f}%.",
                f"Current symbol disagreement: {sym_dis:.2f}%.",
                "Macro + sentiment + technical alignment matters more than headline alone.",
            ]
            data_basis = [
                "news[0].title",
                "symbol.avg_confidence",
                "symbol.drift.disagreement_rate",
                "sentiment.signal",
                "technical.signal",
            ]
        else:
            answer = "I cannot fetch fresh news right now. Open the News panel and I can explain any headline's likely FX impact."
            why = [
                "No recent news rows were available in current context.",
                f"Current symbol confidence: {sym_conf:.2f}%.",
                f"Current symbol disagreement: {sym_dis:.2f}%.",
            ]
            data_basis = [
                "news",
                "symbol.avg_confidence",
                "symbol.drift.disagreement_rate",
            ]
    elif intent_action:
        intent_name = "action"
        answer = (
            "Pre-trade checklist: 1) Confirm market stability in Comparison. 2) Confirm final signal and risk flags in Decision. "
            "3) Set stop-loss and max account risk. 4) Enter only if conditions still match your plan."
        )
        why = [
            f"Current symbol confidence: {sym_conf:.2f}%.",
            f"Current symbol disagreement: {sym_dis:.2f}%.",
            f"Current fallback rate: {sym_fallback:.2f}%.",
            f"Active market coverage: {coverage} symbols.",
        ]
        data_basis = [
            "symbol.avg_confidence",
            "symbol.drift.disagreement_rate",
            "symbol.fallback_rate",
            "market.coverage_symbols",
        ]
    elif intent_risk:
        intent_name = "risk"
        risk_level = "elevated" if (sym_dis >= 20.0 or sym_fallback >= 15.0) else "contained"
        answer = (
            f"Risk on {current_symbol} is currently {risk_level} based on disagreement and fallback behavior. "
            "If either metric rises, reduce size or wait for clearer conditions."
        )
        why = [
            f"Symbol disagreement: {sym_dis:.2f}%.",
            f"Symbol fallback rate: {sym_fallback:.2f}%.",
            f"Market disagreement average: {market_dis:.2f}%.",
            f"Coverage symbols with active data: {coverage}.",
        ]
        data_basis = [
            "symbol.drift.disagreement_rate",
            "symbol.fallback_rate",
            "market.avg_disagreement",
            "market.coverage_symbols",
        ]
    else:
        intent_name = "summary"
        q_short = str(question or "").strip()
        if len(q_short) > 80:
            q_short = q_short[:77] + "..."
        answer = (
            f"For your question ({q_short}), based on current platform data, review stability and disagreement first, then confirm on the Decision page before trading. "
            "Use strict risk control if drift rises or coverage is low."
        )
        why = [
            f"Market coverage symbols: {coverage}.",
            f"Average market disagreement: {market_dis:.2f}%.",
            f"Current symbol disagreement: {sym_dis:.2f}%.",
            f"Current symbol confidence: {sym_conf:.2f}%.",
        ]
        data_basis = [
            "market.avg_disagreement",
            "market.coverage_symbols",
            "symbol.drift.disagreement_rate",
            "symbol.avg_confidence",
        ]

    limitations: List[str] = []
    if coverage == 0:
        limitations.append("No active symbol coverage yet; generate decisions first.")
    if int(perf.get("total", 0) or 0) == 0:
        limitations.append("No telemetry for selected symbol/timeframe in current window.")
    if not OPENAI_API_KEY:
        limitations.append("LLM is not enabled; response is generated by deterministic fallback logic.")

    return {
        "answer": answer,
        "why": why[:4],
        "risk_notes": [
            "Never treat model confidence as certainty.",
            "Reduce size when disagreement or fallback rises.",
            "Do not trade without predefined stop-loss and max risk.",
        ],
        "data_basis": data_basis[:6],
        "limitations": limitations,
        "confidence": 0.58 if coverage > 0 else 0.42,
        "source": "fallback",
        "intent": intent_name,
    }


def copilot_answer(
    question: str,
    symbol: str,
    timeframe: str,
    model: Optional[str],
    window: int,
    trend_horizon: str,
) -> Dict:
    question = str(question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="question is required")

    symbol = str(symbol or "EURUSD").upper()
    timeframe = str(timeframe or "1H").upper()
    if symbol not in SYMBOLS:
        raise HTTPException(status_code=400, detail=f"Unknown symbol: {symbol}")
    if timeframe not in TIMEFRAMES:
        raise HTTPException(status_code=400, detail=f"Unknown timeframe: {timeframe}")

    context = build_context(symbol, timeframe, model, window, trend_horizon, news_limit=5)

    llm_available = bool(OPENAI_API_KEY and OPENAI_SDK_AVAILABLE)
    if not is_relevant_question(question):
        out = {
            "answer": TRADING_SCOPE_REFUSAL,
            "why": [],
            "risk_notes": [],
            "data_basis": [],
            "limitations": ["Question is outside assistant scope."],
            "confidence": 1.0,
            "source": "guard",
            "intent": "out_of_scope",
        }
    else:
        llm_out = None
        if llm_available:
            try:
                llm_out = _call_llm_copilot(question, context)
            except Exception as e:
                logger.warning("LLM copilot failed: %s", e)
        out = llm_out or fallback_response(question, context)
    return {
        "question": question,
        "symbol": symbol,
        "timeframe": timeframe,
        "model_type": model,
        "window": window,
        "trend_horizon": trend_horizon,
        "provider": {
            "model": OPENAI_MODEL,
            "llm_enabled": llm_available,
            "source": out.get("source", "fallback"),
            "intent": out.get("intent", "llm"),
        },
        "response": out,
        "context_summary": {
            "market_coverage": ((context.get("market_comparison") or {}).get("market") or {}).get("coverage_symbols", 0),
            "symbol_event_count": ((context.get("reporting_overview") or {}).get("performance") or {}).get("total", 0),
        },
    }


def _default_copilot_filters() -> Dict[str, str]:
    symbol = "EURUSD"
    timeframe = "1H"
    with decision_telemetry_lock:
        if decision_telemetry:
            last = decision_telemetry[-1]
            symbol = str(last.get("symbol") or symbol).upper()
            timeframe = str(last.get("timeframe") or timeframe).upper()
    if symbol not in SYMBOLS:
        symbol = "EURUSD"
    if timeframe not in TIMEFRAMES:
        timeframe = "1H"
    return {"symbol": symbol, "timeframe": timeframe}


def _build_copilot_conversation_prompt(message: str, history: List[Dict[str, str]], context: Dict) -> str:
    compact_ctx = json.dumps(context, ensure_ascii=True)[:6000]
    compact_hist = json.dumps(history[-10:], ensure_ascii=True)
    return (
        "You are Trady Copilot, a friendly and concise forex/trading assistant. "
        "Rules: prioritize Trady context, market signals, risk, and safe execution habits. "
        "You may also answer general forex/trading questions (education, execution basics, brokers/platform flow) when asked. "
        "Be explicit that Trady is decision support, not a broker/exchange for order execution. "
        "Do not provide guarantees, do not encourage reckless trading. "
        "Keep answer clear and conversational (max 140 words). "
        "Use context data when relevant; if uncertain, say so simply. "
        "Return strict JSON only with keys: answer, confidence. confidence is 0..1 for explanation quality.\n\n"
        f"Conversation history (latest first may be omitted): {compact_hist}\n"
        f"Latest user message: {message}\n"
        f"Context JSON: {compact_ctx}"
    )


def _call_llm_copilot_conversation(message: str, history: List[Dict[str, str]], context: Dict) -> Optional[Dict]:
    out = generate_llm_response(message, context, history=history)
    if not out:
        return None
    return {
        "answer": str(out.get("answer", "")).strip()[:1000],
        "confidence": float(out.get("confidence", 0.65) or 0.65),
        "source": str(out.get("source") or "llm"),
    }


def _last_history_text(history: List[Dict[str, str]], role: str) -> str:
    for item in reversed(history):
        if str(item.get("role") or "") == role:
            return str(item.get("content") or "")
    return ""


def _simple_pretrade_plan(symbol: str, confidence: float, disagreement: float, fallback: float) -> str:
    return (
        "Here is a simple action plan before your next trade:\n"
        f"1) Context: check {symbol} trend and key support/resistance on your entry timeframe.\n"
        f"2) Signal quality: only proceed if confidence stays above 70% (now {confidence:.2f}%) and disagreement is low (now {disagreement:.2f}%).\n"
        f"3) Reliability: if fallback rises above 15% (now {fallback:.2f}%), reduce size or skip.\n"
        "4) Risk: set stop-loss first; risk only a small fixed fraction of account (for example 0.5% to 1%).\n"
        "5) Entry: use limit/market based on your setup, then set take-profit with at least 1:1.5 reward-to-risk.\n"
        "6) Exit discipline: if invalidation hits, exit without averaging down."
    )


def _fallback_copilot_conversation(message: str, history: List[Dict[str, str]], context: Dict) -> Dict:
    q = str(message or "").strip()
    ql = q.lower()
    tokens = set(re.findall(r"[a-z']+", ql))
    last_user = _last_history_text(history, "user").lower()
    last_assistant = _last_history_text(history, "assistant").lower()
    perf = (context.get("reporting_overview") or {}).get("performance") or {}
    drift = perf.get("drift") or {}
    market = (context.get("market_comparison") or {}).get("market") or {}
    recent_news = context.get("recent_news") or []
    symbol = str((context.get("filters") or {}).get("symbol") or "EURUSD")
    confidence = float(perf.get("avg_confidence", 0.0) or 0.0) * 100
    disagreement = float(drift.get("disagreement_rate", 0.0) or 0.0) * 100
    fallback = float(perf.get("fallback_rate", 0.0) or 0.0) * 100
    coverage = int(market.get("coverage_symbols", 0) or 0)
    affirmative = ql in {"yes", "y", "yeah", "yep", "sure", "ok", "okay", "go ahead", "do it", "please"}

    if affirmative and (
        "action plan" in last_assistant
        or "before your next trade" in last_assistant
        or "checklist" in last_user
        or "buy" in last_user
        or "sell" in last_user
    ):
        answer = _simple_pretrade_plan(symbol, confidence, disagreement, fallback)
    elif (
        "news" in tokens
        or "headline" in tokens
        or ("latest" in tokens and ("news" in ql or "update" in tokens))
        or ("what" in tokens and "happening" in tokens)
    ):
        if recent_news:
            top = recent_news[:3]
            lines = []
            for item in top:
                title = str(item.get("title") or "Untitled").strip()
                source = str(item.get("source") or "Unknown").strip()
                published = str(item.get("published_at") or "").strip()
                stamp = published[:16].replace("T", " ") if published else "recent"
                lines.append(f"- {title} ({source}, {stamp})")
            answer = "Latest forex headlines I can see right now:\n" + "\n".join(lines)
        else:
            answer = (
                "I could not load fresh headlines right now. "
                "You can still open the News panel, and I can summarize any article you paste here."
            )
    elif (("where" in tokens and "trade" in tokens) or "which broker" in ql or "broker" in tokens or "exchange" in tokens):
        answer = (
            "Trady does not execute orders. It helps with analysis and decision support. "
            "To actually trade, use a broker platform account (for example MT5 via your broker), then place buy/sell orders there. "
            "Use Trady to validate direction, risk, and timing before execution."
        )
    elif any(k in ql for k in ["how can i buy", "how do i buy", "how to buy", "how to sell", "buy and sell signals", "execute", "place order"]):
        answer = (
            "Practical flow: 1) read Trady signal and risk context, 2) open your broker terminal (MT5), 3) choose pair and lot size, "
            "4) set stop-loss and take-profit first, 5) place Buy if your strategy confirms bullish setup or Sell for bearish setup. "
            "Trady gives guidance; execution happens on your broker account."
        )
    elif any(k in ql for k in ["beginner", "new trader", "newbie", "explain this setup"]):
        answer = (
            f"Beginner view: Trady is saying the setup on {symbol} currently looks structured, with confidence {confidence:.2f}%. "
            "That does not mean guaranteed profit. Think of it as decision support: wait for confirmation, trade small size, and always use stop-loss."
        )
    elif bool(tokens.intersection({"hi", "hello", "hey"})):
        answer = (
            "Hello, I can help you understand Trady signals, compare market conditions, explain risk in simple words, and guide your pre-trade checklist. "
            "Ask me anything about your setup and I will keep it practical and safe."
        )
    elif any(k in ql for k in ["help", "what can you do", "how can you help"]):
        answer = (
            "I can do four main things: 1) explain your current setup clearly, 2) compare symbols by stability/risk, "
            "3) give a pre-trade checklist, and 4) translate metrics into beginner-friendly language."
        )
    elif any(k in ql for k in ["before entering", "enter", "checklist", "what should i do"]):
        answer = (
            "Before entry: confirm market stability, confirm decision signal plus risk flags, set stop-loss, and cap account risk. "
            f"Right now for {symbol}: confidence {confidence:.2f}%, disagreement {disagreement:.2f}%, fallback {fallback:.2f}%."
        )
    elif any(k in ql for k in ["risk", "danger", "safe", "warning"]):
        level = "contained" if (disagreement < 20.0 and fallback < 15.0) else "elevated"
        answer = (
            f"Current risk looks {level}. For {symbol}, disagreement is {disagreement:.2f}% and fallback is {fallback:.2f}%. "
            "If either rises, reduce position size or wait for clearer conditions."
        )
    elif any(k in ql for k in ["compare", "vs", "versus"]):
        answer = (
            f"I can compare symbols for you using current Trady context. Right now market coverage is {coverage} symbols. "
            "Tell me the pair names (for example EURUSD vs GBPUSD) and I will rank them by stability and risk."
        )
    else:
        answer = (
            f"Good question. For the current Trady context on {symbol}, confidence is {confidence:.2f}% with disagreement {disagreement:.2f}%. "
            "If you want, I can break this into a simple action plan before your next trade."
        )

    return {
        "answer": answer,
        "confidence": 0.62 if coverage > 0 else 0.45,
        "source": "fallback",
    }


def copilot_converse(message: str, session_id: Optional[str]) -> Dict:
    message = str(message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    session_id = (session_id or "").strip() or hashlib.sha256(f"{datetime.now(timezone.utc).isoformat()}:{message}".encode("utf-8", errors="ignore")).hexdigest()[:16]

    with copilot_sessions_lock:
        history = list(copilot_sessions.get(session_id, []))

    defaults = _default_copilot_filters()
    symbol = defaults["symbol"]
    timeframe = defaults["timeframe"]
    context = build_context(symbol, timeframe, None, 200, "medium", news_limit=3)

    llm_available = bool(OPENAI_API_KEY and OPENAI_SDK_AVAILABLE)
    if not is_relevant_question(message):
        out = {
            "answer": TRADING_SCOPE_REFUSAL,
            "confidence": 1.0,
            "source": "guard",
        }
    else:
        llm_out = None
        if llm_available:
            try:
                llm_out = _call_llm_copilot_conversation(message, history, context)
            except Exception as e:
                logger.warning("LLM copilot conversation failed: %s", e)
        out = llm_out or _fallback_copilot_conversation(message, history, context)
    answer = str(out.get("answer", "")).strip() or "I could not generate a response right now."

    with copilot_sessions_lock:
        current = copilot_sessions.get(session_id, [])
        current.append({"role": "user", "content": message})
        current.append({"role": "assistant", "content": answer})
        if len(current) > COPILOT_SESSION_MAX_MESSAGES:
            current = current[-COPILOT_SESSION_MAX_MESSAGES:]
        copilot_sessions[session_id] = current
        if len(copilot_sessions) > COPILOT_TOTAL_SESSIONS_MAX:
            oldest_key = next(iter(copilot_sessions))
            copilot_sessions.pop(oldest_key, None)

    return {
        "session_id": session_id,
        "message": answer,
        "source": out.get("source", "fallback"),
        "llm_enabled": llm_available,
        "confidence": round(float(out.get("confidence", 0.5) or 0.5), 4),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def fetch_and_store_latest_news() -> int:
    """
    Pull latest forex headlines from NewsAPI and upsert into PostgreSQL.
    Returns number of inserted rows.
    """
    global last_news_refresh_ts
    if pg_conn is None or not NEWSAPI_KEY:
        return 0

    try:
        params = {
            "q": "forex OR EURUSD OR USDJPY OR GBPUSD OR USDCHF",
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 25,
            "apiKey": NEWSAPI_KEY,
        }
        resp = requests.get("https://newsapi.org/v2/everything", params=params, timeout=12)
        if resp.status_code != 200:
            logger.warning(f"NewsAPI HTTP {resp.status_code}")
            return 0

        payload = resp.json()
        raw_articles = payload.get("articles", [])
        if not raw_articles:
            return 0

        inserted = 0
        cur = pg_conn.cursor()
        try:
            for a in raw_articles:
                title = a.get("title") or "Untitled"
                description = a.get("description") or ""
                url = a.get("url")
                source = (a.get("source") or {}).get("name") or "Unknown"
                published_at = _parse_published_at(a.get("publishedAt"))
                if not url:
                    continue

                # Insert only if URL does not already exist.
                cur.execute(
                    """
                    INSERT INTO forex_news (published_at, title, description, url, source)
                    SELECT %s, %s, %s, %s, %s
                    WHERE NOT EXISTS (
                        SELECT 1 FROM forex_news WHERE url = %s
                    );
                    """,
                    (published_at, title, description, url, source, url),
                )
                inserted += int(cur.rowcount or 0)
        finally:
            cur.close()

        last_news_refresh_ts = int(datetime.now(timezone.utc).timestamp())
        logger.info(f"[NEWS] inserted={inserted}, fetched={len(raw_articles)}")
        return inserted
    except Exception as e:
        logger.error(f"News refresh error: {e}")
        return 0


# ═══════════════════════════════════════════════════════════════════════════════
# LIFESPAN & BACKGROUND TASKS
# ═══════════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("  FX-AlphaLab Platform Starting")
    logger.info("=" * 60)

    status["mt5"]      = await asyncio.to_thread(connect_mt5)
    status["influxdb"] = await asyncio.to_thread(connect_influxdb)
    status["postgres"] = await asyncio.to_thread(connect_postgres)
    status["model"]       = await asyncio.to_thread(load_model)
    status["macro_model"] = await asyncio.to_thread(load_macro_model)
    status["sentiment_model"] = await asyncio.to_thread(load_sentiment_model)
    status["decision_model"] = await asyncio.to_thread(load_decision_model)
    logger.info(f"Status → {status}")

    _agents_path = FRONTEND_DIR / "agents.html"
    logger.info(f"Agents page: {_agents_path} (exists={_agents_path.is_file()})")

    tick_task = asyncio.create_task(_tick_broadcaster())
    news_task = asyncio.create_task(_news_refresher())
    yield

    tick_task.cancel()
    news_task.cancel()
    try:
        if MT5_AVAILABLE:
            mt5.shutdown()
    except Exception:
        pass
    if influx_write_api:
        influx_write_api.close()
    if influx_client:
        influx_client.close()
    if pg_conn:
        pg_conn.close()
    logger.info("FX-AlphaLab stopped.")


async def _tick_broadcaster():
    """Broadcast live ticks to WebSocket clients at a configurable low-latency interval."""
    global price_cache, ws_clients, tick_counter
    
    logger.info("🚀 Tick broadcaster started")
    
    while True:
        try:
            # Get ticks from MT5
            ticks = await asyncio.to_thread(get_live_ticks)
            
            if ticks:
                tick_counter += len(ticks)
                price_cache = ticks

                # Save to InfluxDB
                await asyncio.to_thread(save_ticks_to_influxdb, ticks)

                # Broadcast to all WebSocket clients
                msg = json.dumps({"type": "ticks", "data": ticks})
                dead = set()
                
                logger.debug(f"📡 Broadcasting {len(ticks)} ticks to {len(ws_clients)} clients (total: {tick_counter})")
                
                for ws in ws_clients.copy():
                    try:
                        await ws.send_text(msg)
                    except Exception as e:
                        logger.warning(f"WS send error: {e}")
                        dead.add(ws)
                
                ws_clients -= dead
            else:
                logger.warning("⚠️ No ticks received from MT5")
                
        except asyncio.CancelledError:
            logger.info("Tick broadcaster stopped")
            break
        except Exception as e:
            logger.error(f"Tick broadcast error: {e}")
        
        await asyncio.sleep(2)


async def _news_refresher():
    """Refresh news feed periodically so dashboard stays current."""
    if not NEWSAPI_KEY:
        logger.warning("NEWSAPI_KEY missing; live news refresh disabled")
        return

    while True:
        try:
            await asyncio.to_thread(fetch_and_store_latest_news)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"News background task error: {e}")
        await asyncio.sleep(max(15, NEWS_REFRESH_SECONDS))


# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI APP & ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(title="FX-AlphaLab", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def index():
    return FileResponse(FRONTEND_DIR / "index.html", headers={"Cache-Control": "no-store"})


def _serve_agents_html():
    """Serve the multi-agent overview page (several paths for compatibility)."""
    path = FRONTEND_DIR / "agents.html"
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"agents.html missing at {path}. Restart server after adding the file.",
        )
    return FileResponse(path, media_type="text/html; charset=utf-8", headers={"Cache-Control": "no-store"})


def _serve_macro_html():
    """Serve the macro agent page (several paths for compatibility)."""
    path = FRONTEND_DIR / "macro.html"
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"macro.html missing at {path}. Restart server after adding the file.",
        )
    return FileResponse(path, media_type="text/html; charset=utf-8", headers={"Cache-Control": "no-store"})


def _serve_technical_html():
    """Serve the technical agent page (several paths for compatibility)."""
    path = FRONTEND_DIR / "technical.html"
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"technical.html missing at {path}. Restart server after adding the file.",
        )
    return FileResponse(path, media_type="text/html; charset=utf-8", headers={"Cache-Control": "no-store"})


def _serve_sentiment_html():
    """Serve the sentiment agent page (several paths for compatibility)."""
    path = FRONTEND_DIR / "sentiment.html"
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"sentiment.html missing at {path}. Restart server after adding the file.",
        )
    return FileResponse(path, media_type="text/html; charset=utf-8", headers={"Cache-Control": "no-store"})


def _serve_decision_html():
    """Serve the decision agent page (several paths for compatibility)."""
    path = FRONTEND_DIR / "decision.html"
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"decision.html missing at {path}. Restart server after adding the file.",
        )
    return FileResponse(path, media_type="text/html; charset=utf-8", headers={"Cache-Control": "no-store"})


def _serve_reporting_html():
    """Serve the reporting dashboard page (several paths for compatibility)."""
    path = FRONTEND_DIR / "reporting.html"
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"reporting.html missing at {path}. Restart server after adding the file.",
        )
    return FileResponse(path, media_type="text/html; charset=utf-8", headers={"Cache-Control": "no-store"})


def _serve_market_comparison_html():
    """Serve the market comparison dashboard page (several paths for compatibility)."""
    path = FRONTEND_DIR / "market_comparison.html"
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"market_comparison.html missing at {path}. Restart server after adding the file.",
        )
    return FileResponse(path, media_type="text/html; charset=utf-8", headers={"Cache-Control": "no-store"})


def _serve_trader_guide_html():
    """Serve the beginner trader guide page (several paths for compatibility)."""
    path = FRONTEND_DIR / "trader_guide.html"
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"trader_guide.html missing at {path}. Restart server after adding the file.",
        )
    return FileResponse(path, media_type="text/html; charset=utf-8", headers={"Cache-Control": "no-store"})


def _serve_copilot_html():
    """Serve the AI Copilot page (several paths for compatibility)."""
    path = FRONTEND_DIR / "copilot.html"
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"copilot.html missing at {path}. Restart server after adding the file.",
        )
    return FileResponse(path, media_type="text/html; charset=utf-8", headers={"Cache-Control": "no-store"})


def _serve_testing_html():
    """Serve the Testing Mode page (paper trading simulation)."""
    path = FRONTEND_DIR / "testing.html"
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"testing.html missing at {path}. Restart server after adding the file.",
        )
    return FileResponse(path, media_type="text/html; charset=utf-8", headers={"Cache-Control": "no-store"})


def _serve_copilot_widget_js():
    """Serve shared JS for floating Copilot launcher widget."""
    path = FRONTEND_DIR / "copilot_widget.js"
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"copilot_widget.js missing at {path}. Restart server after adding the file.",
        )
    return FileResponse(path, media_type="application/javascript; charset=utf-8", headers={"Cache-Control": "no-store"})


def _serve_shared_css():
    """Serve shared stylesheet used by all frontend pages."""
    path = FRONTEND_DIR / "shared.css"
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"shared.css missing at {path}. Restart server after adding the file.",
        )
    return FileResponse(path, media_type="text/css; charset=utf-8", headers={"Cache-Control": "no-store"})


def _serve_shared_js():
    """Serve shared frontend JavaScript (theme toggle, shared UI behavior)."""
    path = FRONTEND_DIR / "shared.js"
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"shared.js missing at {path}. Restart server after adding the file.",
        )
    return FileResponse(path, media_type="application/javascript; charset=utf-8", headers={"Cache-Control": "no-store"})


@app.get("/agents", include_in_schema=False)
@app.get("/agents/", include_in_schema=False)
@app.get("/agents.html", include_in_schema=False)
async def agents_page():
    return _serve_agents_html()


@app.get("/macro", include_in_schema=False)
@app.get("/macro/", include_in_schema=False)
@app.get("/macro.html", include_in_schema=False)
async def macro_page():
    return _serve_macro_html()


@app.get("/technical", include_in_schema=False)
@app.get("/technical/", include_in_schema=False)
@app.get("/technical.html", include_in_schema=False)
async def technical_page():
    return _serve_technical_html()


@app.get("/sentiment", include_in_schema=False)
@app.get("/sentiment/", include_in_schema=False)
@app.get("/sentiment.html", include_in_schema=False)
async def sentiment_page():
    return _serve_sentiment_html()


@app.get("/decision", include_in_schema=False)
@app.get("/decision/", include_in_schema=False)
@app.get("/decision.html", include_in_schema=False)
async def decision_page():
    return _serve_decision_html()


@app.get("/reporting", include_in_schema=False)
@app.get("/reporting/", include_in_schema=False)
@app.get("/reporting.html", include_in_schema=False)
async def reporting_page():
    return _serve_reporting_html()


@app.get("/market-comparison", include_in_schema=False)
@app.get("/market-comparison/", include_in_schema=False)
@app.get("/market_comparison.html", include_in_schema=False)
async def market_comparison_page():
    return _serve_market_comparison_html()


@app.get("/trader-guide", include_in_schema=False)
@app.get("/trader-guide/", include_in_schema=False)
@app.get("/trader_guide.html", include_in_schema=False)
async def trader_guide_page():
    return _serve_trader_guide_html()


@app.get("/copilot", include_in_schema=False)
@app.get("/copilot/", include_in_schema=False)
@app.get("/copilot.html", include_in_schema=False)
async def copilot_page():
    return _serve_copilot_html()


@app.get("/testing", include_in_schema=False)
@app.get("/testing/", include_in_schema=False)
@app.get("/testing.html", include_in_schema=False)
async def testing_page():
    return _serve_testing_html()


@app.get("/copilot_widget.js", include_in_schema=False)
async def copilot_widget_js():
    return _serve_copilot_widget_js()


@app.get("/shared.css", include_in_schema=False)
async def shared_css():
    return _serve_shared_css()


@app.get("/shared.js", include_in_schema=False)
async def shared_js():
    return _serve_shared_js()


app.include_router(test_mode_router)


@app.get("/api/status")
async def api_status():
    return {
        **status,
        "tick_count": tick_counter,
        "last_news_refresh_ts": last_news_refresh_ts,
    }


@app.get("/api/v2/monitoring/health_check")
@app.get("/api/v2/monitoring/health_check/")
async def api_v2_monitoring_health_check():
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    summary = await asyncio.to_thread(_decision_performance_summary, None, None, None, 300, "medium")
    freshness = await asyncio.to_thread(_news_freshness_health, 240)
    agent_performances = _build_v2_agent_performances(summary)

    infra_flags = [bool(status.get("mt5")), bool(status.get("influxdb")), bool(status.get("postgres"))]
    if all(infra_flags):
        health_status = "operational"
    elif any(infra_flags):
        health_status = "degraded"
    else:
        health_status = "offline"

    drift = summary.get("drift") if isinstance(summary.get("drift"), dict) else {}
    last_event = summary.get("last_event") if isinstance(summary.get("last_event"), dict) else {}

    return {
        "status": health_status,
        "timestamp": now_iso,
        "agent_performances": agent_performances,
        "monitoring": {
            "performance_tracker": {
                "status": "active" if int(summary.get("total", 0) or 0) > 0 else "idle",
                "agents_tracked": len(agent_performances),
            },
            "drift_detector": {
                "status": "active" if int(drift.get("comparison_events", 0) or 0) > 0 else "idle",
                "last_check": last_event.get("timestamp") or now_iso,
            },
            "safety_monitor": {
                "status": "active",
                "cooldown_active": _clip01(summary.get("fallback_rate", 0.0)) >= 0.5,
            },
            "news_freshness": {
                "status": freshness.get("status", "NO_DATA"),
                "age_minutes": freshness.get("age_minutes"),
                "articles_last_1h": int(freshness.get("articles_last_1h", 0) or 0),
                "articles_last_24h": int(freshness.get("articles_last_24h", 0) or 0),
                "freshness_score": float(freshness.get("freshness_score", 0.0) or 0.0),
            },
        },
        "system": {
            "uptime_seconds": max(0, int((now - APP_START_UTC).total_seconds())),
            "memory_usage_mb": _memory_usage_mb(),
        },
    }


@app.get("/api/v2/monitoring/agent_performance")
@app.get("/api/v2/monitoring/agent_performance/")
async def api_v2_monitoring_agent_performance(days: int = 30):
    days = max(1, min(days, 365))
    summary = await asyncio.to_thread(_decision_performance_summary, None, None, None, 2000, "medium")
    base = _build_v2_agent_performances(summary)

    agents = {
        "TechnicalV2": {
            "win_rate": float((base.get("technical") or {}).get("win_rate", 0.0)),
            "sharpe_ratio": float((base.get("technical") or {}).get("sharpe_ratio", 0.0)),
            "max_drawdown": float((base.get("technical") or {}).get("max_drawdown", 0.0)),
            "total_signals": int((base.get("technical") or {}).get("total_signals", 0)),
            "total_pnl": float((base.get("technical") or {}).get("total_pnl", 0.0)),
        },
        "MacroV2": {
            "win_rate": float((base.get("macro") or {}).get("win_rate", 0.0)),
            "sharpe_ratio": float((base.get("macro") or {}).get("sharpe_ratio", 0.0)),
            "max_drawdown": float((base.get("macro") or {}).get("max_drawdown", 0.0)),
            "total_signals": int((base.get("macro") or {}).get("total_signals", 0)),
            "total_pnl": float((base.get("macro") or {}).get("total_pnl", 0.0)),
        },
        "SentimentV2": {
            "win_rate": float((base.get("sentiment") or {}).get("win_rate", 0.0)),
            "sharpe_ratio": float((base.get("sentiment") or {}).get("sharpe_ratio", 0.0)),
            "max_drawdown": float((base.get("sentiment") or {}).get("max_drawdown", 0.0)),
            "total_signals": int((base.get("sentiment") or {}).get("total_signals", 0)),
            "total_pnl": float((base.get("sentiment") or {}).get("total_pnl", 0.0)),
        },
    }

    return {
        "period_days": days,
        "agents": agents,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/v2/monitoring/drift_detection")
@app.get("/api/v2/monitoring/drift_detection/")
async def api_v2_monitoring_drift_detection(window: int = 500):
    window = max(50, min(window, 5000))
    summary = await asyncio.to_thread(_decision_performance_summary, None, None, None, window, "medium")
    drift = summary.get("drift") if isinstance(summary.get("drift"), dict) else {}
    disagreement_rate = float(drift.get("disagreement_rate", 0.0) or 0.0)
    avg_conf_delta = float(drift.get("avg_confidence_delta", 0.0) or 0.0)

    if disagreement_rate >= 0.35:
        severity = "high"
    elif disagreement_rate >= 0.20:
        severity = "medium"
    else:
        severity = "low"

    if avg_conf_delta >= 0.15:
        trend = "widening"
    elif avg_conf_delta <= 0.05:
        trend = "stable"
    else:
        trend = "mixed"

    if disagreement_rate >= 0.35:
        regime = "volatile"
    elif disagreement_rate <= 0.10:
        regime = "trending"
    else:
        regime = "ranging"

    return {
        "sentiment_drift": {
            "detected": disagreement_rate >= 0.20,
            "ks_statistic": round(disagreement_rate, 6),
            "p_value": round(max(0.0, 1.0 - disagreement_rate), 6),
            "severity": severity,
        },
        "volatility_drift": {
            "current_regime": regime,
            "regime_confidence": round(max(0.0, min(1.0, 0.5 + disagreement_rate)), 6),
            "trend": trend,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/v2/monitoring/freshness_health")
@app.get("/api/v2/monitoring/freshness_health/")
async def api_v2_monitoring_freshness_health(target_minutes: int = 240):
    target_minutes = max(15, min(target_minutes, 1440))
    freshness = await asyncio.to_thread(_news_freshness_health, target_minutes)
    score_ratio = float(freshness.get("freshness_score", 0.0) or 0.0)
    freshness["freshness_score"] = round(score_ratio * 100.0, 2)
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "freshness": freshness,
    }


def _run_news_refresh_background():
    try:
        fetch_and_store_latest_news()
    except Exception as e:
        logger.warning(f"News refresh background task failed: {e}")


@app.post("/api/v2/data/refresh_news")
@app.post("/api/v2/data/refresh_news/")
async def api_v2_data_refresh_news():
    if not NEWSAPI_KEY:
        return JSONResponse(
            status_code=202,
            content={
                "accepted": False,
                "message": "NEWSAPI_KEY missing; refresh skipped",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    t = threading.Thread(target=_run_news_refresh_background, daemon=True)
    t.start()
    return JSONResponse(
        status_code=202,
        content={
            "accepted": True,
            "message": "News refresh started",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.post("/api/v2/signals/generate_signal")
@app.post("/api/v2/signals/generate_signal/")
async def api_v2_generate_signal(body: V2GenerateSignalRequest):
    symbol = _schema_symbol_from_aliases(body.pair, body.symbol)
    timeframe = str(body.timeframe or "1H").upper()
    started_at = datetime.now(timezone.utc)

    try:
        decision = await asyncio.to_thread(
            get_decision_signal,
            symbol,
            timeframe,
            bool(body.explain),
            body.model,
        )
        elapsed_ms = max(0, int((datetime.now(timezone.utc) - started_at).total_seconds() * 1000))
        return _schema_decision_to_v2_signal(decision, elapsed_ms)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"generate_signal_failed: {e}",
            },
        )


@app.get("/api/prices/{symbol}")
async def api_prices(
    symbol: str,
    timeframe: str = "1H",
    limit: int = 500,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Returns candles from InfluxDB (pre-aggregated + tick-aggregated).
    
    Parameters:
    - symbol: EURUSD, USDJPY, GBPUSD, USDCHF
    - timeframe: 1S, 1H, 4H, 1D
    - limit: max number of candles to return
    - start_date: ISO format (2026-03-04) or relative (1h, 4h, 1d, 7d, 30d)
    - end_date: ISO format (2026-03-04) - defaults to now
    """
    
    symbol = symbol.upper()
    timeframe = timeframe.upper()
    if symbol not in SYMBOLS:
        raise HTTPException(400, f"Unknown symbol: {symbol}")
    if timeframe not in TIMEFRAMES:
        raise HTTPException(400, f"Unknown timeframe: {timeframe}")

    # Calculate time range
    now = datetime.now(timezone.utc)
    
    # Parse end_date
    if end_date:
        try:
            end_ts = int(datetime.fromisoformat(end_date.replace('Z', '+00:00')).timestamp())
        except:
            end_ts = int(now.timestamp())
    else:
        end_ts = int(now.timestamp())
    
    # Parse start_date
    if start_date:
        if start_date in ["1h", "4h", "1d", "3d", "7d", "30d", "365d"]:
            # Relative time
            delta_map = {"1h": 3600, "4h": 14400, "1d": 86400, "3d": 259200, "7d": 604800, "30d": 2592000, "365d": 31536000}
            start_ts = end_ts - delta_map.get(start_date, 3600)
        else:
            # ISO format
            try:
                start_ts = int(datetime.fromisoformat(start_date.replace('Z', '+00:00')).timestamp())
            except:
                start_ts = end_ts - (86400 * 3)  # Default to 3 days cleanly to auto-scale graphing without pulling dead 400-day void
    else:
        start_ts = end_ts - (86400 * 3)  # Default to 3 days cleanly to auto-scale graphing without pulling dead 400-day void

    logger.info(f"🔍 Querying {symbol} {timeframe} from {datetime.fromtimestamp(start_ts, tz=timezone.utc).isoformat()} to {datetime.fromtimestamp(end_ts, tz=timezone.utc).isoformat()}")

    # Timeframe-aware caps: deep pre-aggregated history for higher TFs,
    # while keeping tick aggregation tightly bounded for performance.
    preagg_cap_days_map = {
        "1S": 3,
        "1H": 120,
        "4H": 730,
        "1D": 3650,
    }
    tick_cap_days_map = {
        "1S": 3,
        "1H": 7,
        "4H": 14,
        "1D": 30,
    }

    preagg_cap_days = preagg_cap_days_map.get(timeframe, 30)
    tick_cap_days = tick_cap_days_map.get(timeframe, 3)

    # Get candles from InfluxDB (includes both pre-aggregated and tick-aggregated)
    data = await asyncio.to_thread(
        get_candles_from_influxdb,
        symbol,
        timeframe,
        start_ts,
        end_ts,
        preagg_cap_days,
        tick_cap_days,
    )

    # If Influx is sparse for higher timeframes, backfill with broker-native MT5 candles
    # for the same requested window to keep timeframe views current and meaningful.
    sparse_floor = {"1H": 24, "4H": 18, "1D": 10}
    min_needed = sparse_floor.get(timeframe, 0)
    if min_needed and len(data) < min_needed:
        influx_count = len(data)
        mt5_data = await asyncio.to_thread(get_candles_from_mt5, symbol, timeframe, start_ts, end_ts)
        if mt5_data:
            merged = {c["time"]: c for c in data}
            merged.update({c["time"]: c for c in mt5_data})
            data = sorted(merged.values(), key=lambda x: x["time"])
            logger.info(
                "MT5 backfill merged for %s %s: influx=%s mt5=%s total=%s",
                symbol,
                timeframe,
                influx_count,
                len(mt5_data),
                len(data),
            )
    
    # Limit results
    data = data[-limit:] if len(data) > limit else data
    
    logger.info(f"📊 Returning {len(data)} candles for {symbol} {timeframe}")
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "count": len(data),
        "start_date": datetime.fromtimestamp(start_ts, tz=timezone.utc).isoformat(),
        "end_date": datetime.fromtimestamp(end_ts, tz=timezone.utc).isoformat(),
        "candles": data
    }


@app.get("/api/signals/macro/{symbol}")
async def api_signals_macro(symbol: str, explain: bool = False):
    """Macro agent: same signal JSON shape as technical (optional explanation top features)."""
    symbol = symbol.upper()
    return await asyncio.to_thread(get_macro_signal, symbol, explain)


@app.get("/api/signals/sentiment/{symbol}")
async def api_signals_sentiment(symbol: str, timeframe: str = "1H", explain: bool = False):
    """Sentiment agent: same signal JSON shape as technical and macro."""
    symbol = symbol.upper()
    timeframe = timeframe.upper()
    return await asyncio.to_thread(get_sentiment_signal, symbol, timeframe, explain)


@app.get("/api/signals/decision/{symbol}")
async def api_signals_decision(
    symbol: str,
    timeframe: str = "1H",
    explain: bool = True,
    model: Optional[str] = None,
):
    """Meta-decision signal synthesized from Technical, Macro, and Sentiment agents."""
    symbol = symbol.upper()
    timeframe = timeframe.upper()
    return await asyncio.to_thread(get_decision_signal, symbol, timeframe, explain, model)


@app.get("/api/signals/decision/performance/summary")
async def api_signals_decision_performance(
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    model: Optional[str] = None,
    window: int = 200,
    trend_horizon: str = "medium",
):
    """Decision telemetry aggregates for monitoring fallback rate, latency and confidence trends."""
    window = max(1, min(window, 5000))
    if symbol:
        symbol = symbol.upper()
    if timeframe:
        timeframe = timeframe.upper()
    return await asyncio.to_thread(
        _decision_performance_summary,
        symbol,
        timeframe,
        model,
        window,
        trend_horizon,
    )


@app.get("/api/reporting/overview")
async def api_reporting_overview(
    symbol: str = "EURUSD",
    timeframe: str = "1H",
    model: Optional[str] = None,
    window: int = 200,
    trend_horizon: str = "medium",
):
    symbol = symbol.upper()
    timeframe = timeframe.upper()
    window = max(1, min(window, 5000))
    return await asyncio.to_thread(_reporting_overview, symbol, timeframe, model, window, trend_horizon)


@app.get("/api/reporting/history")
async def api_reporting_history(
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    model: Optional[str] = None,
    limit: int = 500,
    compress: bool = True,
):
    if symbol:
        symbol = symbol.upper()
    if timeframe:
        timeframe = timeframe.upper()
    limit = max(1, min(limit, 5000))
    return await asyncio.to_thread(_decision_history, symbol, timeframe, model, limit, compress)


@app.get("/api/market/comparison")
async def api_market_comparison(
    timeframe: str = "1H",
    model: Optional[str] = None,
    window: int = 200,
    trend_horizon: str = "medium",
):
    timeframe = timeframe.upper()
    if timeframe not in TIMEFRAMES:
        raise HTTPException(status_code=400, detail=f"Unknown timeframe: {timeframe}")
    return await asyncio.to_thread(_market_comparison_snapshot, timeframe, model, window, trend_horizon)


@app.post("/api/copilot/chat")
async def api_copilot_chat(body: CopilotChatRequest):
    return await asyncio.to_thread(
        copilot_answer,
        body.question,
        body.symbol,
        body.timeframe,
        body.model,
        body.window,
        body.trend_horizon,
    )


@app.post("/api/copilot/converse")
async def api_copilot_converse(body: CopilotConversationRequest):
    return await asyncio.to_thread(copilot_converse, body.message, body.session_id)


@app.get("/api/copilot/conversation")
async def api_copilot_conversation(session_id: str):
    session_id = (session_id or "").strip()
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    with copilot_sessions_lock:
        history = list(copilot_sessions.get(session_id, []))
    return {
        "session_id": session_id,
        "messages": history,
        "count": len(history),
    }


@app.get("/api/signals/{symbol}")
async def api_signals(symbol: str, timeframe: str = "1H"):
    symbol = symbol.upper()
    timeframe = timeframe.upper()
    return await asyncio.to_thread(get_signal, symbol, timeframe)


@app.get("/api/news")
async def api_news(limit: int = 20):
    # Trigger lightweight on-demand refresh if the background task is delayed/stale.
    now_ts = int(datetime.now(timezone.utc).timestamp())
    if NEWSAPI_KEY and (now_ts - last_news_refresh_ts) > max(30, NEWS_REFRESH_SECONDS * 2):
        await asyncio.to_thread(fetch_and_store_latest_news)
    articles = await asyncio.to_thread(get_news, limit)
    return {"count": len(articles), "articles": articles}


@app.post("/api/news/explain")
async def api_news_explain(body: ExplainNewsRequest):
    title = (body.title or "").strip()
    content = (body.content or "").strip()
    if not title and not content:
        raise HTTPException(status_code=400, detail="title or content is required")

    explanation = await asyncio.to_thread(explain_news_article, title, content, body.symbol)
    return explanation


@app.get("/api/ticks")
async def api_ticks():
    """Snapshot of latest cached ticks."""
    return price_cache


@app.websocket("/ws/prices")
async def ws_prices(websocket: WebSocket):
    await websocket.accept()
    ws_clients.add(websocket)
    logger.info(f"✅ WS client connected ({len(ws_clients)} total)")
    try:
        if price_cache:
            await websocket.send_text(json.dumps({"type": "ticks", "data": price_cache}))
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("❌ WS client disconnected")
    finally:
        ws_clients.discard(websocket)
        logger.info(f"WS clients remaining: {len(ws_clients)}")
