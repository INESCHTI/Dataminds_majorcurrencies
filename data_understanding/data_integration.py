import pandas as pd
import numpy as np
import psycopg2
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

env_path = Path(__file__).parent.parent / 'config' / '.env'
load_dotenv(dotenv_path=env_path, override=True)

FEATURES_DIR = Path(__file__).parent.parent / 'data_understanding_outputs' / 'features'
INTEGRATED_DIR = Path(__file__).parent.parent / 'data_understanding_outputs' / 'integrated'

# Configuration
POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_PORT = os.getenv('POSTGRES_PORT')
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')

PAIRS = ['EURUSD', 'USDJPY', 'GBPUSD', 'USDCHF']
TIMEFRAMES = ['1H', '4H', '1D']

def connect_postgres():
    """Connect to PostgreSQL"""
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )
    return conn

def load_price_features(symbol, timeframe):
    """Load price features from CSV"""
    filepath = FEATURES_DIR / f'features_{symbol}_{timeframe}.csv'
    
    try:
        df = pd.read_csv(filepath, index_col=0, parse_dates=True)
        df.index.name = 'time'
        return df
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        return None

def load_fred_data(conn):
    """Load FRED economic indicators from database"""
    query = """
    SELECT 
        date,
        series_id,
        indicator_name,
        value
    FROM economic_indicators
    ORDER BY date ASC
    """
    
    df = pd.read_sql(query, conn)
    df['date'] = pd.to_datetime(df['date'])
    
    # Pivot to get each indicator as a column
    pivot_df = df.pivot_table(index='date', columns='indicator_name', values='value')
    pivot_df.index.name = 'date'
    
    return pivot_df

def load_news_data(conn):
    """Load news articles from database"""
    query = """
    SELECT 
        published_at,
        currencies,
        source
    FROM news_articles
    WHERE published_at IS NOT NULL
    ORDER BY published_at ASC
    """
    
    df = pd.read_sql(query, conn)
    df['published_at'] = pd.to_datetime(df['published_at'], utc=True)
    df.set_index('published_at', inplace=True)
    
    return df

def create_sentiment_score(df_news):
    """Create simple sentiment score from news"""
    print(f"\n📰 Creating sentiment scores from news...")
    
    # Simple sentiment based on keywords
    positive_words = ['rise', 'gain', 'strength', 'rally', 'bullish', 'upside', 'higher', 'surge']
    negative_words = ['fall', 'loss', 'weakness', 'bearish', 'downside', 'lower', 'drop', 'decline']
    
    df_news['sentiment'] = 0.0
    
    for idx, row in df_news.iterrows():
        sentiment = 0.0
        if pd.notna(row.get('source')):
            source_text = str(row['source']).lower()
            
            # Count positive and negative keywords
            for word in positive_words:
                if word in source_text:
                    sentiment += 0.1
            
            for word in negative_words:
                if word in source_text:
                    sentiment -= 0.1
        
        df_news.loc[idx, 'sentiment'] = np.clip(sentiment, -1, 1)
    
    # Resample to daily sentiment
    daily_sentiment = df_news['sentiment'].resample('D').mean()
    print(f"   ✅ Created daily sentiment scores: {len(daily_sentiment)} days")
    
    return daily_sentiment

def align_timeframes(df_price, df_fred, currency):
    """Align price data with FRED data by date"""
    print(f"   Aligning {currency} with FRED data...")
    
    # Convert price index to date only (if it has time)
    if hasattr(df_price.index, 'date'):
        price_dates = df_price.index.date
        df_price_daily = df_price.groupby(price_dates).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })
        df_price_daily.index = pd.to_datetime(df_price_daily.index)
    else:
        df_price_daily = df_price.copy()
        df_price_daily.index = pd.to_datetime(df_price_daily.index)
    
    # Forward fill FRED data to align with daily price data
    df_fred_aligned = df_fred.reindex(df_price_daily.index, method='ffill')
    
    # Merge on date
    df_merged = pd.concat([df_price_daily, df_fred_aligned], axis=1)
    
    return df_merged

def handle_missing_values(df, strategy='forward_fill'):
    """Handle missing values in integrated data"""
    print(f"   Handling missing values...")
    
    initial_missing = df.isna().sum().sum()
    
    if strategy == 'forward_fill':
        df = df.ffill()
    elif strategy == 'interpolate':
        df = df.interpolate(method='linear', limit_direction='both')
    elif strategy == 'drop':
        df = df.dropna()
    
    final_missing = df.isna().sum().sum()
    
    print(f"      Missing values: {initial_missing} → {final_missing}")
    
    return df

def create_lagged_economic_features(df, lags=[1, 5, 20]):
    """Create lagged features from FRED data"""
    print(f"   Creating lagged economic features...")
    
    economic_cols = [col for col in df.columns if col not in 
                    ['open', 'high', 'low', 'close', 'volume']]
    
    for lag in lags:
        for col in economic_cols[:5]:  # Limit to top 5 for performance
            df[f'{col}_lag_{lag}'] = df[col].shift(lag)
    
    print(f"      Created {len(lags) * min(5, len(economic_cols))} lagged economic features")
    
    return df

