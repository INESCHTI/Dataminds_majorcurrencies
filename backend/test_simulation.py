#!/usr/bin/env python
"""
Test script for simulation mode
"""
import os
import sys
import django
import time

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from data_layer.live_data_manager import create_live_data_manager

def test_simulation_mode():
    """Test the live data manager in simulation mode"""
    print("🚀 Testing Live Data Manager in Simulation Mode")
    print("=" * 50)
    
    # Create manager
    manager = create_live_data_manager()
    
    # Check initial status
    print("📊 Initial Status:")
    print(f"   Active providers: {manager.active_providers}")
    print(f"   Provider status: {manager.get_provider_status()}")
    
    # Start simulation
    symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF']
    print(f"\n🎬 Starting simulation for: {symbols}")
    manager.start(symbols)
    
    # Wait for data
    print("⏳ Waiting 5 seconds for data...")
    time.sleep(5)
    
    # Check results
    stats = manager.get_statistics()
    print(f"\n📈 Results after 5 seconds:")
    print(f"   Total ticks: {stats['total_ticks']}")
    print(f"   Total errors: {stats['total_errors']}")
    print(f"   Is running: {stats['is_running']}")
    print(f"   Uptime: {stats['uptime_seconds']:.1f}s")
    
    # Show latest prices
    print(f"\n💰 Latest Prices:")
    for symbol, price in list(manager.last_prices.items())[:4]:
        print(f"   {symbol}: {price:.5f}")
    
    # Stop the manager
    print(f"\n🛑 Stopping live data...")
    manager.stop()
    
    print("✅ Test completed successfully!")

if __name__ == "__main__":
    test_simulation_mode()
