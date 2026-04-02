import os
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient
import psycopg2

load_dotenv()

print("VERIFYING DATA")

client = InfluxDBClient(
    url=os.getenv('INFLUXDB_URL'),
    token=os.getenv('INFLUXDB_TOKEN'),
    org=os.getenv('INFLUXDB_ORG')
)
query_api = client.query_api()

query = '''
from(bucket: "forex_data")
  |> range(start: -5y)
  |> filter(fn: (r) => r._measurement == "forex_prices")
  |> count()
'''

result = query_api.query(query)
total = 0
for table in result:
    for record in table.records:
        total += record.get_value()

print("Total candles:", total)

client.close()

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT'),
    dbname=os.getenv('POSTGRES_DB'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD')
)

cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM economic_indicators")
print("Economic records:", cursor.fetchone()[0])

cursor.execute("SELECT COUNT(*) FROM news_articles")
print("News records:", cursor.fetchone()[0])

cursor.close()
conn.close()
