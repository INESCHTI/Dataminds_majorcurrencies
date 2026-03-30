import os
import time
import threading
import signal
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import MetaTrader5 as mt5
from influxdb_client import InfluxDBClient, Point, WritePrecision
import psycopg2
import requests

class RealTimeScraper:
    def __init__(self, config_path="../../config/.env"):
        project_root = Path(__file__).resolve().parents[2]
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        load_dotenv(config_path)
        self.mt5_login = int(os.getenv("MT5_LOGIN"))
        self.mt5_password = os.getenv("MT5_PASSWORD")
        self.mt5_server = os.getenv("MT5_SERVER")
        self.mt5_path = os.getenv("MT5_PATH", r"C:\Program Files\MetaTrader 5\terminal64.exe")
        self.influxdb_url = os.getenv("INFLUXDB_URL")
        self.influxdb_token = os.getenv("INFLUXDB_TOKEN")
        self.influxdb_org = os.getenv("INFLUXDB_ORG")
        self.influxdb_bucket = os.getenv("INFLUXDB_BUCKET")
        self.pg_host = os.getenv("POSTGRES_HOST")
        self.pg_port = int(os.getenv("POSTGRES_PORT", 5432))
        self.pg_db = os.getenv("POSTGRES_DB")
        self.pg_user = os.getenv("POSTGRES_USER")
        self.pg_password = os.getenv("POSTGRES_PASSWORD")
        self.newsapi_key = os.getenv("NEWSAPI_KEY")
        self.fred_refresh_enabled = os.getenv("FRED_REFRESH_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}
        self.symbols = ["EURUSD", "USDJPY", "GBPUSD", "USDCHF"]
        self.price_interval = 2
        self.news_interval = 300  # 5 minutes
        self.fred_interval = max(300, int(os.getenv("FRED_REFRESH_SECONDS", "3600")))
        self.last_news_check = datetime.now(timezone.utc) - timedelta(seconds=self.news_interval)
        self.last_fred_check = datetime.now(timezone.utc) - timedelta(seconds=self.fred_interval)
        self._stop_event = threading.Event()
        self._setup_logging()
        self._init_connections()

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format="[%(asctime)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        self.logger = logging.getLogger("RealTimeScraper")

    def _init_connections(self):
        if not self._connect_mt5():
            self.logger.warning("MT5: Initial connection failed, will retry in background.")
        if not self._connect_influxdb():
            self.logger.warning("InfluxDB: Initial connection failed, will retry in background.")
        if not self._connect_postgres():
            self.logger.warning("PostgreSQL: Initial connection failed, will retry in background.")

    def _connect_mt5(self, timeout=30):
        """Attempt a single MT5 connection with timeout. Returns True on success."""
        mt5.shutdown()  # ensure clean state before init
        result = [None]

        def _init():
            result[0] = mt5.initialize(
                path=self.mt5_path, server=self.mt5_server,
                login=self.mt5_login, password=self.mt5_password
            )

        t = threading.Thread(target=_init, daemon=True)
        t.start()
        t.join(timeout=timeout)

        if t.is_alive():
            self.logger.error(f"MT5: initialize() timed out after {timeout}s (path={self.mt5_path}).")
            return False
        if result[0]:
            self.logger.info(f"MT5: Connected (path={self.mt5_path}).")
            return True
        else:
            err = mt5.last_error()
            self.logger.error(f"MT5: Connection failed: {err} (path={self.mt5_path}).")
            return False

    def _connect_influxdb(self):
        """Attempt a single InfluxDB connection with health check. Returns True on success."""
        try:
            self.influx_client = InfluxDBClient(
                url=self.influxdb_url,
                token=self.influxdb_token,
                org=self.influxdb_org
            )
            # Verify the connection is alive with a health check
            health = self.influx_client.health()
            if health.status != "pass":
                self.logger.error(f"InfluxDB: Health check failed: {health.message}")
                return False
            from influxdb_client.client.write_api import SYNCHRONOUS
            self.influx_write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
            self.logger.info("InfluxDB: Connected.")
            return True
        except Exception as e:
            self.logger.error(f"InfluxDB: Connection failed: {e}.")
            return False

    def _connect_postgres(self):
        """Attempt a single PostgreSQL connection. Returns True on success."""
        try:
            self.pg_conn = psycopg2.connect(
                host=self.pg_host,
                port=self.pg_port,
                dbname=self.pg_db,
                user=self.pg_user,
                password=self.pg_password
            )
            self.pg_conn.autocommit = True
            self.pg_cursor = self.pg_conn.cursor()
            self._ensure_news_table()
            self.logger.info("PostgreSQL: Connected.")
            return True
        except Exception as e:
            self.logger.error(f"PostgreSQL: Connection failed: {e}.")
            return False

    def _ensure_news_table(self):
        self.pg_cursor.execute('''
            CREATE TABLE IF NOT EXISTS forex_news (
                id SERIAL PRIMARY KEY,
                published_at TIMESTAMP,
                title TEXT,
                description TEXT,
                url TEXT,
                source TEXT
            );
        ''')

    def _retry_connect(self, connect_func, delay=5, max_retries=5):
        """Retry a connection function up to max_retries times."""
        for attempt in range(1, max_retries + 1):
            if self._stop_event.is_set():
                return False
            self.logger.info(f"Retry {attempt}/{max_retries} for {connect_func.__name__} in {delay}s...")
            time.sleep(delay)
            try:
                if connect_func():
                    return True
            except Exception as e:
                self.logger.error(f"Retry {attempt} failed: {e}")
        self.logger.error(f"All {max_retries} retries exhausted for {connect_func.__name__}.")
        return False

    def _scrape_prices(self):
        while not self._stop_event.is_set():
            for symbol in self.symbols:
                try:
                    tick = mt5.symbol_info_tick(symbol)
                    if tick is None:
                        self.logger.warning(f"{symbol}: No tick data (MT5 may be disconnected).")
                        self._retry_connect(self._connect_mt5, max_retries=3)
                        break  # restart symbol loop after reconnect
                    point = Point("forex_price") \
                        .tag("symbol", symbol) \
                        .field("bid", float(tick.bid)) \
                        .field("ask", float(tick.ask)) \
                        .time(datetime.now(timezone.utc), WritePrecision.S)
                    try:
                        self.influx_write_api.write(bucket=self.influxdb_bucket, org=self.influxdb_org, record=point)
                        self.logger.info(f"{symbol}: {tick.bid} | InfluxDB: OK")
                    except Exception as e:
                        self.logger.error(f"{symbol}: InfluxDB write error: {e}. Reconnecting InfluxDB...")
                        self._retry_connect(self._connect_influxdb, max_retries=3)
                        break  # restart symbol loop after reconnect
                except Exception as e:
                    self.logger.error(f"{symbol}: MT5 error: {e}. Reconnecting MT5...")
                    self._retry_connect(self._connect_mt5, max_retries=3)
                    break
            time.sleep(self.price_interval)

    def _scrape_news(self):
        while not self._stop_event.is_set():
            now = datetime.now(timezone.utc)
            if (now - self.last_news_check).total_seconds() >= self.news_interval:
                try:
                    url = f"https://newsapi.org/v2/top-headlines?category=business&language=en&apiKey={self.newsapi_key}"
                    resp = requests.get(url, timeout=10)
                    if resp.status_code == 200:
                        news = resp.json().get("articles", [])
                        for article in news:
                            published_at = article.get("publishedAt")
                            title = article.get("title")
                            description = article.get("description")
                            url = article.get("url")
                            source = article.get("source", {}).get("name")
                            self.pg_cursor.execute(
                                """
                                INSERT INTO forex_news (published_at, title, description, url, source)
                                VALUES (%s, %s, %s, %s, %s)
                                ON CONFLICT DO NOTHING;
                                """,
                                (published_at, title, description, url, source)
                            )
                        self.logger.info(f"NewsAPI: {len(news)} articles inserted.")
                    else:
                        self.logger.warning(f"NewsAPI: HTTP {resp.status_code}")
                except Exception as e:
                    self.logger.error(f"NewsAPI: Error: {e}. Reconnecting...")
                    self._retry_connect(self._connect_postgres, max_retries=3)
                self.last_news_check = now
            time.sleep(5)

    def _scrape_fred(self):
        if not self.fred_refresh_enabled:
            self.logger.info("FRED refresh: disabled")
            return

        try:
            from data_understanding.acquire_fred_data import fetch_fred_data, write_to_postgres
        except Exception as e:
            self.logger.error(f"FRED refresh: import error: {e}")
            return

        self.logger.info(f"FRED refresh: enabled every {self.fred_interval}s")

        while not self._stop_event.is_set():
            now = datetime.now(timezone.utc)
            if (now - self.last_fred_check).total_seconds() >= self.fred_interval:
                try:
                    df = fetch_fred_data()
                    if df is not None and len(df) > 0:
                        write_to_postgres(df)
                        self.logger.info(f"FRED refresh: upserted {len(df)} rows into economic_indicators")
                    else:
                        self.logger.warning("FRED refresh: no rows returned")
                except Exception as e:
                    self.logger.error(f"FRED refresh: error: {e}")
                    self._retry_connect(self._connect_postgres, max_retries=3)
                self.last_fred_check = now
            time.sleep(10)

    def start(self):
        self.logger.info("Starting RealTimeScraper agent...")
        self.price_thread = threading.Thread(target=self._scrape_prices, daemon=True)
        self.news_thread = threading.Thread(target=self._scrape_news, daemon=True)
        self.fred_thread = threading.Thread(target=self._scrape_fred, daemon=True)
        self.price_thread.start()
        self.news_thread.start()
        self.fred_thread.start()
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        while not self._stop_event.is_set():
            time.sleep(1)
        self._cleanup()

    def _signal_handler(self, signum, frame):
        self.logger.info("Received stop signal. Shutting down...")
        self._stop_event.set()

    def _cleanup(self):
        try:
            mt5.shutdown()
            self.logger.info("MT5: Disconnected.")
        except Exception:
            pass
        try:
            self.influx_client.close()
            self.logger.info("InfluxDB: Disconnected.")
        except Exception:
            pass
        try:
            self.pg_cursor.close()
            self.pg_conn.close()
            self.logger.info("PostgreSQL: Disconnected.")
        except Exception:
            pass
        self.logger.info("RealTimeScraper stopped.")

if __name__ == "__main__":
    agent = RealTimeScraper()
    agent.start()
