import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from statsmodels.tsa.stattools import adfuller, grangercausalitytests
from statsmodels.tsa.vector_ar.vecm import coint_johansen
import os
from pathlib import Path
from dotenv import load_dotenv
import warnings
warnings.filterwarnings('ignore')

env_path = Path(__file__).parent.parent / 'config' / '.env'
load_dotenv(dotenv_path=env_path, override=True)

INTEGRATED_DIR = Path(__file__).parent.parent / 'data_understanding_outputs' / 'integrated'
STATISTICS_DIR = Path(__file__).parent.parent / 'data_understanding_outputs' / 'statistics'

PAIRS = ['EURUSD', 'USDJPY', 'GBPUSD', 'USDCHF']
TIMEFRAMES = ['1H', '4H', '1D']

# Plotting settings
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def load_integrated_data(symbol, timeframe):
    """Load integrated data from CSV"""
    filepath = INTEGRATED_DIR / f'integrated_{symbol}_{timeframe}.csv'
    
    try:
        df = pd.read_csv(filepath, index_col=0, parse_dates=True)
        return df
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        return None

def calculate_correlation_matrix(df, symbol, timeframe, output_dir=STATISTICS_DIR):
    """Calculate and visualize correlation matrix"""
    os.makedirs(STATISTICS_DIR, exist_ok=True)
    
    print(f"\n📊 Calculating correlation matrix for {symbol} {timeframe}...")
    
    # Select only numeric columns and drop NaN-heavy columns
    numeric_df = df.select_dtypes(include=[np.number])
    
    # Drop columns with too many NaN values
    numeric_df = numeric_df.dropna(axis=1, thresh=len(numeric_df) * 0.5)
    
    # Calculate correlation
    corr_matrix = numeric_df.corr()
    
    # Create heatmap
    fig, ax = plt.subplots(figsize=(16, 12))
    
    sns.heatmap(corr_matrix, annot=False, cmap='coolwarm', center=0,
                square=True, linewidths=0.5, cbar_kws={"shrink": 0.8}, ax=ax)
    
    ax.set_title(f'{symbol} {timeframe} - Correlation Matrix\n({len(corr_matrix)} features)', 
                 fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right', fontsize=8)
    plt.yticks(rotation=0, fontsize=8)
    plt.tight_layout()
    
    filename = f'{output_dir}/correlation_{symbol}_{timeframe}.png'
    plt.savefig(filename, dpi=100, bbox_inches='tight')
    print(f"   📊 Saved: {filename}")
    plt.close()
    
    # Save correlation matrix to CSV
    corr_csv = f'{output_dir}/correlation_{symbol}_{timeframe}.csv'
    corr_matrix.to_csv(corr_csv)
    
    return corr_matrix

def find_top_correlations(corr_matrix, target_col='close', top_n=15):
    """Find top correlations with target column"""
    if target_col not in corr_matrix.columns:
        return None
    
    correlations = corr_matrix[target_col].sort_values(ascending=False)
    return correlations[correlations.index != target_col].head(top_n)

def test_stationarity(df, symbol, timeframe, output_dir=STATISTICS_DIR):
    """Test stationarity of key variables using ADF test"""
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n🔬 Testing stationarity for {symbol} {timeframe}...")
    
    # Key columns to test
    test_cols = ['close', 'returns_simple', 'rsi_14', 'macd']
    test_cols = [col for col in test_cols if col in df.columns]
    
    results = []
    
    for col in test_cols:
        data = df[col].dropna()
        
        if len(data) < 10:
            continue
        
        try:
            adf_result = adfuller(data, autolag='AIC')
            
            is_stationary = adf_result[1] < 0.05  # p-value < 0.05
            
            results.append({
                'Variable': col,
                'ADF_Statistic': adf_result[0],
                'P_Value': adf_result[1],
                'Stationary': 'Yes' if is_stationary else 'No',
                'Critical_Value_5%': adf_result[4]['5%']
            })
            
            symbol_str = f"{symbol} {timeframe}"
            if is_stationary:
                print(f"   ✅ {col}: STATIONARY (p={adf_result[1]:.4f})")
            else:
                print(f"   ⚠️  {col}: NON-STATIONARY (p={adf_result[1]:.4f})")
        
        except Exception as e:
            print(f"   ❌ Error testing {col}: {str(e)[:50]}")
    
    if results:
        results_df = pd.DataFrame(results)
        csv_file = f'{output_dir}/stationarity_{symbol}_{timeframe}.csv'
        results_df.to_csv(csv_file, index=False)
        print(f"   📊 Saved: {csv_file}")
        
        return results_df
    
    return None

def calculate_rolling_correlation(df, col1, col2, window=20, symbol='', timeframe='', output_dir=STATISTICS_DIR):
    """Calculate and plot rolling correlation"""
    os.makedirs(output_dir, exist_ok=True)
    
    if col1 not in df.columns or col2 not in df.columns:
        return None
    
    rolling_corr = df[col1].rolling(window=window).corr(df[col2])
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    ax.plot(df.index, rolling_corr, linewidth=1.5, color='#1f77b4', label=f'Rolling Corr (window={window})')
    ax.axhline(y=0, color='black', linestyle='--', linewidth=0.5)
    ax.fill_between(df.index, rolling_corr, 0, alpha=0.3, color='#1f77b4')
    
    ax.set_title(f'{symbol} {timeframe} - Rolling Correlation: {col1} vs {col2}', 
                 fontsize=12, fontweight='bold')
    ax.set_xlabel('Date')
    ax.set_ylabel('Correlation')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    filename = f'{output_dir}/rolling_corr_{symbol}_{timeframe}_{col1}_vs_{col2}.png'
    plt.savefig(filename, dpi=100, bbox_inches='tight')
    print(f"   📊 Saved: {filename}")
    plt.close()
    
    return rolling_corr

def analyze_price_volatility_relationship(df, symbol, timeframe, output_dir=STATISTICS_DIR):
    """Analyze relationship between price changes and volatility"""
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n📈 Analyzing price-volatility relationship for {symbol} {timeframe}...")
    
    if 'returns_simple' not in df.columns or 'volatility_20' not in df.columns:
        print(f"   ⚠️  Required columns not found")
        return None
    
    # Create scatter plot
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Sample data if too large (for visualization)
    sample_df = df.dropna(subset=['returns_simple', 'volatility_20'])
    if len(sample_df) > 5000:
        sample_df = sample_df.sample(n=5000)
    
    ax.scatter(sample_df['volatility_20'], sample_df['returns_simple'], 
              alpha=0.5, s=20, color='#1f77b4')
    
    # Add regression line
    z = np.polyfit(sample_df['volatility_20'].dropna(), 
                   sample_df['returns_simple'].dropna(), 1)
    p = np.poly1d(z)
    x_line = np.linspace(sample_df['volatility_20'].min(), sample_df['volatility_20'].max(), 100)
    ax.plot(x_line, p(x_line), "r--", linewidth=2, label=f'Trend: y={z[0]:.4f}x+{z[1]:.4f}')
    
    ax.set_xlabel('Volatility (20-day rolling std)')
    ax.set_ylabel('Returns (%)')
    ax.set_title(f'{symbol} {timeframe} - Returns vs Volatility', fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    filename = f'{output_dir}/returns_vs_volatility_{symbol}_{timeframe}.png'
    plt.savefig(filename, dpi=100, bbox_inches='tight')
    print(f"   📊 Saved: {filename}")
    plt.close()
    
    # Calculate correlation
    corr = sample_df['returns_simple'].corr(sample_df['volatility_20'])
    print(f"   Correlation: {corr:.4f}")
    
    return corr

def analyze_economic_impact(df, symbol, timeframe, output_dir=STATISTICS_DIR):
    """Analyze impact of economic indicators on price"""
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n💰 Analyzing economic indicator impact for {symbol} {timeframe}...")
    
    # Economic indicators
    economic_cols = ['Federal Funds Rate', 'US CPI', 'US 10Y Treasury', 
                     'US 10Y Inflation Expectations', 'US Unemployment Rate']
    economic_cols = [col for col in economic_cols if col in df.columns]
    
    if not economic_cols:
        print(f"   ⚠️  No economic indicators found")
        return None
    
    results = []
    
    for econ_col in economic_cols:
        if 'close' in df.columns:
            clean_df = df[[econ_col, 'close']].dropna()
            
            if len(clean_df) > 10:
                corr = clean_df[econ_col].corr(clean_df['close'])
                
                # Calculate percentage change correlation
                econ_pct = clean_df[econ_col].pct_change()
                price_pct = clean_df['close'].pct_change()
                corr_pct = econ_pct.corr(price_pct)
                
                results.append({
                    'Economic_Indicator': econ_col,
                    'Correlation_with_Price': corr,
                    'Correlation_with_Returns': corr_pct,
                    'Relationship': 'Positive' if corr > 0 else 'Negative',
                    'Strength': 'Strong' if abs(corr) > 0.5 else 'Moderate' if abs(corr) > 0.3 else 'Weak'
                })
                
                print(f"   {econ_col}:")
                print(f"      Price correlation: {corr:.4f}")
                print(f"      Returns correlation: {corr_pct:.4f}")
    
    if results:
        results_df = pd.DataFrame(results)
        csv_file = f'{output_dir}/economic_impact_{symbol}_{timeframe}.csv'
        results_df.to_csv(csv_file, index=False)
        print(f"   📊 Saved: {csv_file}")
        
        return results_df
    
    return None

def create_summary_report(all_results, output_dir=STATISTICS_DIR):
    """Create comprehensive statistical summary report"""
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n\n{'='*70}")
    print("📊 STATISTICAL ANALYSIS SUMMARY")
    print(f"{'='*70}")
    
    with open(f'{output_dir}/statistical_analysis_report.txt', 'w') as f:
        f.write("STATISTICAL ANALYSIS REPORT\n")
        f.write("="*70 + "\n")
        f.write(f"Generated: {pd.Timestamp.now()}\n\n")
        
        f.write("KEY FINDINGS:\n")
        f.write("-"*70 + "\n")
        
        for symbol_tf, results in all_results.items():
            f.write(f"\n{symbol_tf}:\n")
            
            if 'correlations' in results and results['correlations'] is not None:
                f.write(f"  Top correlations with price:\n")
                for idx, val in results['correlations'].head(5).items():
                    f.write(f"    - {idx}: {val:.4f}\n")
            
            if 'stationarity' in results and results['stationarity'] is not None:
                stationary_count = (results['stationarity']['Stationary'] == 'Yes').sum()
                f.write(f"  Stationarity: {stationary_count} stationary variables\n")
            
            if 'economic_impact' in results and results['economic_impact'] is not None:
                f.write(f"  Economic indicators impact:\n")
                for _, row in results['economic_impact'].iterrows():
                    f.write(f"    - {row['Economic_Indicator']}: {row['Correlation_with_Price']:.4f}\n")
        
        f.write("\n" + "="*70 + "\n")
        f.write("RECOMMENDATIONS:\n")
        f.write("-"*70 + "\n")
        f.write("1. Focus on stationary variables for time series modeling\n")
        f.write("2. Use highly correlated economic indicators as features\n")
        f.write("3. Apply differencing to non-stationary variables\n")
        f.write("4. Test for Granger causality between key variables\n")
    
    print(f"✅ Report saved to: {output_dir}/statistical_analysis_report.txt")

def main():
    print("\n" + "="*70)
    print("📊 STATISTICAL ANALYSIS")
    print("="*70)
    
    os.makedirs(STATISTICS_DIR, exist_ok=True)
    
    all_results = {}
    
    # Analyze each symbol and timeframe
    for symbol in PAIRS:
        for timeframe in TIMEFRAMES:
            print(f"\n{'='*70}")
            print(f"🔬 Analyzing {symbol} {timeframe}")
            print(f"{'='*70}")
            
            df = load_integrated_data(symbol, timeframe)
            
            if df is None or len(df) < 10:
                print(f"   ❌ Could not load data")
                continue
            
            results_key = f"{symbol} {timeframe}"
            all_results[results_key] = {}
            
            # 1. Correlation analysis
            corr_matrix = calculate_correlation_matrix(df, symbol, timeframe)
            top_corr = find_top_correlations(corr_matrix, 'close')
            all_results[results_key]['correlations'] = top_corr
            
            if top_corr is not None:
                print(f"\n   Top correlations with close price:")
                for idx, val in top_corr.head(5).items():
                    print(f"      {idx}: {val:.4f}")
            
            # 2. Stationarity test
            stationarity_df = test_stationarity(df, symbol, timeframe)
            all_results[results_key]['stationarity'] = stationarity_df
            
            # 3. Rolling correlation (price vs major economic indicator)
            if 'Federal Funds Rate' in df.columns:
                rolling_corr = calculate_rolling_correlation(
                    df, 'close', 'Federal Funds Rate', 
                    window=20, symbol=symbol, timeframe=timeframe
                )
                all_results[results_key]['rolling_corr'] = rolling_corr
            
            # 4. Price-volatility relationship
            pv_corr = analyze_price_volatility_relationship(df, symbol, timeframe)
            all_results[results_key]['pv_correlation'] = pv_corr
            
            # 5. Economic impact analysis
            econ_impact = analyze_economic_impact(df, symbol, timeframe)
            all_results[results_key]['economic_impact'] = econ_impact
    
    # Create summary report
    create_summary_report(all_results)
    
    print(f"\n\n{'='*70}")
    print("✅ STATISTICAL ANALYSIS COMPLETE!")
    print(f"{'='*70}")
    
    print(f"\n📁 Output files created:")
    print(f"   - correlation_*.png (heatmaps)")
    print(f"   - correlation_*.csv (correlation matrices)")
    print(f"   - stationarity_*.csv (ADF test results)")
    print(f"   - rolling_corr_*.png (rolling correlation plots)")
    print(f"   - returns_vs_volatility_*.png (scatter plots)")
    print(f"   - economic_impact_*.csv (economic indicator impact)")
    print(f"   - statistical_analysis_report.txt (summary)")
    
    print(f"\n🔍 Key Insights Generated:")
    print(f"   ✅ Correlation matrices (which features move together)")
    print(f"   ✅ Stationarity tests (which variables are stationary)")
    print(f"   ✅ Rolling correlations (time-varying relationships)")
    print(f"   ✅ Economic impact (how macro data affects price)")
    print(f"   ✅ Price-volatility dynamics")
    
    print(f"\n💡 Next steps:")
    print(f"   1. Review correlation heatmaps")
    print(f"   2. Select best features based on correlation & stationarity")
    print(f"   3. Prepare data for modeling")
    print(f"   4. Begin machine learning phase")

if __name__ == "__main__":
    main()