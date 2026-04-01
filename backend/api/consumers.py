"""
Django Channels WebSocket Consumers for Real-time Data
"""
import json
import asyncio
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from data_layer.real_time_data_store import real_time_data_store
from data_layer.websocket_manager import websocket_manager


class RealTimeDataConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time market data streaming
    
    Features:
    - Subscribe to specific symbols
    - Receive tick data in real-time
    - Receive OHLCV candle data
    - Connection management
    """
    
    async def connect(self):
        """Accept WebSocket connection"""
        await self.accept()
        
        # Generate unique connection ID
        self.connection_id = f"conn_{datetime.now().timestamp()}"
        
        # Store connection
        self.symbols = set()
        
        print(f"WebSocket connected: {self.connection_id}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Unsubscribe from all symbols
        for symbol in self.symbols:
            await self.unsubscribe_symbol(symbol)
        
        print(f"WebSocket disconnected: {self.connection_id}")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            message = json.loads(text_data)
            message_type = message.get('type')
            
            if message_type == 'subscribe':
                symbol = message.get('symbol')
                if symbol:
                    await self.subscribe_symbol(symbol)
            
            elif message_type == 'unsubscribe':
                symbol = message.get('symbol')
                if symbol:
                    await self.unsubscribe_symbol(symbol)
            
            elif message_type == 'ping':
                # Respond to ping with pong
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                }))
            
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def subscribe_symbol(self, symbol: str):
        """Subscribe to real-time data for a symbol"""
        if symbol not in self.symbols:
            self.symbols.add(symbol)
            
            # Send current latest price if available
            latest_tick = real_time_data_store.get_latest_tick(symbol)
            if latest_tick:
                await self.send(text_data=json.dumps({
                    'type': 'tick',
                    'symbol': symbol,
                    'timestamp': latest_tick.timestamp.isoformat(),
                    'bid': float(latest_tick.bid),
                    'ask': float(latest_tick.ask),
                    'mid': float(latest_tick.mid),
                    'spread': float(latest_tick.spread),
                    'volume': latest_tick.volume
                }))
            
            # Send recent candles
            recent_candles = real_time_data_store.get_recent_candles(symbol, 'M1', 10)
            for candle in recent_candles:
                await self.send(text_data=json.dumps({
                    'type': 'ohlcv',
                    'symbol': symbol,
                    'timestamp': candle.timestamp.isoformat(),
                    'open': float(candle.open),
                    'high': float(candle.high),
                    'low': float(candle.low),
                    'close': float(candle.close),
                    'volume': candle.volume,
                    'timeframe': candle.timeframe
                }))
            
            print(f"Subscribed to {symbol}")
    
    async def unsubscribe_symbol(self, symbol: str):
        """Unsubscribe from real-time data for a symbol"""
        if symbol in self.symbols:
            self.symbols.remove(symbol)
            print(f"Unsubscribed from {symbol}")


class SymbolListConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for symbol list and general information
    """
    
    async def connect(self):
        """Accept WebSocket connection"""
        await self.accept()
        
        # Send available symbols
        await self.send(text_data=json.dumps({
            'type': 'symbols',
            'symbols': [
                'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF',
                'AUDUSD', 'USDCAD', 'NZDUSD', 'EURGBP',
                'EURJPY', 'GBPJPY', 'EURCHF', 'GBPCHF'
            ],
            'timeframes': ['M1', 'M5', 'M15', 'H1', 'H4', 'D1'],
            'message': 'Connected to FX Alpha Platform WebSocket'
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        pass
    
    async def receive(self, text_data):
        """Handle incoming messages"""
        try:
            message = json.loads(text_data)
            message_type = message.get('type')
            
            if message_type == 'get_status':
                # Send system status
                stats = real_time_data_store.get_statistics()
                connections = real_time_data_store.get_connection_status()
                
                await self.send(text_data=json.dumps({
                    'type': 'status',
                    'statistics': stats,
                    'connections': connections,
                    'timestamp': datetime.now().isoformat()
                }))
            
            elif message_type == 'get_quality':
                # Send data quality for all symbols
                symbols = message.get('symbols', ['EURUSD', 'GBPUSD', 'USDJPY'])
                quality_data = {}
                
                for symbol in symbols:
                    quality_data[symbol] = real_time_data_store.get_data_quality(symbol)
                
                await self.send(text_data=json.dumps({
                    'type': 'quality',
                    'quality': quality_data,
                    'timestamp': datetime.now().isoformat()
                }))
            
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }))
                
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))


class RealTimeSignalConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time trading signals
    """
    
    async def connect(self):
        """Accept WebSocket connection"""
        await self.accept()
        self.subscribed_symbols = set()
        
        await self.send(text_data=json.dumps({
            'type': 'connected',
            'message': 'Connected to real-time signal stream'
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        pass
    
    async def receive(self, text_data):
        """Handle incoming messages"""
        try:
            message = json.loads(text_data)
            message_type = message.get('type')
            
            if message_type == 'subscribe_signals':
                symbols = message.get('symbols', ['EURUSD'])
                self.subscribed_symbols = set(symbols)
                
                await self.send(text_data=json.dumps({
                    'type': 'subscription_confirmed',
                    'symbols': list(self.subscribed_symbols)
                }))
            
            elif message_type == 'generate_signal':
                symbol = message.get('symbol', 'EURUSD')
                
                # Generate signal (this would call the signal generation API)
                await self.send(text_data=json.dumps({
                    'type': 'signal_generating',
                    'symbol': symbol,
                    'message': f'Generating signal for {symbol}...'
                }))
                
                # Here you would integrate with the signal generation system
                # For now, send a mock signal
                await asyncio.sleep(1)  # Simulate processing time
                
                await self.send(text_data=json.dumps({
                    'type': 'signal_generated',
                    'symbol': symbol,
                    'signal': {
                        'direction': 'BUY',
                        'confidence': 0.75,
                        'reasoning': 'Multi-agent consensus: Technical bullish, Macro neutral, Sentiment positive',
                        'timestamp': datetime.now().isoformat()
                    }
                }))
            
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }))
                
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
