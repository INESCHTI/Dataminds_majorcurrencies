import sys
import os

# Fix encoding BEFORE anything else
os.environ['PGPASSFILE'] = ''
os.environ['PGSYSCONFDIR'] = ''
os.environ['PGSERVICEFILE'] = ''

from fredapi import Fred
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

# Configuration
FRED_API_KEY = os.getenv('FRED_API_KEY')

# Economic indicators to fetch
INDICATORS = {
    'CPIAUCSL': 'US CPI',
    'UNRATE': 'US Unemployment Rate',
    'FEDFUNDS': 'Federal Funds Rate',
    'GDP': 'US GDP',
    'DEXUSEU': 'EUR/USD Exchange Rate',
    'DEXJPUS': 'USD/JPY Exchange Rate',
    'DEXUSUK': 'GBP/USD Exchange Rate',
    'DEXSZUS': 'USD/CHF Exchange Rate',
    'DGS10': 'US 10Y Treasury',
    'T10YIE': 'US 10Y Inflation Expectations',
}

def fetch_fred_data():
    print("=" * 60)
    print("FRED DATA ACQUISITION")
    print("=" * 60)

    fred = Fred(api_key=FRED_API_KEY)
    all_data = []

    for series_id, name in INDICATORS.items():
        print(f"\nFetching {name} ({series_id})...")

        try:
            data = fred.get_series(series_id, observation_start='2015-01-01')

            df = pd.DataFrame({
                'date': data.index,
                'value': data.values,
                'series_id': series_id,
                'indicator_name': name
            })

            print(f"   Retrieved {len(df):,} observations")
            print(f"   From {df['date'].min()} to {df['date'].max()}")

            all_data.append(df)

        except Exception as e:
            print(f"   Error: {e}")

    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        print(f"\nTotal observations: {len(combined):,}")
        return combined

    return None

def write_to_postgres(df):
    print("\nWriting to PostgreSQL...")

    try:
        # Use DSN string to avoid any encoding issues with kwargs
        dsn = "host=localhost port=5432 dbname=forex_metadata user=forex_user password=forex_pass_2026"
        conn = psycopg2.connect(dsn)
    except Exception as e:
        print(f"Connection failed: {e}")
        raise

    cursor = conn.cursor()

    try:
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
        print(f"Wrote {len(values):,} records to PostgreSQL")

    except Exception as e:
        conn.rollback()
        print(f"Write failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def main():
    df = fetch_fred_data()

    if df is not None and len(df) > 0:
        write_to_postgres(df)
        print("\n" + "=" * 60)
        print("FRED DATA ACQUISITION COMPLETE")
        print("=" * 60)
    else:
        print("\nNo data collected")

if __name__ == "__main__":
    main()