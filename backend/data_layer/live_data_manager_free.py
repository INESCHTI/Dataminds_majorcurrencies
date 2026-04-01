"""
FREE Live Data Manager - Only FREE Data Sources
Integrates MetaTrader5 and free data providers - NO PAID APIS
"""
import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
import logging
import pandas as pd

from core.database import DatabaseManager

logger = logging.getLogger(__name__)

@dataclass
class FreeLiveDataConfig:
    """Configuration for FREE data sources only"""
    mt5_enabled: bool = True  # MetaTrader5 (FREE with demo account)
    fallback_to_simulation: bool = False  # ELIMINATED - No simulation fallback
    update_interval_ms: int = 1000
    reconnect_interval_s: int = 30
    max_reconnect_attempts: int = 5
    # Free RSS feeds for market data
    free_rss_enabled: bool = True

class FreeLiveDataManager:
    """
    FREE Live Data Manager - Only uses FREE data sources
    
    Data Sources:
    1. MetaTrader5 (FREE demo account)
    2. InfluxDB historical data (FREE)
    3. Free RSS feeds for market sentiment
    4. FRED API (FREE economic data)
    """
    
    def __init__(self, config: Optional[FreeLiveDataConfig] = None):
        self.config = config or FreeLiveDataConfig()
        self.is_running = False
        self.tick_callbacks: List[Callable] = []
        self.ohlcv_callbacks: List[Callable] = []
        self.error_callbacks: List[Callable] = []
        
        # MT5 connection (FREE)
        self.mt5_connected = False
        
        # Data cache
        self.latest_ticks: Dict[str, Dict] = {}
        self.latest_ohlcv: Dict[str, Dict] = {}
        
        # Statistics
        self.stats = {
            'ticks_received': 0,
            'last_update': None,
            'connected_sources': [],
            'errors': 0
        }
    
    def add_tick_callback(self, callback: Callable):
        """Add callback for tick data"""
        self.tick_callbacks.append(callback)
    
    def add_ohlcv_callback(self, callback: Callable):
        """Add callback for OHLCV data"""
        self.ohlcv_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable):
        """Add callback for error handling"""
        self.error_callbacks.append(callback)
    
    def start(self):
        """Start FREE data collection"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Starting FREE Live Data Manager...")
        
        # Start MT5 connection (FREE)
        if self.config.mt5_enabled:
            self._start_mt5_collection()
        
        # Start InfluxDB data streaming (FREE)
        self._start_influxdb_streaming()
        
        logger.info("FREE Live Data Manager started successfully")
    
    def stop(self):
        """Stop data collection"""
        self.is_running = False
        logger.info("FREE Live Data Manager stopped")
    
    def _start_mt5_collection(self):
        """Start MetaTrader5 data collection (FREE)"""
        def mt5_worker():
            try:
                import MetaTrader5 as mt5
                
                # Connect to MT5 (FREE demo account)
                if mt5.initialize():
                    login = int(os.getenv('MT5_LOGIN', '5046521974'))
                    password = os.getenv('MT5_PASSWORD', 'W_Mr5kFd')
                    server = os.getenv('MT5_SERVER', 'MetaQuotes-Demo')
                    
                    if mt5.login(login, password, server):
                        self.mt5_connected = True
                        self.stats['connected_sources'].append('MT5')
                        logger.info(f"Connected to MT5: {server}")
                        
                        # Collect real-time data
                        symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF']
                        
                        while self.is_running:
                            try:
                                for symbol in symbols:
                                    # Get tick data
                                    tick = mt5.symbol_info_tick(symbol)
                                    if tick:
                                        self._process_mt5_tick(symbol, tick)
                                
                                # Get OHLCV data
                                for symbol in symbols:
                                    candles = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 1)
                                    if candles and len(candles) > 0:
                                        self._process_mt5_candle(symbol, candles[0])
                                
                                time.sleep(self.config.update_interval_ms / 1000)
                                
                            except Exception as e:
                                logger.error(f"MT5 data error: {e}")
                                self.stats['errors'] += 1
                                time.sleep(5)  # Wait before retry
                        
                        mt5.shutdown()
                    else:
                        logger.error(f"MT5 login failed: {mt5.last_error()}")
                else:
                    logger.error(f"MT5 initialize failed: {mt5.last_error()}")
                    
            except ImportError:
                logger.warning("MetaTrader5 not installed - using InfluxDB only")
            except Exception as e:
                logger.error(f"MT5 connection failed: {e}")
                self.stats['errors'] += 1
        
        # Start MT5 worker thread
        mt5_thread = threading.Thread(target=mt5_worker, daemon=True)
        mt5_thread.start()
    
    def _start_influxdb_streaming(self):
        """Start InfluxDB data streaming (FREE)"""
        def influxdb_worker():
            while self.is_running:
                try:
                    # Get latest data from InfluxDB
                    with DatabaseManager.get_influx_client() as client:
                        query_api = client.query_api()
                        
                        # Query recent OHLCV data
                        query = '''
                        from(bucket: "forex_data")
                          |> range(start: -5m)
                          |> filter(fn: (r) => r["_measurement"] == "ohlcv")
                          |> filter(fn: (r) => r["_field"] == "close")
                          |> group(columns: ["symbol"])
                          |> last()
                        '''
                        
                        result = query_api.query(query)
                        
                        for table in result:
                            for record in table.records:
                                symbol = record.values.get('symbol')
                                price = record.get_value()
                                timestamp = record.get_time()
                                
                                if symbol and price:
                                    # Create synthetic tick from InfluxDB
                                    tick_data = {
                                        'symbol': symbol,
                                        'bid': price,
                                        'ask': price + 0.0001,  # Small spread
                                        'timestamp': timestamp,
                                        'source': 'InfluxDB'
                                    }
                                    
                                    self._process_tick_data(tick_data)
                    
                    time.sleep(10)  # Update every 10 seconds
                    
                except Exception as e:
                    logger.error(f"InfluxDB streaming error: {e}")
                    self.stats['errors'] += 1
                    time.sleep(30)  # Wait before retry
        
        # Start InfluxDB worker thread
        influxdb_thread = threading.Thread(target=influxdb_worker, daemon=True)
        influxdb_thread.start()
    
    def _process_mt5_tick(self, symbol: str, tick):
        """Process MT5 tick data"""
        tick_data = {
            'symbol': symbol,
            'bid': tick.bid,
            'ask': tick.ask,
            'timestamp': datetime.fromtimestamp(tick.time),
            'source': 'MT5'
        }
        
        self._process_tick_data(tick_data)
    
    def _process_mt5_candle(self, symbol: str, candle):
        """Process MT5 OHLCV candle"""
        ohlcv_data = {
            'symbol': symbol,
            'open': candle[1],
            'high': candle[2],
            'low': candle[3],
            'close': candle[4],
            'volume': candle[5],
            'timestamp': datetime.fromtimestamp(candle[0]),
            'source': 'MT5'
        }
        
        self._process_ohlcv_data(ohlcv_data)
    
    def _process_tick_data(self, tick_data: Dict):
        """Process incoming tick data"""
        try:
            symbol = tick_data['symbol']
            
            # Update cache
            self.latest_ticks[symbol] = tick_data
            self.stats['ticks_received'] += 1
            self.stats['last_update'] = datetime.now()
            
            # Notify callbacks
            for callback in self.tick_callbacks:
                try:
                    callback(tick_data)
                except Exception as e:
                    logger.error(f"Tick callback error: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing tick data: {e}")
            self.stats['errors'] += 1
    
    def _process_ohlcv_data(self, ohlcv_data: Dict):
        """Process incoming OHLCV data"""
        try:
            symbol = ohlcv_data['symbol']
            
            # Update cache
            self.latest_ohlcv[symbol] = ohlcv_data
            
            # Notify callbacks
            for callback in self.ohlcv_callbacks:
                try:
                    callback(ohlcv_data)
                except Exception as e:
                    logger.error(f"OHLCV callback error: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing OHLCV data: {e}")
            self.stats['errors'] += 1
    
    def get_latest_tick(self, symbol: str) -> Optional[Dict]:
        """Get latest tick for symbol"""
        return self.latest_ticks.get(symbol)
    
    def get_latest_ohlcv(self, symbol: str) -> Optional[Dict]:
        """Get latest OHLCV for symbol"""
        return self.latest_ohlcv.get(symbol)
    
    def get_statistics(self) -> Dict:
        """Get collection statistics"""
        return {
            **self.stats,
            'is_running': self.is_running,
            'mt5_connected': self.mt5_connected,
            'active_symbols': list(self.latest_ticks.keys()),
            'config': {
                'mt5_enabled': self.config.mt5_enabled,
                'update_interval_ms': self.config.update_interval_ms,
            }
        }
    
    def get_supported_symbols(self) -> List[str]:
        """Get list of supported symbols"""
        return ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF']
    
    def is_symbol_supported(self, symbol: str) -> bool:
        """Check if symbol is supported"""
        return symbol in self.get_supported_symbols()


# Singleton instance for FREE data manager
_free_live_data_manager = None

def get_free_live_data_manager() -> FreeLiveDataManager:
    """Get singleton instance of FREE live data manager"""
    global _free_live_data_manager
    if _free_live_data_manager is None:
        _free_live_data_manager = FreeLiveDataManager()
    return _free_live_data_manager


def start_free_live_data():
    """Start FREE live data collection"""
    manager = get_free_live_data_manager()
    manager.start()
    return manager


def stop_free_live_data():
    """Stop FREE live data collection"""
    manager = get_free_live_data_manager()
    manager.stop()
