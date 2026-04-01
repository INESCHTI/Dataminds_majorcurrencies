#!/usr/bin/env python
"""
Test script for backtesting functionality
"""
import os
import sys
from datetime import datetime, timedelta

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from analytics.backtesting_engine import BacktestingEngine

def test_backtesting():
    """Test the backtesting system"""
    print("🔄 Testing Backtesting Engine")
    print("=" * 50)
    
    # Create backtesting engine
    engine = BacktestingEngine(initial_balance=100000.0, commission_rate=0.0002)
    
    print(f"💰 Initial Balance: ${engine.initial_balance:,.2f}")
    print(f"💸 Commission Rate: {engine.commission_rate * 100:.3f}%")
    
    # Define test parameters
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 31)
    symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
    
    print(f"\n📅 Backtesting Period:")
    print(f"   Start: {start_date.strftime('%Y-%m-%d')}")
    print(f"   End: {end_date.strftime('%Y-%m-%d')}")
    print(f"   Duration: {(end_date - start_date).days} days")
    print(f"   Symbols: {', '.join(symbols)}")
    
    # Load historical data
    print(f"\n📊 Loading Historical Data...")
    historical_data = engine.load_historical_data(start_date, end_date, symbols)
    
    for symbol, df in historical_data.items():
        print(f"   {symbol}: {len(df)} candles")
        print(f"     Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"     Price range: ${df['close'].min():.5f} - ${df['close'].max():.5f}")
    
    # Create a simple signal generator for testing
    def simple_signal_generator(timestamp, prices, positions):
        """Simple signal generator for testing"""
        signals = {}
        
        for symbol, price in prices.items():
            # Simple moving average crossover logic
            if symbol in historical_data:
                df = historical_data[symbol]
                current_data = df[df['timestamp'] <= timestamp]
                
                if len(current_data) >= 20:  # Need at least 20 periods
                    # Calculate simple moving averages
                    recent_prices = current_data['close'].tail(20)
                    short_ma = recent_prices.tail(5).mean()
                    long_ma = recent_prices.mean()
                    
                    # Generate signals based on MA crossover
                    if short_ma > long_ma * 1.001:  # 0.1% threshold
                        signals[symbol] = {
                            'direction': 'BUY',
                            'confidence': 0.7,
                            'timestamp': timestamp.isoformat()
                        }
                    elif short_ma < long_ma * 0.999:  # 0.1% threshold
                        signals[symbol] = {
                            'direction': 'SELL',
                            'confidence': 0.6,
                            'timestamp': timestamp.isoformat()
                        }
        
        return signals
    
    print(f"\n🚀 Running Backtest...")
    
    # Run backtest
    results = engine.run_backtest(
        historical_data=historical_data,
        signal_generator=simple_signal_generator,
        start_date=start_date,
        end_date=end_date
    )
    
    # Display results
    print(f"\n📊 Backtest Results:")
    metrics = results['metrics']
    
    print(f"   Final Balance: ${results['final_balance']:,.2f}")
    print(f"   Total Return: {results['total_return']:.2f}%")
    print(f"   Total P&L: ${metrics['total_pnl']:,.2f}")
    print(f"   Total Trades: {metrics['total_trades']}")
    print(f"   Winning Trades: {metrics['winning_trades']}")
    print(f"   Losing Trades: {metrics['losing_trades']}")
    print(f"   Win Rate: {metrics['win_rate']:.1f}%")
    
    # Risk metrics
    print(f"\n🛡️ Risk Metrics:")
    print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"   Max Drawdown: {metrics['max_drawdown']:.2f}%")
    print(f"   Max Drawdown Duration: {metrics['max_drawdown_duration']} periods")
    print(f"   Volatility: {metrics['volatility']:.2f}%")
    print(f"   Sortino Ratio: {metrics['sortino_ratio']:.2f}")
    print(f"   Calmar Ratio: {metrics['calmar_ratio']:.2f}")
    
    # Trade statistics
    print(f"\n📈 Trade Statistics:")
    print(f"   Profit Factor: {metrics['profit_factor']:.2f}")
    print(f"   Average Win: ${metrics['avg_win']:.2f}")
    print(f"   Average Loss: ${metrics['avg_loss']:.2f}")
    print(f"   Average Win/Loss Ratio: {metrics['avg_win_loss_ratio']:.2f}")
    print(f"   Largest Win: ${metrics['largest_win']:.2f}")
    print(f"   Largest Loss: ${metrics['largest_loss']:.2f}")
    print(f"   Average Trade Duration: {metrics['avg_trade_duration']:.1f} hours")
    
    # Performance assessment
    print(f"\n🎯 Performance Assessment:")
    
    assessment_points = []
    
    # Sharpe ratio assessment
    if metrics['sharpe_ratio'] > 1.5:
        assessment_points.append("✅ Excellent Sharpe ratio (> 1.5)")
    elif metrics['sharpe_ratio'] > 1.0:
        assessment_points.append("⚠️ Good Sharpe ratio (> 1.0)")
    else:
        assessment_points.append("❌ Poor Sharpe ratio (< 1.0)")
    
    # Drawdown assessment
    if metrics['max_drawdown'] < 15:
        assessment_points.append("✅ Excellent max drawdown (< 15%)")
    elif metrics['max_drawdown'] < 25:
        assessment_points.append("⚠️ Acceptable max drawdown (< 25%)")
    else:
        assessment_points.append("❌ Poor max drawdown (> 25%)")
    
    # Win rate assessment
    if metrics['win_rate'] > 55:
        assessment_points.append("✅ Excellent win rate (> 55%)")
    elif metrics['win_rate'] > 45:
        assessment_points.append("⚠️ Acceptable win rate (> 45%)")
    else:
        assessment_points.append("❌ Poor win rate (< 45%)")
    
    # Profit factor assessment
    if metrics['profit_factor'] > 1.3:
        assessment_points.append("✅ Excellent profit factor (> 1.3)")
    elif metrics['profit_factor'] > 1.1:
        assessment_points.append("⚠️ Acceptable profit factor (> 1.1)")
    else:
        assessment_points.append("❌ Poor profit factor (< 1.1)")
    
    for point in assessment_points:
        print(f"   {point}")
    
    # Sample trades
    print(f"\n📜 Sample Trades (first 5):")
    trades = results['trades'][:5]
    for i, trade in enumerate(trades, 1):
        print(f"   Trade {i}: {trade['symbol']} {trade['direction']} "
              f"${trade['pnl']:+.2f} ({trade['duration_hours']:.1f}h)")
    
    # Generate report
    print(f"\n📋 Backtest Report:")
    report = engine.generate_report(results)
    print(report)
    
    print(f"\n✅ Backtesting Test Completed!")

if __name__ == "__main__":
    test_backtesting()
