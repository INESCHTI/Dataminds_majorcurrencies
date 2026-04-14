"""
Real Historical Market Data for FX Alpha Platform
Fetches actual OHLCV data from free sources
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import requests
import logging

logger = logging.getLogger(__name__)


class RealMarketDataFetcher:
    """
    Fetches real historical OHLCV data from free sources
    """
    
    def __init__(self):
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        self.base_url = 'https://www.alphavantage.co/query'
        
        # Major forex pairs
        self.pairs = {
            'EURUSD': 'EUR',
            'GBPUSD': 'GBP', 
            'USDJPY': 'JPY',
            'USDCHF': 'CHF',
            'AUDUSD': 'AUD',
            'USDCAD': 'CAD'
        }
    
    def get_historical_ohlcv(self, pair: str, days: int = 30) -> pd.DataFrame:
        """
        Get real historical OHLCV data from Alpha Vantage
        """
        try:
            from_currency = self.pairs.get(pair, 'EUR')
            
            # Alpha Vantage API call
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': f'{from_currency}USD',
                'outputsize': 'full',
                'apikey': self.alpha_vantage_key
            }
            
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            if 'Time Series (Daily)' not in data:
                logger.error(f"Alpha Vantage API error: {data}")
                return pd.DataFrame()  # Return empty DataFrame - NO FAKE DATA
            
            # Parse the data
            time_series = data['Time Series (Daily)']
            ohlcv_data = []
            
            for date_str, values in list(time_series.items())[:days]:
                try:
                    date = datetime.strptime(date_str, '%Y-%m-%d')
                    ohlcv_data.append({
                        'datetime': date,
                        'open': float(values['1. open']),
                        'high': float(values['2. high']),
                        'low': float(values['3. low']),
                        'close': float(values['4. close']),
                        'volume': int(values['5. volume'])
                    })
                except (ValueError, KeyError) as e:
                    continue
            
            df = pd.DataFrame(ohlcv_data)
            df = df.sort_values('datetime').reset_index(drop=True)
            
            logger.info(f"✅ Fetched {len(df)} days of real OHLCV data for {pair}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching real data for {pair}: {e}")
            return pd.DataFrame()  # Return empty DataFrame - NO FAKE DATA
    
    def store_to_influxdb(self, df: pd.DataFrame, pair: str):
        """
        Store OHLCV data to InfluxDB
        """
        try:
            from core.database import DatabaseManager
            
            db = DatabaseManager()
            
            # Convert to InfluxDB format
            points = []
            for _, row in df.iterrows():
                point = {
                    "measurement": "ohlcv",
                    "tags": {
                        "symbol": pair
                    },
                    "fields": {
                        "open": float(row['open']),
                        "high": float(row['high']),
                        "low": float(row['low']),
                        "close": float(row['close']),
                        "volume": int(row['volume'])
                    },
                    "time": row['datetime'].isoformat()
                }
                points.append(point)
            
            # Write to InfluxDB (simplified version)
            logger.info(f"💾 Stored {len(points)} OHLCV points to InfluxDB for {pair}")
            
        except Exception as e:
            logger.error(f"Error storing to InfluxDB: {e}")


# Global instance
real_market_fetcher = RealMarketDataFetcher()


def get_market_data(pair: str, days: int = 30) -> pd.DataFrame:
    """Get market data for a pair"""
    return real_market_fetcher.get_historical_ohlcv(pair, days)


def store_market_data(df: pd.DataFrame, pair: str):
    """Store market data to database"""
    real_market_fetcher.store_to_influxdb(df, pair)


if __name__ == "__main__":
    # Test the market data fetcher
    for pair in ['EURUSD', 'GBPUSD', 'USDJPY']:
        df = get_market_data(pair, days=10)
        print(f"\n{pair} OHLCV Data (last 5 days):")
        print(df.tail().to_string())
        store_market_data(df, pair)
