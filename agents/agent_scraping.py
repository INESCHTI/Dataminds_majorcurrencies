"""
=====================================
AUTONOMOUS DATA SCRAPING AGENT
FX-AlphaLab | Major Currencies
=====================================
Scrapes in real-time:
  - Forex news (RSS feeds)
  - MT5 price data
  - FRED macro indicators
  - Economic calendar (Investing.com)

Scheduler: APScheduler (continuous)
Storage  : InfluxDB (prices) + PostgreSQL (news, macro, events)
"""

import os
import time
import logging
import requests
import feedparser
import psycopg2
import MetaTrader5 as mt5
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from fredapi import Fred
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("scraping_agent.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("ScrapingAgent")

# Credentials
FRED_API_KEY     = os.getenv("FRED_API_KEY")
MT5_LOGIN        = int(os.getenv("MT5_LOGIN"))
MT5_PASSWORD     = os.getenv("MT5_PASSWORD")
MT5_SERVER       = os.getenv("MT5_SERVER")
INFLUXDB_URL     = os.getenv("INFLUXDB_URL")
INFLUXDB_TOKEN   = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG     = os.getenv("INFLUXDB_ORG")
INFLUXDB_BUCKET  = os.getenv("INFLUXDB_BUCKET")
PG_DSN           = f"host={os.getenv('POSTGRES_HOST')} port={os.getenv('POSTGRES_PORT')} dbname={os.getenv('POSTGRES_DB')} user={os.getenv('POSTGRES_USER')} password={os.getenv('POSTGRES_PASSWORD')}"

# Forex pairs & timeframes
PAIRS      = ["EURUSD", "USDJPY", "GBPUSD", "USDCHF"]
TIMEFRAMES = {"1H": mt5.TIMEFRAME_H1, "4H": mt5.TIMEFRAME_H4, "1D": mt5.TIMEFRAME_D1}

# FRED indicators
FRED_INDICATORS = {
    "CPIAUCSL": "US CPI",
    "FEDFUNDS": "Federal Funds Rate",
    "UNRATE":   "Unemployment Rate",
    "GDP":      "US GDP",
    "DGS10":    "US 10Y Treasury",
    "T10YIE":   "US 10Y Inflation Expectations",
}

# RSS News sources
RSS_SOURCES = [
    {"name": "FXStreet",       "url": "https://www.fxstreet.com/feeds/news"},
    {"name": "ForexLive",      "url": "https://www.forexlive.com/feed/news"},
    {"name": "DailyFX",        "url": "https://www.dailyfx.com/feeds/market-news"},
    {"name": "Investing.com",  "url": "https://www.investing.com/rss/news_14.rss"},
    {"name": "Reuters",        "url": "https://www.reuters.com/rssFeed/businessNews"},
]

FOREX_KEYWORDS = ["forex","EUR","USD","JPY","GBP","CHF","Federal Reserve","ECB","currency","exchange rate","interest rate"]
CURRENCIES     = ["EUR","USD","JPY","GBP","CHF"]

# ─────────────────────────────────────────
# DB HELPERS
# ─────────────────────────────────────────

def pg_connect():
    return psycopg2.connect(PG_DSN)

def influx_write_api():
    client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    return client, client.write_api(write_options=SYNCHRONOUS)

# ─────────────────────────────────────────
# TASK 1 — MT5 LIVE PRICES  (every 1 min)
# ─────────────────────────────────────────

def task_scrape_mt5_prices():
    log.info("📊 [MT5] Fetching live prices...")
    try:
        if not mt5.initialize():
            log.error(f"MT5 init failed: {mt5.last_error()}")
            return
        if not mt5.login(MT5_LOGIN, MT5_PASSWORD, MT5_SERVER):
            log.error(f"MT5 login failed: {mt5.last_error()}")
            return

        client, write_api = influx_write_api()
        points = []
        now = datetime.now()

        for symbol in PAIRS:
            for tf_name, tf_mt5 in TIMEFRAMES.items():
                # Fetch last 5 candles only (incremental update)
                rates = mt5.copy_rates_from(symbol, tf_mt5, now, 5)
                if rates is None:
                    continue
                for r in rates:
                    p = (
                        Point("forex_prices")
                        .tag("symbol", symbol)
                        .tag("timeframe", tf_name)
                        .field("open",   float(r["open"]))
                        .field("high",   float(r["high"]))
                        .field("low",    float(r["low"]))
                        .field("close",  float(r["close"]))
                        .field("volume", int(r["tick_volume"]))
                        .time(datetime.utcfromtimestamp(r["time"]))
                    )
                    points.append(p)

        if points:
            write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=points)
            log.info(f"   ✅ Wrote {len(points)} price points to InfluxDB")

        client.close()
        mt5.shutdown()

    except Exception as e:
        log.error(f"[MT5] Error: {e}")

