"""
Real-time Data Store for WebSocket data
Handles storage and retrieval of live market data
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict, deque
import threading
import json
import logging

from data_layer.websocket_manager import TickData, OHLCVData, websocket_manager
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from django.conf import settings

logger = logging.getLogger(__name__)


class RealTimeDataStore:
    """
    Real-time data storage and management
    
    Features:
    - In-memory buffering for fast access
    - InfluxDB persistence for historical data
    - Real-time data validation
    - Connection health monitoring
    - Data quality metrics
    """
    
    def __init__(self):
        self.tick_buffer = defaultdict(lambda: deque(maxlen=1000))  # Last 1000 ticks per symbol
        self.ohlcv_buffer = defaultdict(lambda: deque(maxlen=5000))  # Last 5000 candles per symbol
        self.latest_prices = {}
        self.connection_status = {}
        self.data_quality = defaultdict(lambda: {'last_update': None, 'ticks_per_second': 0})
        
        # Statistics
        self.stats = {
            'total_ticks': 0,
            'total_candles': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
        
        # Start background tasks
        self.is_running = False
        self.background_thread = None
        
        # InfluxDB client
        self.influx_client = None
        
    def start(self):
        """Start the real-time data store"""
        self.is_running = True
        
        # Set up WebSocket callbacks
        websocket_manager.add_callback('tick', self._on_tick_received)
        websocket_manager.add_callback('ohlcv', self._on_ohlcv_received)
        websocket_manager.add_callback('connection', self._on_connection_status)
        websocket_manager.add_callback('error', self._on_error)
        
        # Initialize InfluxDB client
        try:
            self.influx_client = InfluxDBClient(
                url=settings.INFLUXDB_URL,
                token=settings.INFLUX_TOKEN,
                org=settings.INFLUX_ORG
            )
        except Exception as e:
            logger.error(f"Failed to initialize InfluxDB client: {e}")
        
        # Start background processing thread
        self.background_thread = threading.Thread(target=self._background_processing, daemon=True)
        self.background_thread.start()
        
        logger.info("Real-time data store started")
    
    def stop(self):
        """Stop the real-time data store"""
        self.is_running = False
        
        # Remove callbacks
        websocket_manager.remove_callback('tick', self._on_tick_received)
        websocket_manager.remove_callback('ohlcv', self._on_ohlcv_received)
        websocket_manager.remove_callback('connection', self._on_connection_status)
        websocket_manager.remove_callback('error', self._on_error)
        
        # Close InfluxDB client
        if self.influx_client:
            self.influx_client.close()
        
        logger.info("Real-time data store stopped")
    
    def _on_tick_received(self, tick: TickData):
        """Handle incoming tick data"""
        try:
            # Add to buffer
            self.tick_buffer[tick.symbol].append(tick)
            
            # Update latest price
            self.latest_prices[tick.symbol] = tick
            
            # Update statistics
            self.stats['total_ticks'] += 1
            
            # Update data quality metrics
            now = datetime.now()
            symbol_quality = self.data_quality[tick.symbol]
            
            if symbol_quality['last_update']:
                time_diff = (now - symbol_quality['last_update']).total_seconds()
                if time_diff > 0:
                    symbol_quality['ticks_per_second'] = min(1.0 / time_diff, 1000)  # Cap at 1000 tps
            
            symbol_quality['last_update'] = now
            
            # Store to InfluxDB (async)
            if self.influx_client:
                self._store_tick_to_influx(tick)
                
        except Exception as e:
            logger.error(f"Error processing tick: {e}")
            self.stats['errors'] += 1
    
    def _on_ohlcv_received(self, candle: OHLCVData):
        """Handle incoming OHLCV data"""
        try:
            # Add to buffer
            self.ohlcv_buffer[candle.symbol].append(candle)
            
            # Update statistics
            self.stats['total_candles'] += 1
            
            # Store to InfluxDB (async)
            if self.influx_client:
                self._store_candle_to_influx(candle)
                
        except Exception as e:
            logger.error(f"Error processing candle: {e}")
            self.stats['errors'] += 1
    
    def _on_connection_status(self, status: Dict):
        """Handle connection status updates"""
        provider = status['provider']
        self.connection_status[provider] = {
            'status': status['status'],
            'last_update': datetime.now()
        }
        logger.info(f"Connection status update: {provider} -> {status['status']}")
    
    def _on_error(self, error: Dict):
        """Handle error messages"""
        provider = error['provider']
        logger.error(f"WebSocket error from {provider}: {error['error']}")
        self.stats['errors'] += 1
    
    def _store_tick_to_influx(self, tick: TickData):
        """Store tick data to InfluxDB"""
        try:
            point = Point("ticks") \
                .tag("symbol", tick.symbol) \
                .field("bid", float(tick.bid)) \
                .field("ask", float(tick.ask)) \
                .field("mid", float(tick.mid)) \
                .field("spread", float(tick.spread)) \
                .field("volume", tick.volume) \
                .time(tick.timestamp)
            
            write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
            write_api.write(bucket=settings.INFLUX_BUCKET, record=point)
            
        except Exception as e:
            logger.error(f"Error storing tick to InfluxDB: {e}")
    
    def _store_candle_to_influx(self, candle: OHLCVData):
        """Store OHLCV data to InfluxDB"""
        try:
            point = Point("ohlcv") \
                .tag("symbol", candle.symbol) \
                .tag("timeframe", candle.timeframe) \
                .field("open", float(candle.open)) \
                .field("high", float(candle.high)) \
                .field("low", float(candle.low)) \
                .field("close", float(candle.close)) \
                .field("volume", candle.volume) \
                .time(candle.timestamp)
            
            write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
            write_api.write(bucket=settings.INFLUX_BUCKET, record=point)
            
        except Exception as e:
            logger.error(f"Error storing candle to InfluxDB: {e}")
    
    def _background_processing(self):
        """Background processing tasks"""
        while self.is_running:
            try:
                # Clean up old data
                self._cleanup_old_data()
                
                # Update statistics
                self._update_statistics()
                
                # Sleep for 1 second
                import time
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in background processing: {e}")
                import time
                time.sleep(5)
    
    def _cleanup_old_data(self):
        """Clean up old data from buffers"""
        # Tick buffers are automatically limited by deque maxlen
        # OHLCV buffers are automatically limited by deque maxlen
        
        # Clean up old quality metrics
        cutoff_time = datetime.now() - timedelta(hours=1)
        for symbol in list(self.data_quality.keys()):
            if self.data_quality[symbol]['last_update'] and \
               self.data_quality[symbol]['last_update'] < cutoff_time:
                del self.data_quality[symbol]
    
    def _update_statistics(self):
        """Update statistics"""
        # Calculate uptime
        uptime = datetime.now() - self.stats['start_time']
        self.stats['uptime_seconds'] = uptime.total_seconds()
        
        # Calculate average ticks per second
        if self.stats['uptime_seconds'] > 0:
            self.stats['avg_ticks_per_second'] = self.stats['total_ticks'] / self.stats['uptime_seconds']
    
    def get_latest_tick(self, symbol: str) -> Optional[TickData]:
        """Get latest tick for a symbol"""
        return self.latest_prices.get(symbol)
    
    def get_recent_ticks(self, symbol: str, count: int = 100) -> List[TickData]:
        """Get recent ticks for a symbol"""
        if symbol not in self.tick_buffer:
            return []
        
        return list(self.tick_buffer[symbol])[-count:]
    
    def get_recent_candles(
        self, 
        symbol: str, 
        timeframe: str, 
        count: int = 100
    ) -> List[OHLCVData]:
        """Get recent candles for a symbol and timeframe"""
        if symbol not in self.ohlcv_buffer:
            return []
        
        # Filter by timeframe
        candles = [
            candle for candle in self.ohlcv_buffer[symbol]
            if candle.timeframe == timeframe
        ]
        
        return candles[-count:]
    
    def get_data_quality(self, symbol: str) -> Dict:
        """Get data quality metrics for a symbol"""
        if symbol not in self.data_quality:
            return {
                'status': 'no_data',
                'last_update': None,
                'ticks_per_second': 0
            }
        
        quality = self.data_quality[symbol]
        
        # Determine status
        now = datetime.now()
        if quality['last_update']:
            age_seconds = (now - quality['last_update']).total_seconds()
            
            if age_seconds < 5:
                status = 'excellent'
            elif age_seconds < 30:
                status = 'good'
            elif age_seconds < 120:
                status = 'fair'
            else:
                status = 'poor'
        else:
            status = 'no_data'
        
        return {
            'status': status,
            'last_update': quality['last_update'],
            'ticks_per_second': quality['ticks_per_second'],
            'age_seconds': age_seconds if quality['last_update'] else None
        }
    
    def get_connection_status(self) -> Dict:
        """Get connection status for all providers"""
        return self.connection_status.copy()
    
    def get_statistics(self) -> Dict:
        """Get overall statistics"""
        stats = self.stats.copy()
        
        # Add provider counts
        stats['active_symbols'] = len(self.latest_prices)
        stats['buffered_ticks'] = sum(len(buffer) for buffer in self.tick_buffer.values())
        stats['buffered_candles'] = sum(len(buffer) for buffer in self.ohlcv_buffer.values())
        
        return stats


# Global real-time data store instance
real_time_data_store = RealTimeDataStore()
