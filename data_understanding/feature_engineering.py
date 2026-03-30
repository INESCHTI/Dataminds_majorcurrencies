import pandas as pd
import numpy as np
from influxdb_client import InfluxDBClient
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Robustly load config/.env regardless of current working directory
from pathlib import Path
env_path = Path(__file__).parent.parent / 'config' / '.env'
load_dotenv(dotenv_path=env_path, override=True)

OUTPUT_DIR = Path(__file__).parent.parent / 'data_understanding_outputs' / 'features'

# Configuration
INFLUXDB_URL = os.getenv('INFLUXDB_URL')
INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN')
INFLUXDB_ORG = os.getenv('INFLUXDB_ORG')
INFLUXDB_BUCKET = os.getenv('INFLUXDB_BUCKET')

PAIRS = ['EURUSD', 'USDJPY', 'GBPUSD', 'USDCHF']
TIMEFRAMES = ['1H', '4H', '1D']

def connect_influxdb():
    """Connect to InfluxDB"""
    # Check environment variables
    missing = []
    for var, val in [
        ("INFLUXDB_URL", INFLUXDB_URL),
        ("INFLUXDB_TOKEN", INFLUXDB_TOKEN),
        ("INFLUXDB_ORG", INFLUXDB_ORG),
        ("INFLUXDB_BUCKET", INFLUXDB_BUCKET)
    ]:
        if not isinstance(val, str) or not val.strip():
            missing.append(var)
    if missing:
        raise ValueError(f"Missing or invalid InfluxDB environment variables: {', '.join(missing)}.\nPlease check your config/.env file and ensure all required variables are set.")

    client = InfluxDBClient(
        url=INFLUXDB_URL,
        token=INFLUXDB_TOKEN,
        org=INFLUXDB_ORG
    )
    return client

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
    
    # Parse results
    data = []
    for table in result:
        for record in table.records:
            data.append({
                'time': record.get_time(),
                'field': record.get_field(),
                'value': record.get_value()
            })
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    if len(df) == 0:
        return None
    
    # Pivot to get OHLCV columns
    df_pivot = df.pivot_table(
        index='time',
        columns='field',
        values='value',
        aggfunc='first'
    )
    
    df_pivot.columns = ['close', 'high', 'low', 'open', 'volume']
    df_pivot = df_pivot[['open', 'high', 'low', 'close', 'volume']].astype(float)
    df_pivot.index.name = 'time'
    
    return df_pivot.sort_index()

# ==================== TECHNICAL INDICATORS ====================

def calculate_sma(df, periods):
    """Simple Moving Average"""
    return df.rolling(window=periods).mean()

def calculate_ema(df, periods):
    """Exponential Moving Average"""
    return df.ewm(span=periods, adjust=False).mean()

def calculate_rsi(df, periods=14):
    """Relative Strength Index"""
    delta = df.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(df, fast=12, slow=26, signal=9):
    """MACD (Moving Average Convergence Divergence)"""
    ema_fast = df.ewm(span=fast, adjust=False).mean()
    ema_slow = df.ewm(span=slow, adjust=False).mean()
    
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal, adjust=False).mean()
    macd_hist = macd - macd_signal
    
    return macd, macd_signal, macd_hist

def calculate_bollinger_bands(df, periods=20, std_dev=2):
    """Bollinger Bands"""
    sma = df.rolling(window=periods).mean()
    std = df.rolling(window=periods).std()
    
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    
    return upper_band, sma, lower_band

def calculate_atr(df, periods=14):
    """Average True Range"""
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())
    
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(window=periods).mean()
    
    return atr

def calculate_stochastic(df, periods=14, smooth=3):
    """Stochastic Oscillator"""
    lowest_low = df['low'].rolling(window=periods).min()
    highest_high = df['high'].rolling(window=periods).max()
    
    k_percent = 100 * (df['close'] - lowest_low) / (highest_high - lowest_low)
    d_percent = k_percent.rolling(window=smooth).mean()
    
    return k_percent, d_percent

def calculate_returns(df):
    """Calculate returns and log returns"""
    simple_returns = df.pct_change()
    log_returns = np.log(df / df.shift(1))
    
    return simple_returns, log_returns

def calculate_volatility(returns, periods=20):
    """Calculate rolling volatility"""
    return returns.rolling(window=periods).std()

