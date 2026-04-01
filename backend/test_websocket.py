"""
Test script for WebSocket service
"""
import os
import sys
import django
import time
import json
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append('d:/Téléchargements/trady/backend')
django.setup()

from data_layer.websocket_manager import websocket_manager
from data_layer.real_time_data_store import real_time_data_store

def on_tick_received(tick):
    """Handle incoming tick data"""
    print(f"📈 Tick: {tick.symbol} | Bid: {tick.bid} | Ask: {tick.ask} | Spread: {tick.spread}")

def on_ohlcv_received(candle):
    """Handle incoming OHLCV data"""
    print(f"📊 Candle: {candle.symbol} {candle.timeframe} | O: {candle.open} | H: {candle.high} | L: {candle.low} | C: {candle.close}")

def on_connection_status(status):
    """Handle connection status updates"""
    print(f"🔗 Connection: {status}")

def on_error(error):
    """Handle error messages"""
    print(f"❌ Error: {error}")

def main():
    print("🚀 Starting WebSocket Service Test")
    print("=" * 50)
    
    # Register callbacks
    websocket_manager.add_callback('tick', on_tick_received)
    websocket_manager.add_callback('ohlcv', on_ohlcv_received)
    websocket_manager.add_callback('connection', on_connection_status)
    websocket_manager.add_callback('error', on_error)
    
    # Start real-time data store
    print("📦 Starting real-time data store...")
    real_time_data_store.start()
    
    # Start WebSocket manager
    print("🔌 Starting WebSocket manager...")
    symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
    providers = {'forexcom': {}}  # Using simulated provider
    
    websocket_manager.start(symbols, providers)
    
    print(f"✅ WebSocket service started for symbols: {symbols}")
    print("📊 Streaming real-time data...")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        # Keep the service running
        while True:
            time.sleep(10)
            
            # Print statistics
            stats = real_time_data_store.get_statistics()
            print(f"📈 Stats: {stats.get('total_ticks', 0)} ticks, {stats.get('total_candles', 0)} candles, {stats.get('active_symbols', 0)} active symbols")
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping WebSocket service...")
        
        # Stop services
        websocket_manager.stop()
        real_time_data_store.stop()
        
        print("✅ WebSocket service stopped")
        print("👋 Goodbye!")

if __name__ == '__main__':
    main()
