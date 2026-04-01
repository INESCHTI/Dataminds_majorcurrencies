"""
Populate Initial Data for FX Alpha Platform
Creates sample data to demonstrate the system
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django
from django.conf import settings
from core.database import DatabaseManager
import logging

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

logger = logging.getLogger(__name__)


class InitialDataPopulator:
    """Populates databases with initial sample data"""
    
    def __init__(self):
        self.pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD']
        self.timeframes = ['M1', 'M5', 'M15', 'H1', 'H4', 'D1']
        
        # Initial prices for realistic data generation
        self.base_prices = {
            'EURUSD': 1.0850,
            'GBPUSD': 1.2650,
            'USDJPY': 149.50,
            'USDCHF': 0.8820,
            'AUDUSD': 0.6520,
            'USDCAD': 1.3580
        }
    
    def generate_ohlcv_data(self, pair: str, timeframe: str, bars: int = 1000):
        """Generate realistic OHLCV data"""
        base_price = self.base_prices[pair]
        
        # Time intervals in minutes
        intervals = {
            'M1': 1, 'M5': 5, 'M15': 15, 'H1': 60, 'H4': 240, 'D1': 1440
        }
        interval_minutes = intervals[timeframe]
        
        data = []
        current_time = datetime.now() - timedelta(minutes=bars * interval_minutes)
        current_price = base_price
        
        for i in range(bars):
            # Generate realistic price movement
            change = np.random.normal(0, 0.0001)  # Small random changes
            volatility = np.random.uniform(0.0005, 0.002)  # Volatility
            
            open_price = current_price
            high_price = open_price + abs(np.random.normal(0, volatility))
            low_price = open_price - abs(np.random.normal(0, volatility))
            close_price = open_price + change
            volume = np.random.randint(100000, 10000000)
            
            # Ensure OHLC logic
            high_price = max(high_price, open_price, close_price)
            low_price = min(low_price, open_price, close_price)
            
            data.append({
                'timestamp': current_time,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })
            
            current_price = close_price
            current_time += timedelta(minutes=interval_minutes)
        
        return pd.DataFrame(data)
    
    def populate_influxdb(self):
        """Populate InfluxDB with OHLCV data"""
        logger.info("Populating InfluxDB with OHLCV data...")
        
        try:
            with DatabaseManager.get_influx_client() as client:
                write_api = client.write_api()
                bucket = os.getenv('INFLUX_BUCKET', 'forex_data')
                
                for pair in self.pairs:
                    for timeframe in ['H1', 'H4', 'D1']:  # Start with key timeframes
                        df = self.generate_ohlcv_data(pair, timeframe, bars=500)
                        
                        points = []
                        for _, row in df.iterrows():
                            point = {
                                "measurement": "ohlcv",
                                "tags": {
                                    "symbol": pair,
                                    "timeframe": timeframe
                                },
                                "fields": {
                                    "open": float(row['open']),
                                    "high": float(row['high']),
                                    "low": float(row['low']),
                                    "close": float(row['close']),
                                    "volume": float(row['volume'])  # Convert to float for consistency
                                },
                                "time": row['timestamp']
                            }
                            points.append(point)
                        
                        write_api.write(bucket=bucket, record=points)
                        logger.info(f"Populated {len(points)} points for {pair} {timeframe}")
                
        except Exception as e:
            logger.error(f"Error populating InfluxDB: {e}")
    
    def populate_postgresql(self):
        """Populate PostgreSQL with sample data"""
        logger.info("Populating PostgreSQL with sample data...")
        
        try:
            with DatabaseManager.get_postgres_connection() as conn:
                cursor = conn.cursor()
                
                # Sample macro data
                macro_data = [
                    ('DFF', 'USD', 5.25, datetime.now().date(), 'DFF'),
                    ('DEXUSEU', 'EUR', 1.0850, datetime.now().date(), 'DEXUSEU'),
                    ('DEXUSUK', 'GBP', 1.2650, datetime.now().date(), 'DEXUSUK'),
                    ('DEXJPUS', 'JPY', 149.50, datetime.now().date(), 'DEXJPUS'),
                    ('DEXCHUS', 'CHF', 0.8820, datetime.now().date(), 'DEXCHUS'),
                    ('DEXUSAL', 'AUD', 0.6520, datetime.now().date(), 'DEXUSAL'),
                    ('DEXUSCA', 'CAD', 1.3580, datetime.now().date(), 'DEXUSCA'),
                ]
                
                cursor.executemany("""
                    INSERT INTO macro_indicators 
                    (indicator_name, currency, value, date, series_id, source, created_at)
                    VALUES (%s, %s, %s, %s, %s, 'Sample', %s)
                    ON CONFLICT DO NOTHING
                """, [(row[0], row[1], row[2], row[3], row[4], datetime.now()) for row in macro_data])
                
                # Sample news articles
                news_data = [
                    ("ECB maintains interest rates despite inflation concerns", "European Central Bank held rates steady at 4.0%, citing economic uncertainty.", "Sample News", "https://example.com/ecb-rates", datetime.now() - timedelta(hours=2), ['EUR', 'USD']),
                    ("Fed signals potential rate cuts in 2024", "Federal Reserve officials indicated possible rate reductions later this year.", "Sample News", "https://example.com/fed-signals", datetime.now() - timedelta(hours=4), ['USD']),
                    ("Bank of Japan maintains ultra-loose policy", "BOJ continues with negative interest rates despite inflation pressure.", "Sample News", "https://example.com/boj-policy", datetime.now() - timedelta(hours=6), ['JPY', 'USD']),
                    ("UK GDP shows stronger than expected growth", "UK economy grew 0.3% in Q2, beating expectations of 0.1%.", "Sample News", "https://example.com/uk-gdp", datetime.now() - timedelta(hours=8), ['GBP', 'USD']),
                    ("Swiss franc strengthens amid safe-haven demand", "Investors flock to CHF as global markets show volatility.", "Sample News", "https://example.com/chf-safe", datetime.now() - timedelta(hours=10), ['CHF', 'EUR']),
                ]
                
                cursor.executemany("""
                    INSERT INTO news_articles 
                    (title, content, source, url, published_at, currencies, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, [(row[0], row[1], row[2], row[3], row[4], row[5], datetime.now()) for row in news_data])
                
                # Sample trading signals
                signal_data = []
                for pair in self.pairs:
                    for i in range(10):  # 10 sample signals per pair
                        direction = np.random.choice(['BUY', 'SELL', 'NEUTRAL'])
                        confidence = np.random.uniform(0.5, 0.95)
                        
                        signal_data.append((
                            pair,
                            direction,
                            confidence,
                            f'{{"technical": "{np.random.choice(["BUY", "SELL", "NEUTRAL"])}", "macro": "{np.random.choice(["BUY", "SELL", "NEUTRAL"])}"}}',
                            f"Sample signal for {pair} based on technical indicators",
                            datetime.now() - timedelta(hours=i*6)
                        ))
                
                cursor.executemany("""
                    INSERT INTO trading_signals_log 
                    (pair, direction, confidence, agent_votes, reasoning, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, signal_data)
                
                conn.commit()
                logger.info(f"Populated PostgreSQL with {len(macro_data)} indicators, {len(news_data)} articles, {len(signal_data)} signals")
                
        except Exception as e:
            logger.error(f"Error populating PostgreSQL: {e}")
    
    def populate_all(self):
        """Populate all databases"""
        logger.info("Starting initial data population...")
        
        self.populate_influxdb()
        self.populate_postgresql()
        
        logger.info("Initial data population complete!")


if __name__ == "__main__":
    populator = InitialDataPopulator()
    populator.populate_all()
