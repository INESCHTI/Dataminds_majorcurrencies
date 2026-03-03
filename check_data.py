# File: check_data.py
# Quick script to check if data exists in databases

import os
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient
import psycopg2

load_dotenv()

print("=" * 60)
print("DATA AVAILABILITY CHECK")
print("=" * 60)

# Check InfluxDB
print("\n📊 InfluxDB Check:")
try:
    client = InfluxDBClient(
        url=os.getenv('INFLUXDB_URL'),
        token=os.getenv('INFLUXDB_TOKEN'),
        org=os.getenv('INFLUXDB_ORG')
    )
    query_api = client.query_api()
    
    query = f'''
    from(bucket: "{os.getenv('INFLUXDB_BUCKET')}")
        |> range(start: -365d)
        |> filter(fn: (r) => r["_measurement"] == "forex_prices")
        |> count()
    '''
    
    result = query_api.query(query)
    
    if result:
        print("   ✅ InfluxDB connection successful")
        for table in result:
            for record in table.records:
                print(f"   📈 Found {record.get_value()} forex price records")
    else:
        print("   ⚠️ No forex data found in InfluxDB")
    
    client.close()
except Exception as e:
    print(f"   ❌ InfluxDB error: {e}")

# Check PostgreSQL
print("\n🗄️ PostgreSQL Check:")
try:
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT'),
        dbname=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        client_encoding='utf8'
    )
    cursor = conn.cursor()
    
    # Check economic indicators
    cursor.execute("SELECT COUNT(*) FROM economic_indicators")
    count = cursor.fetchone()[0]
    print(f"   📊 Economic indicators: {count:,} records")
    
    # Check news articles
    cursor.execute("SELECT COUNT(*) FROM news_articles")
    count = cursor.fetchone()[0]
    print(f"   📰 News articles: {count:,} records")
    
    # Check economic events
    cursor.execute("SELECT COUNT(*) FROM economic_events")
    count = cursor.fetchone()[0]
    print(f"   📅 Economic events: {count:,} records")
    
    conn.close()
    print("   ✅ PostgreSQL connection successful")
except Exception as e:
    print(f"   ❌ PostgreSQL error: {e}")

print("\n" + "=" * 60)
