"""
WebSocket API Views for Real-time Data
Provides WebSocket endpoints for live market data streaming
"""
import json
import asyncio
from datetime import datetime
from typing import Dict, Set
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from data_layer.websocket_manager import websocket_manager, TickData, OHLCVData
from data_layer.real_time_data_store import real_time_data_store


class WebSocketConnectionManager:
    """Manages WebSocket connections for real-time data streaming"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set] = {}
        self.subscribers: Dict[str, Set[str]] = {}  # symbol -> connection_ids
    
    def add_connection(self, connection_id: str, websocket):
        """Add a new WebSocket connection"""
        if connection_id not in self.active_connections:
            self.active_connections[connection_id] = set()
        self.active_connections[connection_id].add(websocket)
    
    def remove_connection(self, connection_id: str, websocket):
        """Remove a WebSocket connection"""
        if connection_id in self.active_connections:
            self.active_connections[connection_id].discard(websocket)
            if not self.active_connections[connection_id]:
                del self.active_connections[connection_id]
        
        # Remove from subscribers
        for symbol in list(self.subscribers.keys()):
            self.subscribers[symbol].discard(connection_id)
            if not self.subscribers[symbol]:
                del self.subscribers[symbol]
    
    def subscribe_to_symbol(self, connection_id: str, symbol: str):
        """Subscribe a connection to a symbol"""
        if symbol not in self.subscribers:
            self.subscribers[symbol] = set()
        self.subscribers[symbol].add(connection_id)
    
    def unsubscribe_from_symbol(self, connection_id: str, symbol: str):
        """Unsubscribe a connection from a symbol"""
        if symbol in self.subscribers:
            self.subscribers[symbol].discard(connection_id)
            if not self.subscribers[symbol]:
                del self.subscribers[symbol]
    
    async def broadcast_to_subscribers(self, symbol: str, data: Dict):
        """Broadcast data to all subscribers of a symbol"""
        if symbol not in self.subscribers:
            return
        
        message = json.dumps(data)
        disconnected_connections = set()
        
        for connection_id in self.subscribers[symbol]:
            if connection_id in self.active_connections:
                for websocket in self.active_connections[connection_id]:
                    try:
                        await websocket.send(message)
                    except Exception as e:
                        print(f"Error sending to {connection_id}: {e}")
                        disconnected_connections.add(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected_connections:
            self.remove_connection(connection_id, None)


# Global connection manager
ws_manager = WebSocketConnectionManager()


@api_view(['GET'])
@require_http_methods(["GET"])
def websocket_info(request):
    """Get WebSocket connection information"""
    return Response({
        'status': 'active',
        'endpoints': {
            'ticks': '/ws/ticks/',
            'ohlcv': '/ws/ohlcv/',
            'symbols': '/ws/symbols/'
        },
        'available_symbols': [
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 
            'AUDUSD', 'USDCAD', 'NZDUSD', 'EURGBP'
        ],
        'supported_timeframes': ['M1', 'M5', 'M15', 'H1', 'H4', 'D1'],
        'connection_info': {
            'active_connections': len(ws_manager.active_connections),
            'total_subscribers': sum(len(subs) for subs in ws_manager.subscribers.values())
        }
    })


@api_view(['POST'])
@require_http_methods(["POST"])
@csrf_exempt
def start_websocket_service(request):
    """Start the WebSocket service for real-time data"""
    try:
        data = json.loads(request.body)
        symbols = data.get('symbols', ['EURUSD', 'GBPUSD', 'USDJPY'])
        providers = data.get('providers', {'forexcom': {}})
        
        # Start WebSocket manager
        websocket_manager.start(symbols, providers)
        
        # Start real-time data store
        real_time_data_store.start()
        
        return Response({
            'status': 'started',
            'symbols': symbols,
            'providers': list(providers.keys()),
            'message': 'WebSocket service started successfully'
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@require_http_methods(["POST"])
@csrf_exempt
def stop_websocket_service(request):
    """Stop the WebSocket service"""
    try:
        # Stop services
        websocket_manager.stop()
        real_time_data_store.stop()
        
        return Response({
            'status': 'stopped',
            'message': 'WebSocket service stopped successfully'
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@require_http_methods(["GET"])
def get_real_time_data(request):
    """Get real-time data for a symbol"""
    symbol = request.GET.get('symbol', 'EURUSD')
    data_type = request.GET.get('type', 'tick')  # tick or ohlcv
    count = int(request.GET.get('count', 100))
    timeframe = request.GET.get('timeframe', 'M1')
    
    try:
        if data_type == 'tick':
            # Get recent ticks
            ticks = real_time_data_store.get_recent_ticks(symbol, count)
            data = [
                {
                    'timestamp': tick.timestamp.isoformat(),
                    'bid': float(tick.bid),
                    'ask': float(tick.ask),
                    'mid': float(tick.mid),
                    'spread': float(tick.spread),
                    'volume': tick.volume
                }
                for tick in ticks
            ]
        elif data_type == 'ohlcv':
            # Get recent candles
            candles = real_time_data_store.get_recent_candles(symbol, timeframe, count)
            data = [
                {
                    'timestamp': candle.timestamp.isoformat(),
                    'open': float(candle.open),
                    'high': float(candle.high),
                    'low': float(candle.low),
                    'close': float(candle.close),
                    'volume': candle.volume,
                    'timeframe': candle.timeframe
                }
                for candle in candles
            ]
        else:
            return Response({
                'error': 'Invalid data type. Use "tick" or "ohlcv"'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'symbol': symbol,
            'type': data_type,
            'timeframe': timeframe if data_type == 'ohlcv' else None,
            'count': len(data),
            'data': data
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@require_http_methods(["GET"])
def get_data_quality(request):
    """Get data quality metrics"""
    symbol = request.GET.get('symbol')
    
    try:
        if symbol:
            # Get quality for specific symbol
            quality = real_time_data_store.get_data_quality(symbol)
            return Response({
                'symbol': symbol,
                'quality': quality
            })
        else:
            # Get quality for all symbols
            stats = real_time_data_store.get_statistics()
            connections = real_time_data_store.get_connection_status()
            
            return Response({
                'statistics': stats,
                'connections': connections,
                'message': 'Use ?symbol=EURUSD to get specific symbol quality'
            })
            
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@require_http_methods(["GET"])
def get_latest_prices(request):
    """Get latest prices for all symbols"""
    try:
        symbols = request.GET.get('symbols', '').split(',')
        if not symbols or symbols == ['']:
            # Get all available symbols
            symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD']
        
        prices = {}
        for symbol in symbols:
            tick = real_time_data_store.get_latest_tick(symbol)
            if tick:
                prices[symbol] = {
                    'timestamp': tick.timestamp.isoformat(),
                    'bid': float(tick.bid),
                    'ask': float(tick.ask),
                    'mid': float(tick.mid),
                    'spread': float(tick.spread),
                    'volume': tick.volume
                }
            else:
                prices[symbol] = None
        
        return Response({
            'prices': prices,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# WebSocket event handlers
def on_tick_received(tick: TickData):
    """Handle tick received event"""
    asyncio.create_task(ws_manager.broadcast_to_subscribers(tick.symbol, {
        'type': 'tick',
        'symbol': tick.symbol,
        'timestamp': tick.timestamp.isoformat(),
        'bid': float(tick.bid),
        'ask': float(tick.ask),
        'mid': float(tick.mid),
        'spread': float(tick.spread),
        'volume': tick.volume
    }))


def on_ohlcv_received(candle: OHLCVData):
    """Handle OHLCV received event"""
    asyncio.create_task(ws_manager.broadcast_to_subscribers(candle.symbol, {
        'type': 'ohlcv',
        'symbol': candle.symbol,
        'timestamp': candle.timestamp.isoformat(),
        'open': float(candle.open),
        'high': float(candle.high),
        'low': float(candle.low),
        'close': float(candle.close),
        'volume': candle.volume,
        'timeframe': candle.timeframe
    }))


# Register event handlers
websocket_manager.add_callback('tick', on_tick_received)
websocket_manager.add_callback('ohlcv', on_ohlcv_received)
