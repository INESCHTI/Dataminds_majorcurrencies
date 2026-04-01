"""
OANDA API Client for Live FX Data
Real-time WebSocket and REST API integration
"""
import json
import time
import hmac
import hashlib
import requests
import websocket
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class OandaConfig:
    api_key: str
    account_id: str
    environment: str = "practice"  # "practice" or "live"
    api_url: str = "https://api-fxpractice.oanda.com"
    stream_url: str = "https://stream-fxpractice.oanda.com"

class OandaClient:
    """OANDA API client for real-time FX data"""
    
    def __init__(self, config: OandaConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {config.api_key}',
            'Content-Type': 'application/json',
            'Accept-Datetime-Format': 'RFC3339'
        })
        
    def get_account_instruments(self) -> List[Dict]:
        """Get tradable instruments for the account"""
        url = f"{self.config.api_url}/v3/accounts/{self.config.account_id}/instruments"
        params = {
            'instruments': 'EUR_USD,GBP_USD,USD_JPY,USD_CHF,AUD_USD,USD_CAD,NZD_USD,EUR_GBP'
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('instruments', [])
        except Exception as e:
            logger.error(f"Failed to get instruments: {e}")
            return []
    
    def get_pricing(self, instruments: List[str]) -> Dict:
        """Get current pricing for specified instruments"""
        url = f"{self.config.api_url}/v3/accounts/{self.config.account_id}/pricing"
        params = {
            'instruments': ','.join(instruments),
            'includeHomeConversions': 'true'
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get pricing: {e}")
            return {}
    
    def get_candles(self, instrument: str, granularity: str = "M1", count: int = 500) -> Dict:
        """Get historical candle data"""
        url = f"{self.config.api_url}/v3/instruments/{instrument}/candles"
        params = {
            'price': 'M',  # Midpoint
            'granularity': granularity,
            'count': count,
            'dailyAlignment': 0,
            'alignmentTimezone': 'UTC'
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get candles for {instrument}: {e}")
            return {}
    
    def create_price_stream(self, instruments: List[str], callback: Callable) -> websocket.WebSocketApp:
        """Create WebSocket connection for real-time price streaming"""
        
        def on_message(ws, message):
            try:
                data = json.loads(message)
                if 'tick' in data or 'heartbeat' in data:
                    callback(data)
            except Exception as e:
                logger.error(f"Error processing stream message: {e}")
        
        def on_error(ws, error):
            logger.error(f"WebSocket error: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            logger.info("WebSocket connection closed")
        
        def on_open(ws):
            logger.info("WebSocket connection opened")
            # Subscribe to price updates
            subscribe_message = {
                "event": "subscribe",
                "instruments": instruments
            }
            ws.send(json.dumps(subscribe_message))
        
        # Build WebSocket URL
        stream_url = f"{self.config.stream_url}/v3/accounts/{self.config.account_id}/pricing/stream"
        
        return websocket.WebSocketApp(
            stream_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            header=[
                f'Authorization: Bearer {self.config.api_key}',
                'Accept-Datetime-Format: RFC3339'
            ]
        )
    
    def place_market_order(self, instrument: str, units: int, order_type: str = "market") -> Dict:
        """Place a market order (for risk management implementation)"""
        url = f"{self.config.api_url}/v3/accounts/{self.config.account_id}/orders"
        
        order_data = {
            "order": {
                "type": "MARKET",
                "instrument": instrument,
                "units": str(units),
                "timeInForce": "FOK",
                "positionFill": "DEFAULT"
            }
        }
        
        try:
            response = self.session.post(url, json=order_data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return {}
    
    def get_account_summary(self) -> Dict:
        """Get account summary including balance and positions"""
        url = f"{self.config.api_url}/v3/accounts/{self.config.account_id}/summary"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get account summary: {e}")
            return {}
    
    def get_open_positions(self) -> List[Dict]:
        """Get current open positions"""
        url = f"{self.config.api_url}/v3/accounts/{self.config.account_id}/positions"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get('positions', [])
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []
    
    def close_position(self, instrument: str, units: str = "ALL") -> Dict:
        """Close a position (for risk management)"""
        url = f"{self.config.api_url}/v3/accounts/{self.config.account_id}/positions/{instrument}/close"
        
        close_data = {
            "units": units,
            "clientExtensions": {
                "tag": "close_position"
            }
        }
        
        try:
            response = self.session.put(url, json=close_data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to close position: {e}")
            return {}

# Utility functions
def create_oanda_config_from_env() -> OandaConfig:
    """Create OANDA config from environment variables"""
    import os
    
    return OandaConfig(
        api_key=os.getenv('OANDA_API_KEY', ''),
        account_id=os.getenv('OANDA_ACCOUNT_ID', ''),
        environment=os.getenv('OANDA_ENVIRONMENT', 'practice')
    )

def parse_oanda_tick(tick_data: Dict) -> Dict:
    """Parse OANDA tick data to standard format"""
    if 'tick' not in tick_data:
        return {}
    
    tick = tick_data['tick']
    return {
        'symbol': tick['instrument'].replace('_', ''),
        'timestamp': tick['time'],
        'bid': float(tick['bid']),
        'ask': float(tick['ask']),
        'mid': float(tick['mid']),
        'spread': float(tick['ask']) - float(tick['bid']),
        'volume': 0  # OANDA doesn't provide volume in ticks
    }

def parse_oanda_candles(candles_data: Dict) -> List[Dict]:
    """Parse OANDA candle data to standard format"""
    if 'candles' not in candles_data:
        return []
    
    parsed_candles = []
    for candle in candles_data['candles']:
        if candle['complete']:  # Only use complete candles
            parsed_candles.append({
                'symbol': candles_data.get('instrument', '').replace('_', ''),
                'timeframe': candles_data.get('granularity', 'M1'),
                'timestamp': candle['time'],
                'open': float(candle['mid']['o']),
                'high': float(candle['mid']['h']),
                'low': float(candle['mid']['l']),
                'close': float(candle['mid']['c']),
                'volume': candle['volume']
            })
    
    return parsed_candles