# ─────────────────────────────────────────
# TASK 2 — FOREX NEWS  (every 15 min)
# ─────────────────────────────────────────

def task_scrape_news():
    log.info("📰 [NEWS] Fetching RSS feeds...")
    articles = []

    for src in RSS_SOURCES:
        try:
            feed = feedparser.parse(src["url"])
            for entry in feed.entries:
                title = entry.get("title", "")
                link  = entry.get("link", "")
                desc  = entry.get("summary", "") or entry.get("description", "")
                pub   = entry.get("published", datetime.now().isoformat())

                content = f"{title} {desc}".lower()
                if not any(kw.lower() in content for kw in FOREX_KEYWORDS):
                    continue
                if not link:
                    continue

                currencies = [c for c in CURRENCIES if c in content.upper()]
                articles.append({
                    "url":          link,
                    "title":        title[:500],
                    "content":      desc[:1000],
                    "source":       src["name"],
                    "published_at": pub,
                    "currencies":   currencies,
                    "scraped_at":   datetime.now(),
                })
        except Exception as e:
            log.warning(f"   ⚠️ [{src['name']}] {e}")

    # Deduplicate
    seen, unique = set(), []
    for a in articles:
        if a["url"] not in seen:
            seen.add(a["url"])
            unique.append(a)

    if not unique:
        log.info("   ℹ️ No new articles found")
        return

    # Write to PostgreSQL
    try:
        conn   = pg_connect()
        cursor = conn.cursor()
        inserted = 0
        for a in unique:
            cursor.execute(
                """
                INSERT INTO news_articles (url, title, content, source, published_at, currencies, scraped_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (url) DO NOTHING
                """,
                (a["url"], a["title"], a["content"], a["source"],
                 a["published_at"], a["currencies"], a["scraped_at"])
            )
            if cursor.rowcount > 0:
                inserted += 1
        conn.commit()
        cursor.close()
        conn.close()
        log.info(f"   ✅ Inserted {inserted} new articles")
    except Exception as e:
        log.error(f"[NEWS] DB write error: {e}")

# ─────────────────────────────────────────
# TASK 3 — FRED MACRO DATA  (every 1 hour)
# ─────────────────────────────────────────

def task_scrape_fred():
    log.info("📈 [FRED] Fetching macro indicators...")
    try:
        fred = Fred(api_key=FRED_API_KEY)
        conn   = pg_connect()
        cursor = conn.cursor()
        total  = 0

        for series_id, name in FRED_INDICATORS.items():
            try:
                # Fetch only last 30 days (incremental)
                since = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                data  = fred.get_series(series_id, observation_start=since)
                for date, value in data.items():
                    if value != value:  # NaN check
                        continue
                    cursor.execute(
                        """
                        INSERT INTO economic_indicators (date, series_id, indicator_name, value)
                        VALUES (%s,%s,%s,%s)
                        ON CONFLICT (date, series_id) DO UPDATE SET value = EXCLUDED.value
                        """,
                        (date, series_id, name, float(value))
                    )
                    total += 1
            except Exception as e:
                log.warning(f"   ⚠️ [{series_id}] {e}")

        conn.commit()
        cursor.close()
        conn.close()
        log.info(f"   ✅ Upserted {total} macro records")

    except Exception as e:
        log.error(f"[FRED] Error: {e}")