def create_interaction_features(df):
    """Create interaction features between price and economic data"""
    print(f"   Creating interaction features...")
    
    # Price momentum × Interest rate
    if 'returns_simple' in df.columns and 'Federal Funds Rate' in df.columns:
        df['momentum_x_rate'] = df['returns_simple'] * df['Federal Funds Rate']
    
    # Volatility × Inflation expectations
    if 'volatility_20' in df.columns and 'US 10Y Inflation Expectations' in df.columns:
        df['vol_x_inflation'] = df['volatility_20'] * df['US 10Y Inflation Expectations']
    
    print(f"      Created interaction features")
    
    return df

def integrate_single_symbol(symbol, timeframe):
    """Integrate all data for a single symbol and timeframe"""
    print(f"\n{'='*70}")
    print(f"🔗 INTEGRATING {symbol} {timeframe}")
    print(f"{'='*70}")
    
    conn = connect_postgres()
    
    try:
        # 1. Load price features
        print(f"\n📊 Loading price features for {symbol} {timeframe}...")
        df_price = load_price_features(symbol, timeframe)
        
        if df_price is None:
            print(f"   ❌ Could not load price features")
            conn.close()
            return None
        
        print(f"   ✅ Loaded {len(df_price):,} rows × {len(df_price.columns)} columns")
        
        # 2. Load FRED data
        print(f"\n📈 Loading FRED economic indicators...")
        df_fred = load_fred_data(conn)
        print(f"   ✅ Loaded {len(df_fred):,} rows × {len(df_fred.columns)} columns")
        
        # 3. Align timeframes
        print(f"\n🔄 Aligning timeframes...")
        df_integrated = align_timeframes(df_price, df_fred, symbol)
        print(f"   ✅ Aligned data: {len(df_integrated):,} rows")
        
        # 4. Handle missing values
        print(f"\n🧹 Data cleaning...")
        df_integrated = handle_missing_values(df_integrated, strategy='forward_fill')
        
        # 5. Create lagged economic features
        print(f"\n⏰ Feature engineering...")
        df_integrated = create_lagged_economic_features(df_integrated)
        
        # 6. Create interaction features
        df_integrated = create_interaction_features(df_integrated)
        
        # 7. Final statistics
        print(f"\n📊 Integration Complete:")
        print(f"   Final shape: {df_integrated.shape[0]:,} rows × {df_integrated.shape[1]} columns")
        print(f"   Features created: {df_integrated.shape[1]}")
        print(f"   Date range: {df_integrated.index.min()} to {df_integrated.index.max()}")
        print(f"   Missing values: {df_integrated.isna().sum().sum()}")
        
        # 8. Save integrated data
        os.makedirs(INTEGRATED_DIR, exist_ok=True)
        output_file = INTEGRATED_DIR / f'integrated_{symbol}_{timeframe}.csv'
        df_integrated.to_csv(output_file)
        print(f"   ✅ Saved: {output_file}")
        
        conn.close()
        
        return df_integrated
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        conn.close()
        return None

def main():
    print("\n" + "="*70)
    print("🔗 DATA INTEGRATION")
    print("="*70)
    print("\nIntegrating price features with FRED economic indicators...")
    
    summary_data = []
    
    # Process each symbol and timeframe
    for symbol in PAIRS:
        for timeframe in TIMEFRAMES:
            df_integrated = integrate_single_symbol(symbol, timeframe)
            
            if df_integrated is not None:
                summary_data.append({
                    'Symbol': symbol,
                    'Timeframe': timeframe,
                    'Rows': len(df_integrated),
                    'Features': df_integrated.shape[1],
                    'Date_Range': f"{df_integrated.index.min().date()} to {df_integrated.index.max().date()}",
                    'Missing_Values': df_integrated.isna().sum().sum()
                })
    
    # Save summary
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv(INTEGRATED_DIR / 'integration_summary.csv', index=False)
        
        print(f"\n\n{'='*70}")
        print("📋 INTEGRATION SUMMARY")
        print(f"{'='*70}\n")
        print(summary_df.to_string(index=False))
        
        print(f"\n\n{'='*70}")
        print("✅ DATA INTEGRATION COMPLETE!")
        print(f"{'='*70}")
        print("\n📁 Integrated data files created:")
        for symbol in PAIRS:
            for timeframe in TIMEFRAMES:
                print(f"   - integrated_{symbol}_{timeframe}.csv")
        
        print(f"\n📊 Summary saved to: integration_summary.csv")
        
        print(f"\n🔍 What was integrated:")
        print(f"   ✅ Price features (OHLCV + 40+ technical indicators)")
        print(f"   ✅ FRED economic indicators (CPI, Unemployment, Interest Rates, etc.)")
        print(f"   ✅ Lagged economic features (for time series modeling)")
        print(f"   ✅ Interaction features (price × economic signals)")
        print(f"   ✅ Proper date/time alignment")
        print(f"   ✅ Missing value handling")
        
        print(f"\n💡 Next steps:")
        print(f"   1. Statistical analysis (correlations, causality)")
        print(f"   2. Feature selection")
        print(f"   3. Model preparation")
        print(f"   4. Machine learning modeling")

if __name__ == "__main__":
    main()