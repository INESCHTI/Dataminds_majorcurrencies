"""
FXCM API Client for Live FX Data
Alternative data provider for redundancy and comparison
"""
import json
import websocket
import requests
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class FXCMConfig:
    api_key: str
    environment: str = "demo"  # "demo" or "live"
    api_url: str = "https://api-demo.fxcm.com:1337"
    stream_url: str = "wss://api-demo.fxcm.com:1338"

class FXCMClient:
    """FXCM API client for real-time FX data"""
    
    def __init__(self, config: FXCMConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {config.api_key}',
            'Content-Type': 'application/json'
        })
        self.access_token = None
        
    def authenticate(self) -> bool:
        """Authenticate with FXCM API"""
        url = f"{self.config.api_url}/token"
        
        try:
            response = self.session.post(url, json={
                'grant_type': 'client_credentials'
            })
            response.raise_for_status()
            data = response.json()
            self.access_token = data.get('access_token')
            
            # Update session headers with access token
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}'
            })
            
            return True
        except Exception as e:
            logger.error(f"FXCM authentication failed: {e}")
            return False
    
    def get_instruments(self) -> List[Dict]:
        """Get available instruments"""
        url = f"{self.config.api_url}/symbols"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get FXCM instruments: {e}")
            return []
    
    def get_pricing(self, symbols: List[str]) -> Dict:
        """Get current pricing"""
        url = f"{self.config.api_url}/rates"
        params = {'symbols': ','.join(symbols)}
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get FXCM pricing: {e}")
            return {}
    
    def create_price_stream(self, symbols: List[str], callback: Callable) -> websocket.WebSocketApp:
        """Create WebSocket connection for real-time price streaming"""
        
        def on_message(ws, message):
            try:
                data = json.loads(message)
                if 'rates' in data:
                    callback(data)
            except Exception as e:
                logger.error(f"Error processing FXCM stream message: {e}")
        
        def on_error(ws, error):
            logger.error(f"FXCM WebSocket error: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            logger.info("FXCM WebSocket connection closed")
        
        def on_open(ws):
            logger.info("FXCM WebSocket connection opened")
            # Subscribe to symbols
            subscribe_message = {
                "command": "subscribe",
                "symbols": symbols
            }
            ws.send(json.dumps(subscribe_message))
        
        return websocket.WebSocketApp(
            self.config.stream_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            header=[
                f'Authorization: Bearer {self.access_token}'
            ]
        )
    
    def get_historical_data(self, symbol: str, timeframe: str = "1m", count: int = 500) -> Dict:
        """Get historical data"""
        url = f"{self.config.api_url}/candles"
        params = {
            'symbol': symbol,
            'timeframe': timeframe,
            'count': count
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get FXCM historical data: {e}")
            return {}

def create_fxcm_config_from_env() -> FXCMConfig:
    """Create FXCM config from environment variables"""
    import os
    
    return FXCMConfig(
        api_key=os.getenv('FXCM_API_KEY', ''),
        environment=os.getenv('FXCM_ENVIRONMENT', 'demo')
    )

def parse_fxcm_tick(rate_data: Dict) -> Dict:
    """Parse FXCM rate data to standard format"""
    if 'rates' not in rate_data:
        return {}
    
    rate = rate_data['rates'][0]  # FXCM returns array
    return {
        'symbol': rate['symbol'],
        'timestamp': datetime.now().isoformat(),
        'bid': float(rate['bid']),
        'ask': float(rate['ask']),
        'mid': (float(rate['bid']) + float(rate['ask'])) / 2,
        'spread': float(rate['ask']) - float(rate['bid']),
        'volume': 0
    }
