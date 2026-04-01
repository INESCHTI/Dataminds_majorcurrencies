#!/usr/bin/env python
"""
Test script for performance tracking functionality
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

from performance.performance_tracker import get_performance_tracker
import random

def test_performance_tracking():
    """Test the performance tracking system"""
    print("📊 Testing Performance Tracking System")
    print("=" * 50)
    
    # Create performance tracker
    tracker = get_performance_tracker(initial_balance=100000.0)
    
    print(f"💰 Initial Balance: ${tracker.initial_balance:,.2f}")
    print(f"📈 Current Balance: ${tracker.current_balance:,.2f}")
    
    # Simulate some trades
    trades = [
        {
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'entry_price': 1.0850,
            'exit_price': 1.0900,
            'size': 10000,
            'pnl': 50.0,
            'duration_hours': 2.5,
            'entry_signal': 'BUY',
            'exit_reason': 'take_profit'
        },
        {
            'symbol': 'GBPUSD',
            'direction': 'SELL',
            'entry_price': 1.2650,
            'exit_price': 1.2600,
            'size': 5000,
            'pnl': 25.0,
            'duration_hours': 1.8,
            'entry_signal': 'SELL',
            'exit_reason': 'stop_loss'
        },
        {
            'symbol': 'USDJPY',
            'direction': 'BUY',
            'entry_price': 149.50,
            'exit_price': 149.20,
            'size': 8000,
            'pnl': -24.0,
            'duration_hours': 3.2,
            'entry_signal': 'BUY',
            'exit_reason': 'stop_loss'
        },
        {
            'symbol': 'USDCHF',
            'direction': 'SELL',
            'entry_price': 0.8820,
            'exit_price': 0.8750,
            'size': 12000,
            'pnl': 84.0,
            'duration_hours': 4.1,
            'entry_signal': 'SELL',
            'exit_reason': 'take_profit'
        }
    ]
    
    print(f"\n📝 Adding Sample Trades:")
    
    for i, trade in enumerate(trades, 1):
        print(f"   Trade {i}: {trade['symbol']} {trade['direction']} P&L: ${trade['pnl']:+.2f}")
        tracker.add_trade(trade)
    
    # Update balance to reflect trades
    final_balance = 100000.0 + sum(trade['pnl'] for trade in trades)
    tracker.update_balance(final_balance)
    
    print(f"\n💰 Final Balance: ${tracker.current_balance:,.2f}")
    print(f"📈 Total P&L: ${tracker.total_pnl:+,.2f}")
    print(f"📊 Total Return: {((tracker.current_balance - tracker.initial_balance) / tracker.initial_balance) * 100:+.2f}%")
    
    # Get current metrics
    print(f"\n📊 Current Performance Metrics:")
    metrics = tracker.get_current_metrics()
    
    print(f"   Total Trades: {metrics['total_trades']}")
    print(f"   Winning Trades: {metrics['winning_trades']}")
    print(f"   Losing Trades: {metrics['losing_trades']}")
    print(f"   Win Rate: {metrics['win_rate']:.1f}%")
    print(f"   Profit Factor: {metrics['profit_factor']:.2f}")
    print(f"   Average Win: ${metrics['avg_win']:.2f}")
    print(f"   Average Loss: ${metrics['avg_loss']:.2f}")
    print(f"   Largest Win: ${metrics['largest_win']:.2f}")
    print(f"   Largest Loss: ${metrics['largest_loss']:.2f}")
    print(f"   Average Trade Duration: {metrics['avg_trade_duration']:.1f} hours")
    
    # Risk metrics
    print(f"\n🛡️ Risk Metrics:")
    print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"   Sortino Ratio: {metrics['sortino_ratio']:.2f}")
    print(f"   Max Drawdown: {metrics['max_drawdown']:.2f}%")
    print(f"   Volatility: {metrics['volatility']:.2f}%")
    print(f"   Calmar Ratio: {metrics['calmar_ratio']:.2f}")
    
    # Get performance summary
    print(f"\n📋 Performance Summary:")
    summary = tracker.get_performance_summary()
    
    print(f"   Rating: {summary['rating']}")
    print(f"   Insights:")
    for insight in summary['insights']:
        print(f"     • {insight}")
    
    if summary['recommendations']:
        print(f"   Recommendations:")
        for rec in summary['recommendations']:
            print(f"     • {rec}")
    
    # Test equity curve
    print(f"\n📈 Equity Curve Data (last 10 points):")
    equity_data = tracker.get_equity_curve_data(days=30)
    for point in equity_data[-10:]:
        print(f"   {point['timestamp'][:19]}: ${point['balance']:,.2f} ({point['return']:+.2f}%)")
    
    # Test trade history
    print(f"\n📜 Trade History:")
    trade_history = tracker.get_trade_history(limit=5)
    for trade in trade_history:
        print(f"   {trade['timestamp'][:19]}: {trade['symbol']} {trade['direction']} "
              f"${trade['pnl']:+.2f} ({trade['return_pct']:+.2f}%)")
    
    print(f"\n✅ Performance Tracking Test Completed!")

if __name__ == "__main__":
    test_performance_tracking()
