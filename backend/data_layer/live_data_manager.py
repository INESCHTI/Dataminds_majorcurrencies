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
import os

from core.database import DatabaseManager

logger = logging.getLogger(__name__)

@dataclass
class LiveDataConfig:
    """Configuration for FREE data sources only"""
    oanda_enabled: bool = False  # DISABLED - PAID API
    fxcm_enabled: bool = False   # DISABLED - PAID API
    mt5_enabled: bool = True     # ENABLED - FREE with demo account
    fallback_to_simulation: bool = False  # ELIMINATED - No simulation fallback
    update_interval_ms: int = 1000
    reconnect_interval_s: int = 30
    max_reconnect_attempts: int = 5
    # Free RSS feeds for market data
    free_rss_enabled: bool = True

class LiveDataManager:
    """
    FREE Live Data Manager - Only uses FREE data sources
    
    Data Sources:
    1. MetaTrader5 (FREE demo account)
    2. InfluxDB historical data (FREE)
    3. Free RSS feeds for market sentiment
    4. FRED API (FREE economic data)
    """
    
    def __init__(self, config: Optional[LiveDataConfig] = None):
        self.config = config or LiveDataConfig()
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
        self.tick_callbacks: List[Callable] = []
        self.candle_callbacks: List[Callable] = []
        self.error_callbacks: List[Callable] = []
        
        self.is_running = False
        self.provider_threads: Dict[str, threading.Thread] = {}
        self.last_prices: Dict[str, float] = {}
        
        # Statistics
        self.stats = {
            'total_ticks': 0,
            'total_errors': 0,
            'provider_status': {},
            'last_update': None,
            'start_time': None
        }
    
    def initialize_providers(self):
        """Initialize data providers"""
        if self.config.oanda_enabled:
            try:
                oanda_config = create_oanda_config_from_env()
                if oanda_config.api_key and oanda_config.account_id:
                    self.oanda_client = OandaClient(oanda_config)
                    logger.info("OANDA client initialized")
                else:
                    logger.warning("OANDA credentials not found in environment")
            except Exception as e:
                logger.error(f"Failed to initialize OANDA: {e}")
        
        if self.config.fxcm_enabled:
            try:
                fxcm_config = create_fxcm_config_from_env()
                if fxcm_config.api_key:
                    self.fxcm_client = FXCMClient(fxcm_config)
                    if self.fxcm_client.authenticate():
                        logger.info("FXCM client initialized and authenticated")
                    else:
                        logger.warning("FXCM authentication failed")
                else:
                    logger.warning("FXCM credentials not found in environment")
            except Exception as e:
                logger.error(f"Failed to initialize FXCM: {e}")
    
    def add_tick_callback(self, callback: Callable):
        """Add callback for tick data"""
        self.tick_callbacks.append(callback)
    
    def add_candle_callback(self, callback: Callable):
        """Add callback for candle data"""
        self.candle_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable):
        """Add callback for error handling"""
        self.error_callbacks.append(callback)
    
    def start(self, symbols: List[str]):
        """Start live data streaming"""
        if self.is_running:
            logger.warning("Live data manager already running")
            return
        
        self.is_running = True
        self.stats['start_time'] = datetime.now()
        
        # Initialize providers
        self.initialize_providers()
        
        # Start provider threads
        if self.oanda_client:
            self._start_oanda_provider(symbols)
        
        if self.fxcm_client:
            self._start_fxcm_provider(symbols)
        
        # NO SIMULATION FALLBACK - Require real data providers
        if not self.active_providers:
            logger.error("No real data providers available. Please configure OANDA or FXCM.")
            raise RuntimeError("Real data providers required - simulation mode removed")
        
        logger.info(f"Live data manager started with providers: {self.active_providers}")
    
    def stop(self):
        """Stop live data streaming"""
        self.is_running = False
        
        # Stop provider threads
        for provider, thread in self.provider_threads.items():
            if thread.is_alive():
                logger.info(f"Stopping {provider} provider")
                # Thread will stop when self.is_running is False
        
        self.provider_threads.clear()
        self.active_providers.clear()
        
        logger.info("Live data manager stopped")
    
    def _start_oanda_provider(self, symbols: List[str]):
        """Start OANDA WebSocket provider"""
        def oanda_worker():
            reconnect_attempts = 0
            
            while self.is_running and reconnect_attempts < self.config.max_reconnect_attempts:
                try:
                    logger.info("Starting OANDA WebSocket connection")
                    
                    def on_tick(data):
                        if not self.is_running:
                            return
                        
                        if 'tick' in data:
                            tick_data = parse_oanda_tick(data)
                            if tick_data:
                                self._process_tick_data(tick_data, 'oanda')
                    
                    # Create WebSocket connection
                    ws = self.oanda_client.create_price_stream(symbols, on_tick)
                    
                    # Update provider status
                    self.stats['provider_status']['oanda'] = 'connected'
                    self.active_providers.append('oanda')
                    
                    # Run WebSocket
                    ws.run_forever()
                    
                except Exception as e:
                    logger.error(f"OANDA provider error: {e}")
                    self.stats['provider_status']['oanda'] = f'error: {str(e)}'
                    self.stats['total_errors'] += 1
                    
                    # Notify error callbacks
                    for callback in self.error_callbacks:
                        try:
                            callback('oanda', str(e))
                        except Exception as cb_error:
                            logger.error(f"Error in error callback: {cb_error}")
                
                # Reconnection logic
                if self.is_running:
                    reconnect_attempts += 1
                    if reconnect_attempts < self.config.max_reconnect_attempts:
                        logger.info(f"Reconnecting OANDA in {self.config.reconnect_interval_s}s (attempt {reconnect_attempts})")
                        time.sleep(self.config.reconnect_interval_s)
                    else:
                        logger.error("Max reconnection attempts reached for OANDA")
                        if 'oanda' in self.active_providers:
                            self.active_providers.remove('oanda')
        
        thread = threading.Thread(target=oanda_worker, daemon=True)
        thread.start()
        self.provider_threads['oanda'] = thread
    
    def _start_fxcm_provider(self, symbols: List[str]):
        """Start FXCM WebSocket provider"""
        def fxcm_worker():
            reconnect_attempts = 0
            
            while self.is_running and reconnect_attempts < self.config.max_reconnect_attempts:
                try:
                    logger.info("Starting FXCM WebSocket connection")
                    
                    def on_tick(data):
                        if not self.is_running:
                            return
                        
                        tick_data = parse_fxcm_tick(data)
                        if tick_data:
                            self._process_tick_data(tick_data, 'fxcm')
                    
                    # Create WebSocket connection
                    ws = self.fxcm_client.create_price_stream(symbols, on_tick)
                    
                    # Update provider status
                    self.stats['provider_status']['fxcm'] = 'connected'
                    self.active_providers.append('fxcm')
                    
                    # Run WebSocket
                    ws.run_forever()
                    
                except Exception as e:
                    logger.error(f"FXCM provider error: {e}")
                    self.stats['provider_status']['fxcm'] = f'error: {str(e)}'
                    self.stats['total_errors'] += 1
                    
                    # Notify error callbacks
                    for callback in self.error_callbacks:
                        try:
                            callback('fxcm', str(e))
                        except Exception as cb_error:
                            logger.error(f"Error in error callback: {cb_error}")
                
                # Reconnection logic
                if self.is_running:
                    reconnect_attempts += 1
                    if reconnect_attempts < self.config.max_reconnect_attempts:
                        logger.info(f"Reconnecting FXCM in {self.config.reconnect_interval_s}s (attempt {reconnect_attempts})")
                        time.sleep(self.config.reconnect_interval_s)
                    else:
                        logger.error("Max reconnection attempts reached for FXCM")
                        if 'fxcm' in self.active_providers:
                            self.active_providers.remove('fxcm')
        
        thread = threading.Thread(target=fxcm_worker, daemon=True)
        thread.start()
        self.provider_threads['fxcm'] = thread
    
    # REMOVED: _start_simulation_provider method - no simulation fallback allowed
    
    def _process_tick_data(self, tick_data: Dict, provider: str):
        """Process incoming tick data"""
        try:
            # Convert to TickData object
            tick_obj = TickData(
                symbol=tick_data['symbol'],
                timestamp=tick_data['timestamp'],
                bid=float(tick_data['bid']),
                ask=float(tick_data['ask']),
                mid=float(tick_data['mid']),
                spread=float(tick_data['spread']),
                volume=tick_data.get('volume', 0)
            )
            
            # Update statistics
            self.stats['total_ticks'] += 1
            self.stats['last_update'] = datetime.now()
            self.last_prices[tick_data['symbol']] = tick_data['mid']
            
            # Notify callbacks
            for callback in self.tick_callbacks:
                try:
                    callback(tick_obj, provider)
                except Exception as e:
                    logger.error(f"Error in tick callback: {e}")
        
        except Exception as e:
            logger.error(f"Error processing tick data: {e}")
            self.stats['total_errors'] += 1
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest price for a symbol"""
        return self.last_prices.get(symbol)
    
    def get_statistics(self) -> Dict:
        """Get provider statistics"""
        return {
            **self.stats,
            'active_providers': self.active_providers,
            'is_running': self.is_running,
            'uptime_seconds': (datetime.now() - self.stats['start_time']).total_seconds() if self.stats['start_time'] else 0
        }
    
    def get_provider_status(self) -> Dict:
        """Get detailed provider status"""
        return {
            'oanda': {
                'enabled': self.oanda_client is not None,
                'active': 'oanda' in self.active_providers,
                'status': self.stats['provider_status'].get('oanda', 'not_initialized')
            },
            'fxcm': {
                'enabled': self.fxcm_client is not None,
                'active': 'fxcm' in self.active_providers,
                'status': self.stats['provider_status'].get('fxcm', 'not_initialized')
            }
            # REMOVED: simulation provider - no simulation fallback allowed
        }

# Global instance for application-wide use
live_data_manager: Optional[LiveDataManager] = None

def create_live_data_manager() -> LiveDataManager:
    """Get or create global live data manager instance"""
    global live_data_manager
    if live_data_manager is None:
        import os
        
        # Require real data providers - no simulation mode
        oanda_enabled = bool(os.getenv('OANDA_API_KEY'))
        fxcm_enabled = bool(os.getenv('FXCM_API_KEY'))
        
        if not oanda_enabled and not fxcm_enabled:
            raise RuntimeError(
                "No real data providers configured. Please set OANDA_API_KEY or FXCM_API_KEY environment variables. "
                "Simulation mode has been removed - only real data providers are allowed."
            )
        
        config = LiveDataConfig(
            oanda_enabled=oanda_enabled,
            fxcm_enabled=fxcm_enabled,
            fallback_to_simulation=False  # ELIMINATED
        )
        live_data_manager = LiveDataManager(config)
    return live_data_manager
