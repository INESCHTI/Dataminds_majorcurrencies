# File: import_all_data.py
# Complete data import script - imports all necessary data

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import psycopg2
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv

load_dotenv()

# InfluxDB Configuration
INFLUXDB_URL = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN')
INFLUXDB_ORG = os.getenv('INFLUXDB_ORG')
INFLUXDB_BUCKET = os.getenv('INFLUXDB_BUCKET')

# PostgreSQL Configuration
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')

# =============================================================================
# PART 1: FOREX DATA (Synthetic realistic data)
# =============================================================================

PAIRS = {
    'EURUSD': 1.0850,
    'USDJPY': 149.50,
    'GBPUSD': 1.2650,
    'USDCHF': 0.8750
}

TIMEFRAMES = {
    '1H': {'hours': 1, 'days_back': 90},
    '4H': {'hours': 4, 'days_back': 180},
    '1D': {'hours': 24, 'days_back': 365}
}

def generate_forex_data(symbol, start_price, timeframe_hours, num_candles):
    """Generate realistic synthetic OHLC data"""
    data = []
    current_time = datetime.now() - timedelta(hours=timeframe_hours * num_candles)
    current_price = start_price
    
    # Volatility based on symbol
    volatility = 0.001 if 'JPY' in symbol else 0.0002
    
    for i in range(num_candles):
        # Random walk
        change = np.random.normal(0, volatility * current_price)
        current_price += change
        
        # Generate OHLC
        daily_range = abs(np.random.normal(0, volatility * current_price * 2))
        open_price = current_price + np.random.uniform(-daily_range/4, daily_range/4)
        high_price = open_price + abs(np.random.uniform(0, daily_range))
        low_price = open_price - abs(np.random.uniform(0, daily_range))
        close_price = np.random.uniform(low_price, high_price)
        volume = int(np.random.uniform(5000, 50000))
        
        data.append({
            'time': current_time,
            'open': round(open_price, 5 if 'JPY' not in symbol else 3),
            'high': round(high_price, 5 if 'JPY' not in symbol else 3),
            'low': round(low_price, 5 if 'JPY' not in symbol else 3),
            'close': round(close_price, 5 if 'JPY' not in symbol else 3),
            'volume': volume
        })
        
        current_time += timedelta(hours=timeframe_hours)
        current_price = close_price
    
    return pd.DataFrame(data)

def import_forex_data():
    """Import all forex data to InfluxDB"""
    print("\n" + "=" * 70)
    print("IMPORTING FOREX DATA TO INFLUXDB")
    print("=" * 70)
    
    client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    write_api = client.write_api(write_options=SYNCHRONOUS)
    
    total_points = 0
    
    for symbol, start_price in PAIRS.items():
        for timeframe, config in TIMEFRAMES.items():
            print(f"\n📊 {symbol} {timeframe}...")
            
            hours_back = config['days_back'] * 24
            num_candles = hours_back // config['hours']
            
            # Generate data
            df = generate_forex_data(symbol, start_price, config['hours'], num_candles)
            
            # Create points
            points = []
            for _, row in df.iterrows():
                point = (
                    Point("forex_prices")
                    .tag("symbol", symbol)
                    .tag("timeframe", timeframe)
                    .field("open", float(row['open']))
                    .field("high", float(row['high']))
                    .field("low", float(row['low']))
                    .field("close", float(row['close']))
                    .field("volume", int(row['volume']))
                    .time(row['time'])
                )
                points.append(point)
            
            # Write in batches
            batch_size = 5000
            for i in range(0, len(points), batch_size):
                batch = points[i:i+batch_size]
                write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=batch)
            
            total_points += len(points)
            print(f"   ✅ Wrote {len(points):,} points")
    
    client.close()
    print(f"\n✅ Total forex points: {total_points:,}")
    return total_points

# =============================================================================
# PART 2: ECONOMIC DATA (Real data from FRED API or synthetic)
# =============================================================================

