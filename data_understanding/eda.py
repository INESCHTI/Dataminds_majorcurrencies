"""
Unified Exploratory Data Analysis & Data Quality Assessment
Covers: MT5 Price Data, FRED Economic Data, News Data
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import psycopg2
from psycopg2.extras import RealDictCursor
from influxdb_client import InfluxDBClient
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta
from collections import Counter
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# ─── Configuration ────────────────────────────────────────────────────────────
env_path = Path(__file__).parent.parent / 'config' / '.env'
load_dotenv(dotenv_path=env_path, override=True)

POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_PORT = os.getenv('POSTGRES_PORT')
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')

INFLUXDB_URL = os.getenv('INFLUXDB_URL')
INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN')
INFLUXDB_ORG = os.getenv('INFLUXDB_ORG')
INFLUXDB_BUCKET = os.getenv('INFLUXDB_BUCKET')

PAIRS = ['EURUSD', 'USDJPY', 'GBPUSD', 'USDCHF']
TIMEFRAMES = ['1H', '4H', '1D']

OUTPUT_DIR = Path(__file__).parent.parent / 'data_understanding_outputs'
PLOTS_DIR = OUTPUT_DIR / 'plots'
EDA_DIR = OUTPUT_DIR / 'eda'

plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


# ─── Database Connections ─────────────────────────────────────────────────────

def connect_influxdb():
    """Connect to InfluxDB"""
    client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    return client

def connect_postgres():
    """Connect to PostgreSQL"""
    conn = psycopg2.connect(
        host=POSTGRES_HOST, port=POSTGRES_PORT,
        dbname=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD
    )
    return conn


# ═══════════════════════════════════════════════════════════════════════════════
# MT5 PRICE DATA — EDA & QUALITY
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_price_data(client, symbol, timeframe):
    """Fetch price data for a symbol and timeframe"""
    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: -5y)
      |> filter(fn: (r) => r._measurement == "forex_prices")
      |> filter(fn: (r) => r.symbol == "{symbol}")
      |> filter(fn: (r) => r.timeframe == "{timeframe}")
      |> sort(columns: ["_time"])
    '''
    query_api = client.query_api()
    result = query_api.query(query)

    data = []
    for table in result:
        for record in table.records:
            data.append({
                'time': record.get_time(),
                'field': record.get_field(),
                'value': record.get_value(),
            })

    df = pd.DataFrame(data)
    if len(df) == 0:
        return None

    df_pivot = df.pivot_table(index='time', columns='field', values='value', aggfunc='first')
    df_pivot.columns = ['close', 'high', 'low', 'open', 'volume']
    df_pivot = df_pivot[['open', 'high', 'low', 'close', 'volume']].astype(float)
    df_pivot.index.name = 'time'
    return df_pivot


def mt5_basic_statistics(df, symbol, timeframe):
    """Calculate and print basic statistics for MT5 price data"""
    print(f"\n📊 BASIC STATISTICS: {symbol} {timeframe}")
    print("=" * 70)

    print(f"\n📈 Data Shape:")
    print(f"   Total candles: {len(df):,}")
    print(f"   Date range: {df.index.min()} to {df.index.max()}")
    print(f"   Duration: {(df.index.max() - df.index.min()).days} days")

    print(f"\n📊 Price Statistics (OHLC):")
    for col in ['open', 'high', 'low', 'close']:
        print(f"   {col.capitalize():5s} - Mean: {df[col].mean():.5f}, Min: {df[col].min():.5f}, Max: {df[col].max():.5f}")

    df['spread'] = df['high'] - df['low']
    df['returns'] = df['close'].pct_change() * 100

    print(f"\n📊 Returns Analysis:")
    print(f"   Mean: {df['returns'].mean():.5f}%, Std: {df['returns'].std():.5f}%")
    print(f"   Skewness: {df['returns'].skew():.5f}, Kurtosis: {df['returns'].kurtosis():.5f}")

    print(f"\n📊 Volume — Mean: {df['volume'].mean():.0f}, Max: {df['volume'].max():.0f}")

    print(f"\n📊 Missing Data:")
    for col in ['open', 'high', 'low', 'close', 'volume']:
        missing = df[col].isna().sum()
        if missing > 0:
            print(f"   {col}: {missing} missing")


def mt5_quality_check(df, symbol, timeframe):
    """Check for data quality issues in MT5 price data"""
    issues = []
    df['spread'] = df['high'] - df['low']
    df['returns'] = df['close'].pct_change() * 100

    if df['close'].isna().sum() > 0:
        issues.append(f"Missing close prices: {df['close'].isna().sum()}")
    if (df['close'] <= 0).any():
        issues.append(f"Zero or negative close prices: {(df['close'] <= 0).sum()}")
    illogical = (df['high'] < df['low']).sum()
    if illogical > 0:
        issues.append(f"High < Low violations: {illogical}")
    extreme_spreads = ((df['spread'] / df['open']) > 0.02).sum()
    if extreme_spreads > 0:
        issues.append(f"Extreme spreads (>2%): {extreme_spreads}")
    extreme_moves = (abs(df['returns']) > 10).sum()
    if extreme_moves > 0:
        issues.append(f"Extreme moves (>10%): {extreme_moves}")

    if issues:
        print(f"\n⚠️  QUALITY ISSUES for {symbol} {timeframe}:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print(f"\n✅ QUALITY OK for {symbol} {timeframe}")
        return True


def run_mt5_eda(client):
    """Run full EDA for MT5 price data"""
    print("\n\n" + "=" * 70)
    print("🔍 EDA — MT5 PRICE DATA")
    print("=" * 70)

    os.makedirs(PLOTS_DIR, exist_ok=True)
    os.makedirs(EDA_DIR, exist_ok=True)
    summary_data = []

    for symbol in PAIRS:
        print(f"\n{'=' * 70}")
        print(f"🔄 Processing {symbol}")
        print(f"{'=' * 70}")

        for timeframe in TIMEFRAMES:
            print(f"\n📥 Fetching {symbol} {timeframe}...")
            try:
                df = fetch_price_data(client, symbol, timeframe)
                if df is None or len(df) == 0:
                    print(f"   ❌ No data found")
                    continue

                print(f"   ✅ Fetched {len(df):,} candles")
                mt5_basic_statistics(df, symbol, timeframe)
                quality_ok = mt5_quality_check(df, symbol, timeframe)

                # --- Plots ---
                df['returns'] = df['close'].pct_change() * 100

                # Price series
                fig, axes = plt.subplots(3, 1, figsize=(14, 10))
                axes[0].plot(df.index, df['close'], linewidth=1.5, color='#1f77b4')
                axes[0].fill_between(df.index, df['low'], df['high'], alpha=0.2, color='#1f77b4')
                axes[0].set_title(f'{symbol} {timeframe} - Close Price', fontweight='bold')
                axes[0].set_ylabel('Price'); axes[0].grid(True, alpha=0.3)
                axes[1].bar(df.index, df['returns'], width=1,
                            color=['#2ca02c' if x > 0 else '#d62728' for x in df['returns']], alpha=0.7)
                axes[1].axhline(y=0, color='black', linestyle='-', linewidth=0.5)
                axes[1].set_title(f'{symbol} {timeframe} - Returns (%)', fontweight='bold')
                axes[1].set_ylabel('Return %'); axes[1].grid(True, alpha=0.3)
                axes[2].bar(df.index, df['volume'], width=1, color='#ff7f0e', alpha=0.7)
                axes[2].set_title(f'{symbol} {timeframe} - Volume', fontweight='bold')
                axes[2].set_ylabel('Volume'); axes[2].grid(True, alpha=0.3)
                plt.tight_layout()
                plt.savefig(PLOTS_DIR / f'{symbol}_{timeframe}_price_series.png', dpi=100, bbox_inches='tight')
                plt.close()

                # Returns distribution
                fig, axes = plt.subplots(1, 2, figsize=(14, 5))
                axes[0].hist(df['returns'].dropna(), bins=100, color='#1f77b4', alpha=0.7, edgecolor='black')
                axes[0].axvline(df['returns'].mean(), color='red', linestyle='--', linewidth=2)
                axes[0].set_title(f'{symbol} {timeframe} - Returns Distribution', fontweight='bold')
                stats.probplot(df['returns'].dropna(), dist="norm", plot=axes[1])
                axes[1].set_title(f'{symbol} {timeframe} - Q-Q Plot', fontweight='bold')
                plt.tight_layout()
                plt.savefig(PLOTS_DIR / f'{symbol}_{timeframe}_returns_dist.png', dpi=100, bbox_inches='tight')
                plt.close()

                print(f"   📊 Plots saved to {PLOTS_DIR}")

                summary_data.append({
                    'Symbol': symbol, 'Timeframe': timeframe, 'Candles': len(df),
                    'Date_Range': f"{df.index.min().date()} to {df.index.max().date()}",
                    'Avg_Price': df['close'].mean(),
                    'Std_Return': df['close'].pct_change().std() * 100,
                    'Quality': 'OK' if quality_ok else 'ISSUES'
                })
            except Exception as e:
                print(f"   ❌ Error: {e}")

    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv(EDA_DIR / 'eda_summary_mt5.csv', index=False)
        print(f"\n✅ MT5 EDA Summary saved to {EDA_DIR / 'eda_summary_mt5.csv'}")

    return summary_data


# ═══════════════════════════════════════════════════════════════════════════════
# FRED ECONOMIC DATA — EDA & QUALITY
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_fred_indicators(conn):
    """Fetch all economic indicators from database"""
    query = """
    SELECT date, series_id, indicator_name, value
    FROM economic_indicators ORDER BY date ASC
    """
    df = pd.read_sql(query, conn)
    df['date'] = pd.to_datetime(df['date'])
    return df


def run_fred_eda(conn):
    """Run full EDA for FRED economic data"""
    print("\n\n" + "=" * 70)
    print("🔍 EDA — FRED ECONOMIC DATA")
    print("=" * 70)

    os.makedirs(PLOTS_DIR, exist_ok=True)
    os.makedirs(EDA_DIR, exist_ok=True)

    df = fetch_fred_indicators(conn)
    print(f"\n✅ Fetched {len(df):,} records")

    # Statistics
    print(f"\n📈 Data Overview:")
    print(f"   Total records: {len(df):,}")
    print(f"   Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    print(f"   Indicators: {df['indicator_name'].nunique()}")
    print(f"   Missing values: {df['value'].isna().sum()}")

    for indicator in df['indicator_name'].unique():
        subset = df[df['indicator_name'] == indicator]
        print(f"\n   {indicator}:")
        print(f"      Records: {len(subset):,}, Mean: {subset['value'].mean():.4f}")
        print(f"      Range: {subset['value'].min():.4f} — {subset['value'].max():.4f}")

    # Plots — time series + distributions
    for indicator in df['indicator_name'].unique():
        subset = df[df['indicator_name'] == indicator].sort_values('date')
        safe_name = indicator.replace('/', '_').replace(' ', '_')

        fig, ax = plt.subplots(figsize=(14, 6))
        ax.plot(subset['date'], subset['value'], linewidth=2, color='#1f77b4', marker='o', markersize=3)
        ax.fill_between(subset['date'], subset['value'], alpha=0.3, color='#1f77b4')
        ax.set_title(f'{indicator} - Time Series', fontsize=14, fontweight='bold')
        ax.set_xlabel('Date'); ax.set_ylabel('Value'); ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45); plt.tight_layout()
        plt.savefig(PLOTS_DIR / f'FRED_{safe_name}_timeseries.png', dpi=100, bbox_inches='tight')
        plt.close()

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        axes[0].hist(subset['value'].dropna(), bins=50, color='#1f77b4', alpha=0.7, edgecolor='black')
        axes[0].axvline(subset['value'].mean(), color='red', linestyle='--', linewidth=2)
        axes[0].set_title(f'{indicator} - Distribution', fontweight='bold')
        axes[1].boxplot(subset['value'].dropna(), vert=True)
        axes[1].set_title(f'{indicator} - Box Plot', fontweight='bold')
        plt.tight_layout()
        plt.savefig(PLOTS_DIR / f'FRED_{safe_name}_distribution.png', dpi=100, bbox_inches='tight')
        plt.close()

    # Correlations
    pivot_df = df.pivot_table(index='date', columns='indicator_name', values='value')
    corr_matrix = pivot_df.corr()

    fig, ax = plt.subplots(figsize=(12, 10))
    sns.heatmap(corr_matrix, annot=True, fmt='.3f', cmap='coolwarm', center=0,
                square=True, linewidths=1, ax=ax)
    ax.set_title('Economic Indicators — Correlation Matrix', fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right'); plt.tight_layout()
    plt.savefig(PLOTS_DIR / 'FRED_correlation_matrix.png', dpi=100, bbox_inches='tight')
    plt.close()

    # Save summaries
    summary_stats = []
    for indicator in df['indicator_name'].unique():
        subset = df[df['indicator_name'] == indicator]
        summary_stats.append({
            'Indicator': indicator, 'Records': len(subset),
            'Mean': subset['value'].mean(), 'Std': subset['value'].std(),
            'Min': subset['value'].min(), 'Max': subset['value'].max(),
            'Date_Range': f"{subset['date'].min().date()} to {subset['date'].max().date()}"
        })

    pd.DataFrame(summary_stats).to_csv(EDA_DIR / 'eda_summary_fred.csv', index=False)
    corr_matrix.to_csv(EDA_DIR / 'eda_correlations_fred.csv')
    print(f"\n✅ FRED EDA complete — saved to {EDA_DIR}")


# ═══════════════════════════════════════════════════════════════════════════════
# NEWS DATA — EDA & QUALITY
# ═══════════════════════════════════════════════════════════════════════════════

def run_news_eda(conn):
    """Run full EDA for news data"""
    print("\n\n" + "=" * 70)
    print("🔍 EDA — NEWS DATA")
    print("=" * 70)

    os.makedirs(PLOTS_DIR, exist_ok=True)
    os.makedirs(EDA_DIR, exist_ok=True)

    query = """
    SELECT article_id, url, title, content, source, published_at, currencies, scraped_at
    FROM news_articles ORDER BY published_at DESC
    """
    df = pd.read_sql(query, conn)
    df['published_at'] = pd.to_datetime(df['published_at'], utc=True)
    df['scraped_at'] = pd.to_datetime(df['scraped_at'], utc=True)

    if len(df) == 0:
        print("❌ No news articles found")
        return

    print(f"\n✅ Fetched {len(df):,} articles")
    print(f"   Sources: {df['source'].nunique()}")
    print(f"   Unique URLs: {df['url'].nunique()}")

    df['title_length'] = df['title'].str.len()
    df['content_length'] = df['content'].str.len()

    print(f"\n📊 Content Stats:")
    print(f"   Title — Mean: {df['title_length'].mean():.0f}, Max: {df['title_length'].max():.0f}")
    print(f"   Content — Mean: {df['content_length'].mean():.0f}, Max: {df['content_length'].max():.0f}")

    # Currency coverage
    all_currencies = []
    for currencies in df['currencies']:
        if currencies is not None:
            if isinstance(currencies, list):
                all_currencies.extend(currencies)
            elif isinstance(currencies, str):
                cleaned = currencies.strip('{}').split(',')
                all_currencies.extend([c.strip() for c in cleaned if c.strip()])

    if all_currencies:
        currency_counts = Counter(all_currencies)
        print(f"\n📊 Currency Coverage:")
        for currency, count in currency_counts.most_common():
            print(f"   {currency}: {count} mentions ({count / len(df) * 100:.1f}%)")

    # Quality checks
    issues = []
    if df['title'].isna().sum() > 0: issues.append(f"Missing titles: {df['title'].isna().sum()}")
    if df['url'].duplicated().sum() > 0: issues.append(f"Duplicate URLs: {df['url'].duplicated().sum()}")

    if issues:
        print(f"\n⚠️  Quality Issues:")
        for i in issues: print(f"   - {i}")
    else:
        print(f"\n✅ News data quality: OK")

    # Plots
    source_counts = df['source'].value_counts()
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(source_counts.index, source_counts.values, color=plt.cm.Set3(np.linspace(0, 1, len(source_counts))),
           edgecolor='black', alpha=0.7)
    ax.set_title('News Articles by Source', fontsize=14, fontweight='bold')
    ax.set_xlabel('Source'); ax.set_ylabel('Count'); ax.grid(True, alpha=0.3, axis='y')
    plt.xticks(rotation=45, ha='right'); plt.tight_layout()
    plt.savefig(PLOTS_DIR / 'News_by_source.png', dpi=100, bbox_inches='tight')
    plt.close()

    if all_currencies:
        fig, ax = plt.subplots(figsize=(10, 6))
        currencies_list = list(currency_counts.keys())
        counts_list = list(currency_counts.values())
        ax.bar(currencies_list, counts_list, color=plt.cm.Set2(np.linspace(0, 1, len(currencies_list))),
               edgecolor='black', alpha=0.7)
        ax.set_title('Currency Mentions in News', fontsize=14, fontweight='bold')
        ax.set_xlabel('Currency'); ax.set_ylabel('Mentions'); ax.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        plt.savefig(PLOTS_DIR / 'News_currency_distribution.png', dpi=100, bbox_inches='tight')
        plt.close()

    # Save summary
    summary_stats = []
    for source in df['source'].unique():
        subset = df[df['source'] == source]
        summary_stats.append({
            'Source': source, 'Articles': len(subset),
            'Avg_Title_Length': subset['title'].str.len().mean(),
            'Avg_Content_Length': subset['content'].str.len().mean(),
        })
    pd.DataFrame(summary_stats).to_csv(EDA_DIR / 'eda_summary_news.csv', index=False)
    print(f"\n✅ News EDA complete — saved to {EDA_DIR}")


# ═══════════════════════════════════════════════════════════════════════════════
# DATA QUALITY ASSESSMENT (all sources)
# ═══════════════════════════════════════════════════════════════════════════════

def run_quality_assessment(influx_client, pg_conn):
    """Run comprehensive data quality assessment across all sources"""
    print("\n\n" + "=" * 70)
    print("🔍 DATA QUALITY ASSESSMENT")
    print("=" * 70)

    os.makedirs(EDA_DIR, exist_ok=True)
    all_issues = []

    # MT5 quality
    print("\n📊 MT5 Price Data Quality...")
    mt5_scores = []
    for symbol in PAIRS:
        for timeframe in TIMEFRAMES:
            try:
                df = fetch_price_data(influx_client, symbol, timeframe)
                if df is None or len(df) == 0:
                    all_issues.append(f"{symbol} {timeframe}: No data")
                    continue
                completeness = 100
                missing_pct = df.isna().sum().max() / len(df) * 100
                if missing_pct > 0: completeness -= min(missing_pct, 10)
                illogical = (df['high'] < df['low']).sum()
                if illogical > 0: completeness -= min(illogical / len(df) * 100, 10)
                mt5_scores.append({
                    'Symbol': symbol, 'Timeframe': timeframe,
                    'Records': len(df), 'Completeness_Score': completeness
                })
                status = "✅ EXCELLENT" if completeness == 100 else f"⚠️ {completeness:.1f}%"
                print(f"   {symbol} {timeframe}: {len(df):,} candles — {status}")
            except Exception as e:
                all_issues.append(f"{symbol} {timeframe}: {str(e)[:50]}")

    if mt5_scores:
        pd.DataFrame(mt5_scores).to_csv(EDA_DIR / 'data_quality_mt5.csv', index=False)

    # FRED quality
    print("\n📈 FRED Economic Data Quality...")
    try:
        query = """
        SELECT indicator_name, COUNT(*) as cnt,
               COUNT(CASE WHEN value IS NULL THEN 1 END) as nulls
        FROM economic_indicators GROUP BY indicator_name
        """
        fred_df = pd.read_sql(query, pg_conn)
        fred_scores = []
        for _, row in fred_df.iterrows():
            null_pct = row['nulls'] / row['cnt'] * 100 if row['cnt'] > 0 else 0
            completeness = 100 - min(null_pct, 10)
            fred_scores.append({
                'Indicator': row['indicator_name'],
                'Records': row['cnt'], 'Missing_Pct': null_pct,
                'Completeness_Score': completeness
            })
            status = "✅" if completeness == 100 else f"⚠️ {completeness:.1f}%"
            print(f"   {row['indicator_name']}: {row['cnt']} records — {status}")
        pd.DataFrame(fred_scores).to_csv(EDA_DIR / 'data_quality_fred.csv', index=False)
    except Exception as e:
        all_issues.append(f"FRED: {str(e)[:50]}")

    # News quality
    print("\n📰 News Data Quality...")
    try:
        query = """
        SELECT source, COUNT(*) as cnt, COUNT(DISTINCT url) as unique_urls
        FROM news_articles GROUP BY source
        """
        news_df = pd.read_sql(query, pg_conn)
        news_scores = []
        for _, row in news_df.iterrows():
            dupes = row['cnt'] - row['unique_urls']
            completeness = 100 - min((dupes / row['cnt'] * 100) if row['cnt'] > 0 else 0, 5)
            news_scores.append({
                'Source': row['source'], 'Articles': row['cnt'],
                'Unique_URLs': row['unique_urls'], 'Completeness_Score': completeness
            })
            status = "✅" if completeness == 100 else f"⚠️ {completeness:.1f}%"
            print(f"   {row['source']}: {row['cnt']} articles — {status}")
        pd.DataFrame(news_scores).to_csv(EDA_DIR / 'data_quality_news.csv', index=False)
    except Exception as e:
        all_issues.append(f"News: {str(e)[:50]}")

    print(f"\n✅ Quality assessment complete — {len(all_issues)} issues found")
    if all_issues:
        for issue in all_issues:
            print(f"   ⚠️ {issue}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("🔍 UNIFIED EDA & DATA QUALITY ASSESSMENT")
    print("=" * 70)

    influx_client = connect_influxdb()
    pg_conn = connect_postgres()

    print("\n✅ Connected to InfluxDB and PostgreSQL")

    run_mt5_eda(influx_client)
    run_fred_eda(pg_conn)
    run_news_eda(pg_conn)
    run_quality_assessment(influx_client, pg_conn)

    influx_client.close()
    pg_conn.close()

    print("\n\n" + "=" * 70)
    print("✅ ALL EDA & QUALITY CHECKS COMPLETE!")
    print("=" * 70)
    print(f"\n📁 Outputs saved to: {OUTPUT_DIR}")
    print(f"   📊 Plots: {PLOTS_DIR}")
    print(f"   📄 CSVs:  {EDA_DIR}")


if __name__ == "__main__":
    main()
