import os
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient
import psycopg2
import MetaTrader5 as mt5

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

mt5_login = os.getenv('MT5_LOGIN')
mt5_password = os.getenv('MT5_PASSWORD')
mt5_server = os.getenv('MT5_SERVER')

if mt5_login and mt5_password and mt5_server:
    if mt5.initialize() and mt5.login(int(mt5_login), mt5_password, mt5_server):
        account = mt5.account_info()
        positions = mt5.positions_get() or []
        orders = mt5.orders_get() or []
        print("MT5 account login:", getattr(account, "login", None))
        print("MT5 balance:", getattr(account, "balance", None))
        print("MT5 equity:", getattr(account, "equity", None))
        print("MT5 free margin:", getattr(account, "margin_free", None))
        print("MT5 open positions:", len(positions))
        print("MT5 pending orders:", len(orders))
        mt5.shutdown()
    else:
        print("MT5 account snapshot unavailable:", mt5.last_error())
        mt5.shutdown()
else:
    print("MT5 account snapshot skipped: credentials not configured")

cursor.close()
conn.close()