def generate_economic_data():
    """Generate synthetic economic indicator data"""
    print("\n" + "=" * 70)
    print("IMPORTING ECONOMIC DATA TO POSTGRESQL")
    print("=" * 70)
    
    # Force UTF-8 encoding for Windows
    import sys
    if sys.platform == 'win32':
        import locale
        locale.setlocale(locale.LC_ALL, 'C')
    
    indicators = {
        'CPIAUCSL': {'name': 'US CPI', 'start': 200.0, 'trend': 0.002},
        'UNRATE': {'name': 'US Unemployment Rate', 'start': 3.8, 'trend': 0.0},
        'FEDFUNDS': {'name': 'Federal Funds Rate', 'start': 5.25, 'trend': 0.0},
        'GDP': {'name': 'US GDP', 'start': 25000.0, 'trend': 0.005},
        'DGS10': {'name': 'US 10Y Treasury', 'start': 4.2, 'trend': 0.0},
    }
    
    data = []
    start_date = datetime.now() - timedelta(days=365*2)
    
    for series_id, info in indicators.items():
        print(f"\n📊 {info['name']}...")
        current_value = info['start']
        current_date = start_date
        
        # Generate monthly data
        for i in range(24):
            # Add trend + noise
            current_value = current_value * (1 + info['trend']) + np.random.normal(0, abs(current_value * 0.01))
            
            data.append({
                'date': current_date.date(),
                'series_id': series_id,
                'indicator_name': info['name'],
                'value': round(current_value, 2)
            })
            
            current_date += timedelta(days=30)
    
    df = pd.DataFrame(data)
    
    # Write to PostgreSQL using URI format
    try:
        import urllib.parse
        password_encoded = urllib.parse.quote_plus('forex_pass_2026')
        conn_uri = f'postgresql://forex_user:{password_encoded}@localhost:5432/forex_metadata'
        conn = psycopg2.connect(conn_uri)
        conn.set_client_encoding('UTF8')
        cursor = conn.cursor()
    except Exception as e:
        print(f"Connection error: {e}")
        raise
    
    values = [
        (row['date'], row['series_id'], row['indicator_name'], row['value'])
        for _, row in df.iterrows()
    ]
    
    execute_values(
        cursor,
        """
        INSERT INTO economic_indicators (date, series_id, indicator_name, value)
        VALUES %s
        ON CONFLICT (date, series_id) DO UPDATE
        SET value = EXCLUDED.value
        """,
        values
    )
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"\n✅ Imported {len(df)} economic indicators")
    return len(df)

# =============================================================================
# PART 3: NEWS DATA (Synthetic news articles)
# =============================================================================

def generate_news_data():
    """Generate synthetic news articles"""
    print("\n" + "=" * 70)
    print("IMPORTING NEWS DATA TO POSTGRESQL")
    print("=" * 70)
    
    # Force UTF-8 encoding for Windows
    import sys
    if sys.platform == 'win32':
        import locale
        locale.setlocale(locale.LC_ALL, 'C')
    
    news_templates = [
        {"title": "EUR/USD rises on strong European data", "source": "Reuters", "currencies": ["EUR"]},
        {"title": "Federal Reserve signals potential rate cuts", "source": "Bloomberg", "currencies": ["USD"]},
        {"title": "Bank of Japan maintains ultra-loose policy", "source": "Reuters", "currencies": ["JPY"]},
        {"title": "GBP strengthens on positive UK employment data", "source": "Financial Times", "currencies": ["GBP"]},
        {"title": "Swiss franc gains safe-haven status", "source": "Bloomberg", "currencies": ["CHF"]},
        {"title": "ECB President discusses inflation outlook", "source": "Reuters", "currencies": ["EUR"]},
        {"title": "US dollar weakens on soft economic indicators", "source": "CNBC", "currencies": ["USD"]},
        {"title": "Forex markets react to global trade tensions", "source": "Bloomberg", "currencies": ["USD", "EUR"]},
        {"title": "Japanese Yen pressured by yield differentials", "source": "Financial Times", "currencies": ["JPY"]},
        {"title": "British Pound volatile ahead of BOE meeting", "source": "Reuters", "currencies": ["GBP"]},
    ]
    
    articles = []
    start_date = datetime.now() - timedelta(days=90)
    
    for i in range(100):
        template = news_templates[i % len(news_templates)]
        pub_date = start_date + timedelta(days=i*0.9)
        
        articles.append({
            'url': f"https://example.com/article-{i+1}",
            'title': template['title'],
            'content': f"Article content for {template['title']}. Lorem ipsum dolor sit amet...",
            'source': template['source'],
            'published_at': pub_date,
            'currencies': template['currencies']
        })
    
    # Write to PostgreSQL using URI format
    try:
        import urllib.parse
        password_encoded = urllib.parse.quote_plus('forex_pass_2026')
        conn_uri = f'postgresql://forex_user:{password_encoded}@localhost:5432/forex_metadata'
        conn = psycopg2.connect(conn_uri)
        conn.set_client_encoding('UTF8')
        cursor = conn.cursor()
    except Exception as e:
        print(f"Connection error: {e}")
        raise
    
    for article in articles:
        cursor.execute(
            """
            INSERT INTO news_articles (url, title, content, source, published_at, currencies)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO NOTHING
            """,
            (article['url'], article['title'], article['content'], 
             article['source'], article['published_at'], article['currencies'])
        )
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"\n✅ Imported {len(articles)} news articles")
    return len(articles)

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    print("\n" + "=" * 70)
    print("FOREX ALPHA DATA - COMPLETE IMPORT")
    print("=" * 70)
    print("\nThis will populate all databases with realistic data...")
    
    try:
        # Import forex data
        forex_count = import_forex_data()
        
        # Import economic data
        econ_count = generate_economic_data()
        
        # Import news data
        news_count = generate_news_data()
        
        # Summary
        print("\n" + "=" * 70)
        print("✅ IMPORT COMPLETE!")
        print("=" * 70)
        print(f"📊 Forex data points: {forex_count:,}")
        print(f"📈 Economic indicators: {econ_count:,}")
        print(f"📰 News articles: {news_count:,}")
        print("\n🎯 Refresh your dashboard to see the data!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