def calculate_roc(df, periods=12):
    """Rate of Change"""
    return ((df - df.shift(periods)) / df.shift(periods)) * 100

# ==================== MAIN FEATURE ENGINEERING ====================

def create_features(df, symbol, timeframe):
    """Create all features for a dataframe"""
    
    print(f"\n[INFO] Creating features for {symbol} {timeframe}...")
    
    # Keep original OHLCV
    features = df[['open', 'high', 'low', 'close', 'volume']].copy()
    
    # ---- RETURNS & VOLATILITY ----
    simple_ret, log_ret = calculate_returns(features['close'])
    features['returns_simple'] = simple_ret
    features['returns_log'] = log_ret
    features['volatility_20'] = calculate_volatility(simple_ret, 20)
    
    # ---- MOVING AVERAGES ----
    features['sma_5'] = calculate_sma(features['close'], 5)
    features['sma_10'] = calculate_sma(features['close'], 10)
    features['sma_20'] = calculate_sma(features['close'], 20)
    features['sma_50'] = calculate_sma(features['close'], 50)
    features['sma_200'] = calculate_sma(features['close'], 200)
    
    features['ema_12'] = calculate_ema(features['close'], 12)
    features['ema_26'] = calculate_ema(features['close'], 26)
    
    # ---- MOMENTUM INDICATORS ----
    features['rsi_14'] = calculate_rsi(features['close'], 14)
    features['roc_12'] = calculate_roc(features['close'], 12)
    
    # ---- MACD ----
    macd, macd_signal, macd_hist = calculate_macd(features['close'])
    features['macd'] = macd
    features['macd_signal'] = macd_signal
    features['macd_hist'] = macd_hist
    
    # ---- BOLLINGER BANDS ----
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(features['close'], 20, 2)
    features['bb_upper'] = bb_upper
    features['bb_middle'] = bb_middle
    features['bb_lower'] = bb_lower
    features['bb_width'] = bb_upper - bb_lower
    features['bb_position'] = (features['close'] - bb_lower) / (bb_upper - bb_lower)
    
    # ---- VOLATILITY INDICATORS ----
    features['atr_14'] = calculate_atr(features, 14)
    
    # ---- STOCHASTIC ----
    k_percent, d_percent = calculate_stochastic(features, 14, 3)
    features['stoch_k'] = k_percent
    features['stoch_d'] = d_percent
    
    # ---- PRICE ACTION ----
    features['high_low_ratio'] = (features['high'] - features['low']) / features['close']
    features['close_open_ratio'] = (features['close'] - features['open']) / features['close']
    features['body_size'] = abs(features['close'] - features['open'])
    features['wick_upper'] = features['high'] - features[['close', 'open']].max(axis=1)
    features['wick_lower'] = features[['close', 'open']].min(axis=1) - features['low']
    
    # ---- LAGGED FEATURES (for ML) ----
    for lag in [1, 2, 3, 5]:
        features[f'returns_lag_{lag}'] = features['returns_simple'].shift(lag)
        features[f'close_lag_{lag}'] = features['close'].shift(lag)
        features[f'volume_lag_{lag}'] = features['volume'].shift(lag)
    
    # ---- VOLUME INDICATORS ----
    features['volume_sma_20'] = features['volume'].rolling(20).mean()
    features['volume_ratio'] = features['volume'] / features['volume_sma_20']
    
    print(f"   [OK] Created {len(features.columns) - 5} features (5 OHLCV + {len(features.columns) - 5} indicators)")
    
    return features