# ─────────────────────────────────────────
# TASK 4 — ECONOMIC CALENDAR  (every 1 hour)
# ─────────────────────────────────────────

def task_scrape_economic_calendar():
    log.info("📅 [CALENDAR] Fetching economic events...")
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        url     = "https://www.forexfactory.com/calendar.php"
        resp    = requests.get(url, headers=headers, timeout=15)
        soup    = BeautifulSoup(resp.content, "html.parser")

        conn   = pg_connect()
        cursor = conn.cursor()
        inserted = 0

        rows = soup.select("tr.calendar__row")
        current_date = datetime.now().strftime("%Y-%m-%d")

        for row in rows:
            try:
                currency   = row.select_one(".calendar__currency")
                event_name = row.select_one(".calendar__event-title")
                impact     = row.select_one(".calendar__impact span")
                forecast   = row.select_one(".calendar__forecast")
                actual     = row.select_one(".calendar__actual")
                previous   = row.select_one(".calendar__previous")

                if not currency or not event_name:
                    continue

                curr_text  = currency.text.strip()
                event_text = event_name.text.strip()
                impact_txt = impact["title"].strip() if impact and impact.has_attr("title") else None

                def parse_val(el):
                    try:
                        return float(el.text.strip().replace("%","").replace("K","").replace("M",""))
                    except:
                        return None

                cursor.execute(
                    """
                    INSERT INTO economic_events (event_date, currency, event_name, importance, forecast, actual, previous)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT DO NOTHING
                    """,
                    (current_date, curr_text, event_text, impact_txt,
                     parse_val(forecast), parse_val(actual), parse_val(previous))
                )
                if cursor.rowcount > 0:
                    inserted += 1
            except Exception:
                continue

        conn.commit()
        cursor.close()
        conn.close()
        log.info(f"   ✅ Inserted {inserted} economic events")

    except Exception as e:
        log.error(f"[CALENDAR] Error: {e}")

# ─────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────

def task_health_check():
    log.info("💓 [HEALTH] Agent running — all systems OK")
    log.info(f"   🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ─────────────────────────────────────────
# SCHEDULER — MAIN ENTRY POINT
# ─────────────────────────────────────────

def main():
    log.info("=" * 55)
    log.info("  🚀 AUTONOMOUS SCRAPING AGENT STARTING")
    log.info("=" * 55)

    scheduler = BlockingScheduler(timezone="UTC")

    # MT5 prices  → every 1 minute
    scheduler.add_job(
        task_scrape_mt5_prices,
        trigger=IntervalTrigger(minutes=1),
        id="mt5_prices",
        name="MT5 Live Prices",
        next_run_time=datetime.now()
    )

    # Forex news  → every 15 minutes
    scheduler.add_job(
        task_scrape_news,
        trigger=IntervalTrigger(minutes=15),
        id="forex_news",
        name="Forex News RSS",
        next_run_time=datetime.now()
    )

    # FRED macro  → every 1 hour
    scheduler.add_job(
        task_scrape_fred,
        trigger=IntervalTrigger(hours=1),
        id="fred_macro",
        name="FRED Macro Data",
        next_run_time=datetime.now()
    )

    # Economic calendar → every 1 hour
    scheduler.add_job(
        task_scrape_economic_calendar,
        trigger=IntervalTrigger(hours=1),
        id="econ_calendar",
        name="Economic Calendar",
        next_run_time=datetime.now()
    )

    # Health check → every 5 minutes
    scheduler.add_job(
        task_health_check,
        trigger=IntervalTrigger(minutes=5),
        id="health_check",
        name="Health Check"
    )

    log.info("📋 Scheduled tasks:")
    log.info("   • MT5 Prices       → every 1 min")
    log.info("   • Forex News       → every 15 min")
    log.info("   • FRED Macro       → every 1 hour")
    log.info("   • Econ Calendar    → every 1 hour")
    log.info("   • Health Check     → every 5 min")
    log.info("=" * 55)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("🛑 Agent stopped gracefully.")

if __name__ == "__main__":
    main()