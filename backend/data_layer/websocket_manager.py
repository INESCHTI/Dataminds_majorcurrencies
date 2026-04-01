"""
WebSocket Manager for Real-time FX Data
Handles connections to multiple FX data providers
"""
import asyncio
import websockets
import json
import logging
from datetime import datetime
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass
from decimal import Decimal
import threading
import time

logger = logging.getLogger(__name__)


@dataclass
class TickData:
    """Real-time tick data structure"""
    symbol: str
    timestamp: datetime
    bid: Decimal
    ask: Decimal
    mid: Decimal
    spread: Decimal
    volume: int


@dataclass
class OHLCVData:
    """OHLCV candle data"""
    symbol: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    timeframe: str


class WebSocketManager:
    """
    Manages WebSocket connections for real-time FX data
    
    Features:
    - Multiple provider support (OANDA, Forex.com, etc.)
    - Automatic reconnection
    - Data buffering and aggregation
    - Real-time candle generation
    - Connection health monitoring
    """
    
    def __init__(self):
        self.connections = {}
        self.callbacks = {
            'tick': [],
            'ohlcv': [],
            'connection': [],
            'error': []
        }
        self.is_running = False
        self.buffer = {}
        self.last_prices = {}
        self.candle_builders = {}
        
        # Configuration for different timeframes
        self.timeframes = {
            'M1': 60,      # 1 minute
            'M5': 300,     # 5 minutes
            'M15': 900,    # 15 minutes
            'H1': 3600,    # 1 hour
            'H4': 14400,   # 4 hours
            'D1': 86400    # 1 day
        }
    
    def add_callback(self, event_type: str, callback: Callable):
        """Add callback for specific events"""
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
    
    def remove_callback(self, event_type: str, callback: Callable):
        """Remove callback for specific events"""
        if event_type in self.callbacks and callback in self.callbacks[event_type]:
            self.callbacks[event_type].remove(callback)
    
    def _emit(self, event_type: str, data):
        """Emit event to all registered callbacks"""
        for callback in self.callbacks.get(event_type, []):
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error in callback for {event_type}: {e}")
    
    async def connect_oanda_stream(self, symbols: List[str], api_key: str, account_id: str):
        """
        Connect to OANDA WebSocket stream
        
        Args:
            symbols: List of currency pairs (e.g., ['EUR_USD', 'GBP_USD'])
            api_key: OANDA API key
            account_id: OANDA account ID
        """
        uri = f"wss://stream-fxpractice.oanda.com/v3/accounts/{account_id}/pricing"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Subscribe to price stream
        subscribe_msg = {
            "event": "subscribe",
            "instruments": symbols
        }
        
        while self.is_running:
            try:
                async with websockets.connect(uri, extra_headers=headers) as websocket:
                    await websocket.send(json.dumps(subscribe_msg))
                    self._emit('connection', {'provider': 'oanda', 'status': 'connected'})
                    
                    async for message in websocket:
                        if not self.is_running:
                            break
                        await self._process_oanda_message(message)
                        
            except websockets.exceptions.ConnectionClosed:
                self._emit('connection', {'provider': 'oanda', 'status': 'disconnected'})
                logger.warning("OANDA WebSocket connection closed, reconnecting...")
                await asyncio.sleep(5)
            except Exception as e:
                self._emit('error', {'provider': 'oanda', 'error': str(e)})
                logger.error(f"OANDA WebSocket error: {e}")
                await asyncio.sleep(10)
    
    async def connect_forexcom_stream(self, symbols: List[str]):
        """
        Connect to free Forex data API (Alpha Vantage)
        Using real forex data instead of simulation
        """
        import aiohttp
        import os
        
        # Use Alpha Vantage free API for real forex data
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        base_url = "https://www.alphavantage.co/query"
        
        headers = {
            'User-Agent': 'FX-Alpha-Platform/1.0'
        }
        
        while self.is_running:
            try:
                async with aiohttp.ClientSession() as session:
                    for symbol in symbols:
                        # Convert EURUSD to EUR/USD format for Alpha Vantage
                        from_symbol = symbol[:3]
                        to_symbol = symbol[3:]
                        
                        params = {
                            'function': 'CURRENCY_EXCHANGE_RATE',
                            'from_currency': from_symbol,
                            'to_currency': to_symbol,
                            'apikey': api_key
                        }
                        
                        async with session.get(base_url, params=params, headers=headers) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                # Extract real exchange rate data
                                if 'Realtime Currency Exchange Rate' in data:
                                    rate_data = data['Realtime Currency Exchange Rate']
                                    exchange_rate = Decimal(rate_data['5. Exchange Rate'])
                                    bid = exchange_rate - Decimal('0.0001')  # Approximate spread
                                    ask = exchange_rate + Decimal('0.0001')
                                    
                                    tick = TickData(
                                        symbol=symbol,
                                        timestamp=datetime.now(),
                                        bid=bid,
                                        ask=ask,
                                        mid=exchange_rate,
                                        spread=ask - bid,
                                        volume=1000000  # Default volume
                                    )
                                    
                                    self._emit('tick', tick)
                                    self._update_candle_builders(tick)
                                
                                # Rate limit: Alpha Vantage free tier allows 5 calls per minute
                                await asyncio.sleep(12)  # 12 seconds between calls
                        
                        # Additional rate limiting
                        await asyncio.sleep(2)
                        
            except Exception as e:
                self._emit('error', {'provider': 'alphavantage', 'error': str(e)})
                logger.error(f"Alpha Vantage API error: {e}")
                await asyncio.sleep(30)
    
    async def _process_oanda_message(self, message: str):
        """Process incoming OANDA WebSocket message"""
        try:
            data = json.loads(message)
            
            if data.get('type') == 'PRICE':
                # Extract price data
                instrument = data.get('instrument', '').replace('_', '')  # EUR_USD -> EURUSD
                timestamp = datetime.fromisoformat(data['time'].replace('Z', '+00:00'))
                
                bid = Decimal(str(data.get('bids', [{}])[0].get('price', 0)))
                ask = Decimal(str(data.get('asks', [{}])[0].get('price', 0)))
                mid = (bid + ask) / 2
                spread = ask - bid
                volume = int(data.get('volume', 0))
                
                tick = TickData(
                    symbol=instrument,
                    timestamp=timestamp,
                    bid=bid,
                    ask=ask,
                    mid=mid,
                    spread=spread,
                    volume=volume
                )
                
                self._emit('tick', tick)
                self._update_candle_builders(tick)
                
        except Exception as e:
            logger.error(f"Error processing OANDA message: {e}")
    
    def _generate_simulated_tick(self, symbol: str) -> TickData:
        """Generate realistic simulated tick data"""
        now = datetime.now()
        
        # Get last price or initialize
        if symbol not in self.last_prices:
            # Initial prices for major pairs
            initial_prices = {
                'EURUSD': Decimal('1.0850'),
                'GBPUSD': Decimal('1.2650'),
                'USDJPY': Decimal('149.50'),
                'USDCHF': Decimal('0.8820'),
                'AUDUSD': Decimal('0.6520'),
                'USDCAD': Decimal('1.3580')
            }
            self.last_prices[symbol] = initial_prices.get(symbol, Decimal('1.0000'))
        
        last_price = self.last_prices[symbol]
        
        # Generate realistic price movement
        import random
        change_percent = random.uniform(-0.0001, 0.0001)  # ±0.01% max change
        new_price = float(last_price) * (1 + change_percent)
        
        # Calculate bid/ask spread
        spread_bps = random.uniform(0.5, 2.0)  # 0.5-2 pips spread
        spread_value = new_price * (spread_bps / 10000)
        
        bid = new_price - (spread_value / 2)
        ask = new_price + (spread_value / 2)
        
        tick = TickData(
            symbol=symbol,
            timestamp=now,
            bid=Decimal(str(bid)),
            ask=Decimal(str(ask)),
            mid=Decimal(str(new_price)),
            spread=Decimal(str(spread_value)),
            volume=random.randint(1000000, 10000000)  # 1M-10M volume
        )
        
        self.last_prices[symbol] = Decimal(str(new_price))
        return tick
    
    def _update_candle_builders(self, tick: TickData):
        """Update candle builders for all timeframes"""
        symbol = tick.symbol
        
        # Initialize candle builders for this symbol if needed
        if symbol not in self.candle_builders:
            self.candle_builders[symbol] = {}
            for tf_name, tf_seconds in self.timeframes.items():
                self.candle_builders[symbol][tf_name] = {
                    'open': tick.mid,
                    'high': tick.mid,
                    'low': tick.mid,
                    'close': tick.mid,
                    'volume': 0,
                    'start_time': self._get_candle_start_time(tick.timestamp, tf_seconds),
                    'is_complete': False
                }
        
        # Update each timeframe
        for tf_name, tf_seconds in self.timeframes.items():
            builder = self.candle_builders[symbol][tf_name]
            
            # Check if current tick belongs to this candle
            candle_start = self._get_candle_start_time(tick.timestamp, tf_seconds)
            
            if candle_start != builder['start_time']:
                # Previous candle is complete, emit it
                if not builder['is_complete'] and builder['start_time']:
                    candle = OHLCVData(
                        symbol=symbol,
                        timestamp=builder['start_time'],
                        open=builder['open'],
                        high=builder['high'],
                        low=builder['low'],
                        close=builder['close'],
                        volume=builder['volume'],
                        timeframe=tf_name
                    )
                    self._emit('ohlcv', candle)
                
                # Start new candle
                builder.update({
                    'open': tick.mid,
                    'high': tick.mid,
                    'low': tick.mid,
                    'close': tick.mid,
                    'volume': tick.volume,
                    'start_time': candle_start,
                    'is_complete': False
                })
            else:
                # Update current candle
                builder['high'] = max(builder['high'], tick.mid)
                builder['low'] = min(builder['low'], tick.mid)
                builder['close'] = tick.mid
                builder['volume'] += tick.volume
    
    def _get_candle_start_time(self, timestamp: datetime, timeframe_seconds: int) -> datetime:
        """Get the start time of the candle for given timestamp"""
        timestamp_ts = timestamp.timestamp()
        candle_start_ts = int(timestamp_ts / timeframe_seconds) * timeframe_seconds
        return datetime.fromtimestamp(candle_start_ts)
    
    def start(self, symbols: List[str], providers: Dict[str, Dict]):
        """
        Start WebSocket connections
        
        Args:
            symbols: List of currency pairs
            providers: Provider configuration
                {
                    'oanda': {'api_key': 'xxx', 'account_id': 'xxx'},
                    'forexcom': {}
                }
        """
        self.is_running = True
        
        # Start connection threads
        for provider_name, config in providers.items():
            if provider_name == 'oanda':
                thread = threading.Thread(
                    target=lambda: asyncio.run(
                        self.connect_oanda_stream(
                            symbols=[s.replace('/', '_') for s in symbols],  # OANDA format
                            api_key=config['api_key'],
                            account_id=config['account_id']
                        )
                    ),
                    daemon=True
                )
                thread.start()
                
            elif provider_name == 'alphavantage':
                thread = threading.Thread(
                    target=lambda: asyncio.run(self.connect_forexcom_stream(symbols)),
                    daemon=True
                )
                thread.start()
        
        logger.info(f"WebSocket manager started for symbols: {symbols}")
    
    def stop(self):
        """Stop all WebSocket connections"""
        self.is_running = False
        logger.info("WebSocket manager stopped")
    
    def get_latest_price(self, symbol: str) -> Optional[TickData]:
        """Get latest price for a symbol"""
        return self.last_prices.get(symbol)
    
    def get_buffered_data(self, symbol: str, count: int = 100) -> List[OHLCVData]:
        """Get buffered OHLCV data for a symbol"""
        if symbol not in self.buffer:
            return []
        
        return self.buffer[symbol][-count:]


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