def main():
    print("\n" + "="*70)
    print("🛠️  FEATURE ENGINEERING & PREPARATION")
    print("="*70)
    
    client = connect_influxdb()
    print("\n✅ Connected to InfluxDB")
    
    summary_data = []
    all_data = [] 
    
    # Process each symbol and timeframe
    for symbol in PAIRS:
        print(f"\n{'='*70}")
        print(f"🔄 Processing {symbol}")
        print(f"{'='*70}")
        
        for timeframe in TIMEFRAMES:
            print(f"\n📥 Fetching {symbol} {timeframe}...")
            
            try:
                df = fetch_price_data(client, symbol, timeframe)
                
                if df is None or len(df) == 0:
                    print(f"   ❌ No data found")
                    continue
                
                print(f"   ✅ Fetched {len(df):,} candles")
                
                # Create features
                features_df = create_features(df, symbol, timeframe)
                
                # Calculate statistics
                print(f"\n📊 Feature Statistics for {symbol} {timeframe}:")
                print(f"   Total rows: {len(features_df):,}")
                print(f"   Total columns: {len(features_df.columns)}")
                print(f"   Date range: {features_df.index.min()} to {features_df.index.max()}")
                
                # Check for NaN values
                nan_pct = (features_df.isna().sum().sum() / (len(features_df) * len(features_df.columns))) * 100
                print(f"   NaN values: {nan_pct:.2f}%")
                
                # Save individual feature file (for data_integration.py)
                os.makedirs(OUTPUT_DIR, exist_ok=True)
                features_df.to_csv(OUTPUT_DIR / f'features_{symbol}_{timeframe}.csv')
                print(f"   💾 Saved: features_{symbol}_{timeframe}.csv")
                
                # Add identifiers and collect
                features_df['symbol'] = symbol
                features_df['timeframe'] = timeframe
                all_data.append(features_df)
                
                summary_data.append({
                    'Symbol': symbol,
                    'Timeframe': timeframe,
                    'Candles': len(features_df),
                    'Features': len(features_df.columns),
                    'Date_Range': f"{features_df.index.min().date()} to {features_df.index.max().date()}",
                    'NaN_Pct': nan_pct
                })
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)[:100]}")
    
    client.close()

    # Save summary
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(OUTPUT_DIR / 'features_summary.csv', index=False)
    pd.concat(all_data).to_csv(OUTPUT_DIR / 'all_features.csv')
    print(f"✅ Saved: {OUTPUT_DIR / 'all_features.csv'}")

    # --- Feature Descriptions ---
    feature_descriptions = [
        {"Feature": "returns_simple", "Purpose": "Simple return from previous close", "Helpfulness": "Shows price change direction and magnitude."},
        {"Feature": "returns_log", "Purpose": "Logarithmic return", "Helpfulness": "Better for statistical analysis and compounding."},
        {"Feature": "volatility_20", "Purpose": "20-period rolling volatility", "Helpfulness": "Measures recent price variability."},
        {"Feature": "sma_5", "Purpose": "5-period simple moving average", "Helpfulness": "Short-term trend direction."},
        {"Feature": "sma_10", "Purpose": "10-period simple moving average", "Helpfulness": "Short/medium trend direction."},
        {"Feature": "sma_20", "Purpose": "20-period simple moving average", "Helpfulness": "Medium-term trend direction."},
        {"Feature": "sma_50", "Purpose": "50-period simple moving average", "Helpfulness": "Longer-term trend direction."},
        {"Feature": "sma_200", "Purpose": "200-period simple moving average", "Helpfulness": "Major trend filter."},
        {"Feature": "ema_12", "Purpose": "12-period exponential moving average", "Helpfulness": "Faster trend signal."},
        {"Feature": "ema_26", "Purpose": "26-period exponential moving average", "Helpfulness": "Slower trend signal."},
        {"Feature": "rsi_14", "Purpose": "14-period Relative Strength Index", "Helpfulness": "Detects overbought/oversold conditions."},
        {"Feature": "roc_12", "Purpose": "12-period Rate of Change", "Helpfulness": "Measures momentum speed."},
        {"Feature": "macd", "Purpose": "MACD line (trend/momentum)", "Helpfulness": "Shows trend changes and momentum."},
        {"Feature": "macd_signal", "Purpose": "MACD signal line", "Helpfulness": "MACD smoothing for signals."},
        {"Feature": "macd_hist", "Purpose": "MACD histogram", "Helpfulness": "MACD/Signal difference, shows momentum shifts."},
        {"Feature": "bb_upper", "Purpose": "Bollinger Bands upper band", "Helpfulness": "Upper price volatility boundary."},
        {"Feature": "bb_middle", "Purpose": "Bollinger Bands middle (SMA)", "Helpfulness": "Central tendency of price."},
        {"Feature": "bb_lower", "Purpose": "Bollinger Bands lower band", "Helpfulness": "Lower price volatility boundary."},
        {"Feature": "bb_width", "Purpose": "Bollinger Band width", "Helpfulness": "Measures volatility expansion/contraction."},
        {"Feature": "bb_position", "Purpose": "Position within Bollinger Bands", "Helpfulness": "Shows where price is within bands."},
        {"Feature": "atr_14", "Purpose": "14-period Average True Range", "Helpfulness": "Measures market volatility."},
        {"Feature": "stoch_k", "Purpose": "%K Stochastic Oscillator", "Helpfulness": "Shows price position in recent range."},
        {"Feature": "stoch_d", "Purpose": "%D Stochastic Oscillator", "Helpfulness": "Smoothed %K, for signals."},
        {"Feature": "high_low_ratio", "Purpose": "(High-Low)/Close ratio", "Helpfulness": "Measures daily price spread."},
        {"Feature": "close_open_ratio", "Purpose": "(Close-Open)/Close ratio", "Helpfulness": "Shows bullish/bearish candle strength."},
        {"Feature": "body_size", "Purpose": "Absolute candle body size", "Helpfulness": "Measures price movement strength."},
        {"Feature": "wick_upper", "Purpose": "Upper wick size", "Helpfulness": "Shows price rejection above body."},
        {"Feature": "wick_lower", "Purpose": "Lower wick size", "Helpfulness": "Shows price rejection below body."},
        {"Feature": "returns_lag_1", "Purpose": "Lagged simple return (1)", "Helpfulness": "Captures short-term return memory."},
        {"Feature": "returns_lag_2", "Purpose": "Lagged simple return (2)", "Helpfulness": "Captures short-term return memory."},
        {"Feature": "returns_lag_3", "Purpose": "Lagged simple return (3)", "Helpfulness": "Captures short-term return memory."},
        {"Feature": "returns_lag_5", "Purpose": "Lagged simple return (5)", "Helpfulness": "Captures short-term return memory."},
        {"Feature": "close_lag_1", "Purpose": "Lagged close price (1)", "Helpfulness": "Previous close for ML models."},
        {"Feature": "close_lag_2", "Purpose": "Lagged close price (2)", "Helpfulness": "Previous close for ML models."},
        {"Feature": "close_lag_3", "Purpose": "Lagged close price (3)", "Helpfulness": "Previous close for ML models."},
        {"Feature": "close_lag_5", "Purpose": "Lagged close price (5)", "Helpfulness": "Previous close for ML models."},
        {"Feature": "volume_lag_1", "Purpose": "Lagged volume (1)", "Helpfulness": "Previous volume for ML models."},
        {"Feature": "volume_lag_2", "Purpose": "Lagged volume (2)", "Helpfulness": "Previous volume for ML models."},
        {"Feature": "volume_lag_3", "Purpose": "Lagged volume (3)", "Helpfulness": "Previous volume for ML models."},
        {"Feature": "volume_lag_5", "Purpose": "Lagged volume (5)", "Helpfulness": "Previous volume for ML models."},
        {"Feature": "volume_sma_20", "Purpose": "20-period volume SMA", "Helpfulness": "Shows average trading activity."},
        {"Feature": "volume_ratio", "Purpose": "Volume/Volume SMA ratio", "Helpfulness": "Detects unusual volume spikes."},
    ]
    feature_desc_df = pd.DataFrame(feature_descriptions)
    feature_desc_df.to_csv(OUTPUT_DIR / 'feature_descriptions.csv', index=False)

    print(f"\n\n{'='*70}")
    print("📋 FEATURE ENGINEERING SUMMARY")
    print(f"{'='*70}\n")
    print(summary_df.to_string(index=False))

    print(f"\n\n{'='*70}")
    print("✅ FEATURE ENGINEERING COMPLETE!")
    print(f"{'='*70}")
    print("\n📁 Feature files created:")
    for _, row in summary_df.iterrows():
        print(f"   - features_{row['Symbol']}_{row['Timeframe']}.csv ({row['Features']} features)")

    print(f"\n📊 Feature Summary saved to: features_summary.csv")
    print(f"\n📄 Feature Descriptions saved to: feature_descriptions.csv")

    print(f"\n🔍 Features Created:")
    print(f"   See 'feature_descriptions.csv' for a clear list of all engineered features, their purpose, and how they help analysis and modeling.")

    print(f"\n💡 Next steps:")
    print(f"   1. Explore feature correlations")
    print(f"   2. Integrate with FRED economic data")
    print(f"   3. Handle missing values (NaN)")
    print(f"   4. Normalize/scale features for ML")

if __name__ == "__main__":
    main()