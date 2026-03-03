# File: generate_demo_data.py
# Generate synthetic forex data without MetaTrader

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
INFLUXDB_URL = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN')
INFLUXDB_ORG = os.getenv('INFLUXDB_ORG')
INFLUXDB_BUCKET = os.getenv('INFLUXDB_BUCKET')

# Currency pairs with realistic starting prices
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

def generate_ohlc_data(symbol, start_price, timeframe_hours, num_candles):
    """Generate realistic synthetic OHLC data"""
    print(f"\n📊 Generating {symbol} data...")
    
    data = []
    current_time = datetime.now() - timedelta(hours=timeframe_hours * num_candles)
    current_price = start_price
    
    # Volatility based on symbol
    volatility = 0.001 if 'JPY' in symbol else 0.0002
    
    for i in range(num_candles):
        # Generate random walk with realistic constraints
        change = np.random.normal(0, volatility * current_price)
        current_price += change
        
        # Generate OHLC
        daily_range = abs(np.random.normal(0, volatility * current_price * 2))
        
        open_price = current_price + np.random.uniform(-daily_range/4, daily_range/4)
        high_price = open_price + abs(np.random.uniform(0, daily_range))
        low_price = open_price - abs(np.random.uniform(0, daily_range))
        close_price = np.random.uniform(low_price, high_price)
        
        # Generate volume
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
    
    df = pd.DataFrame(data)
    print(f"   ✅ Generated {len(df):,} candles")
    print(f"   📅 From {df['time'].min()} to {df['time'].max()}")
    print(f"   💰 Price range: {df['low'].min():.5f} - {df['high'].max():.5f}")
    
    return df

def write_to_influxdb(df, symbol, timeframe):
    """Write data to InfluxDB"""
    print(f"   💾 Writing to InfluxDB...")
    
    client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    write_api = client.write_api(write_options=SYNCHRONOUS)
    
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
    
    try:
        # Write in batches of 5000
        batch_size = 5000
        for i in range(0, len(points), batch_size):
            batch = points[i:i+batch_size]
            write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=batch)
        
        print(f"   ✅ Wrote {len(points):,} points to InfluxDB")
    except Exception as e:
        print(f"   ❌ Write failed: {e}")
    finally:
        client.close()

def main():
    print("=" * 70)
    print("SYNTHETIC FOREX DATA GENERATOR")
    print("=" * 70)
    print("\n⚡ Generating realistic forex data without MetaTrader...")
    
    total_points = 0
    
    for symbol, start_price in PAIRS.items():
        for timeframe, config in TIMEFRAMES.items():
            # Calculate number of candles
            hours_back = config['days_back'] * 24
            num_candles = hours_back // config['hours']
            
            # Generate data
            df = generate_ohlc_data(symbol, start_price, config['hours'], num_candles)
            
            # Write to InfluxDB
            write_to_influxdb(df, symbol, timeframe)
            
            total_points += len(df)
    
    print("\n" + "=" * 70)
    print(f"✅ SUCCESS!")
    print(f"📊 Total points written: {total_points:,}")
    print(f"🎯 Pairs: {', '.join(PAIRS.keys())}")
    print(f"⏰ Timeframes: {', '.join(TIMEFRAMES.keys())}")
    print("=" * 70)

if __name__ == "__main__":
    main()
