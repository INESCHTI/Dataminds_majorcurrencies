"""
Free Data Collector for FX Alpha Platform
Uses only free, real data sources
"""

import os
import time
import requests
import feedparser
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from core.database import DatabaseManager

logger = logging.getLogger(__name__)


class FreeDataCollector:
    """
    Collects free forex data from multiple sources:
    1. Alpha Vantage (free tier - 5 calls/minute)
    2. FRED API (free tier)
    3. RSS news feeds (unlimited)
    4. Reddit API (free tier)
    """
    
    def __init__(self):
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        self.fred_key = os.getenv('FRED_API_KEY', 'ab5c8988b37a81db4461029d60a73b7f')
        self.news_api_key = os.getenv('NEWS_API_KEY', 'demo')
        
        # Free RSS feeds for forex news
        self.rss_feeds = [
            'https://www.forexfactory.com/news.xml',
            'https://www.dailyfx.com/rss/news',
            'https://www.investing.com/rss/news_301.rss',
            'https://www.reuters.com/business/markets/europe/rss.xml',
            'https://www.bloomberg.com/markets/europe/rss.xml'
        ]
        
        # Major currency pairs
        self.pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD']
        
    def collect_forex_rates(self):
        """Collect current forex rates from Alpha Vantage"""
        rates = {}
        
        for pair in self.pairs:
            try:
                from_symbol = pair[:3]
                to_symbol = pair[3:]
                
                url = f"https://www.alphavantage.co/query"
                params = {
                    'function': 'CURRENCY_EXCHANGE_RATE',
                    'from_currency': from_symbol,
                    'to_currency': to_symbol,
                    'apikey': self.alpha_vantage_key
                }
                
                response = requests.get(url, params=params, timeout=10)
                data = response.json()
                
                if 'Realtime Currency Exchange Rate' in data:
                    rate_data = data['Realtime Currency Exchange Rate']
                    rates[pair] = {
                        'rate': float(rate_data['5. Exchange Rate']),
                        'bid': float(rate_data['8. Bid Price']) if '8. Bid Price' in rate_data else None,
                        'ask': float(rate_data['9. Ask Price']) if '9. Ask Price' in rate_data else None,
                        'timestamp': datetime.now(),
                        'source': 'Alpha Vantage'
                    }
                
                # Rate limiting for free tier
                time.sleep(12)  # 12 seconds between calls
                
            except Exception as e:
                logger.error(f"Error fetching {pair} rate: {e}")
                continue
        
        return rates
    
    def collect_fred_data(self):
        """Collect macroeconomic data from FRED"""
        indicators = {
            'USD': ['DFF', 'DEXUSEU', 'DEXUSUK', 'DEXJPUS', 'DEXCHUS', 'DEXUSAL', 'DEXUSCA'],
            'EUR': ['DEXUSEU', 'EURD'],
            'GBP': ['DEXUSUK', 'GBPD'],
            'JPY': ['DEXJPUS', 'JPYD'],
            'CHF': ['DEXCHUS', 'CHFD'],
            'AUD': ['DEXUSAL', 'AUDD'],
            'CAD': ['DEXUSCA', 'CADD']
        }
        
        macro_data = {}
        
        for currency, series_list in indicators.items():
            for series_id in series_list:
                try:
                    url = f"https://api.stlouisfed.org/fred/series/observations"
                    params = {
                        'series_id': series_id,
                        'api_key': self.fred_key,
                        'file_type': 'json',
                        'limit': 10,  # Get last 10 observations
                        'sort_order': 'desc'
                    }
                    
                    response = requests.get(url, params=params, timeout=10)
                    data = response.json()
                    
                    if 'observations' in data and data['observations']:
                        latest = data['observations'][0]
                        if latest['value'] != '.':
                            macro_data[f"{currency}_{series_id}"] = {
                                'value': float(latest['value']),
                                'date': latest['date'],
                                'series_id': series_id,
                                'currency': currency,
                                'timestamp': datetime.now(),
                                'source': 'FRED'
                            }
                    
                    time.sleep(1)  # Rate limiting
                    
                except Exception as e:
                    logger.error(f"Error fetching FRED {series_id}: {e}")
                    continue
        
        return macro_data
    
    def collect_news_rss(self):
        """Collect news from RSS feeds"""
        news_articles = []
        
        for feed_url in self.rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:10]:  # Get last 10 articles per feed
                    # Extract currency mentions
                    currencies_mentioned = []
                    for pair in self.pairs:
                        base = pair[:3]
                        quote = pair[3:]
                        if base in entry.title or base in entry.get('summary', '') or \
                           quote in entry.title or quote in entry.get('summary', ''):
                            currencies_mentioned.extend([base, quote])
                    
                    if currencies_mentioned:
                        article = {
                            'title': entry.title,
                            'summary': entry.get('summary', ''),
                            'link': entry.get('link', ''),
                            'published': entry.get('published', ''),
                            'currencies': list(set(currencies_mentioned)),
                            'source': feed.feed.get('title', feed_url),
                            'timestamp': datetime.now(),
                            'source_type': 'RSS'
                        }
                        news_articles.append(article)
                
                time.sleep(1)  # Be respectful to RSS feeds
                
            except Exception as e:
                logger.error(f"Error fetching RSS {feed_url}: {e}")
                continue
        
        return news_articles
    
    def collect_reddit_sentiment(self):
        """Collect forex sentiment from Reddit (read-only)"""
        # Note: This would require Reddit API setup
        # For now, return empty as it requires OAuth setup
        return []
    
    def store_forex_rates(self, rates):
        """Store forex rates in InfluxDB"""
        if not rates:
            return
        
        try:
            with DatabaseManager.get_influx_client() as client:
                write_api = client.write_api()
                
                for pair, data in rates.items():
                    point = {
                        "measurement": "forex_rates",
                        "tags": {
                            "symbol": pair,
                            "source": data['source']
                        },
                        "fields": {
                            "rate": data['rate'],
                            "bid": data.get('bid'),
                            "ask": data.get('ask')
                        },
                        "time": data['timestamp']
                    }
                    write_api.write(bucket=os.getenv('INFLUX_BUCKET', 'forex_data'), record=point)
                
                logger.info(f"Stored {len(rates)} forex rates")
                
        except Exception as e:
            logger.error(f"Error storing forex rates: {e}")
    
    def store_macro_data(self, macro_data):
        """Store macro data in PostgreSQL"""
        if not macro_data:
            return
        
        try:
            with DatabaseManager.get_postgres_connection() as conn:
                cursor = conn.cursor()
                
                for key, data in macro_data.items():
                    cursor.execute("""
                        INSERT INTO macro_indicators 
                        (indicator_name, currency, value, date, source, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, (
                        data['series_id'],
                        data['currency'],
                        data['value'],
                        data['date'],
                        data['source'],
                        data['timestamp']
                    ))
                
                conn.commit()
                logger.info(f"Stored {len(macro_data)} macro indicators")
                
        except Exception as e:
            logger.error(f"Error storing macro data: {e}")
    
    def store_news(self, news_articles):
        """Store news articles in PostgreSQL"""
        if not news_articles:
            return
        
        try:
            with DatabaseManager.get_postgres_connection() as conn:
                cursor = conn.cursor()
                
                for article in news_articles:
                    cursor.execute("""
                        INSERT INTO news_articles 
                        (title, content, source, url, published_at, currencies, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, (
                        article['title'],
                        article['summary'],
                        article['source'],
                        article['link'],
                        article['published'],
                        article['currencies'],
                        article['timestamp']
                    ))
                
                conn.commit()
                logger.info(f"Stored {len(news_articles)} news articles")
                
        except Exception as e:
            logger.error(f"Error storing news: {e}")
    
    def run_collection(self):
        """Run complete data collection"""
        logger.info("Starting free data collection...")
        
        # Collect all data
        forex_rates = self.collect_forex_rates()
        macro_data = self.collect_fred_data()
        news_articles = self.collect_news_rss()
        
        # Store data
        self.store_forex_rates(forex_rates)
        self.store_macro_data(macro_data)
        self.store_news(news_articles)
        
        logger.info(f"Collection complete: {len(forex_rates)} rates, {len(macro_data)} indicators, {len(news_articles)} articles")
        
        return {
            'forex_rates': len(forex_rates),
            'macro_data': len(macro_data),
            'news_articles': len(news_articles)
        }


# Global collector instance
free_data_collector = FreeDataCollector()


def collect_free_data():
    """Convenience function to run data collection"""
    return free_data_collector.run_collection()


if __name__ == "__main__":
    # Run collection when script is executed directly
    collect_free_data()
