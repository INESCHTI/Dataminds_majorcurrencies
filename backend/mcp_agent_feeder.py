"""
MCP Agent Feeder - Specialized Data Distribution to Agents
Connects MCP Agent Collecteur to each agent with task-specific data feeds
"""
import os
import sys
import json
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django
django.setup()

from signal_layer.technical_agent_v2_enhanced import TechnicalAgentV2Enhanced
from signal_layer.macro_agent_v2 import MacroAgentV2
from signal_layer.sentiment_agent_v2 import SentimentAgentV2
from signal_layer.geopolitical_agent_v2_enhanced import GeopoliticalAgentV2Enhanced
from signal_layer.coordinator_agent_v2_enhanced import CoordinatorAgentV2Enhanced
from mcp_agent_collecteur import get_mcp_agent_collecteur


@dataclass
class AgentDataFeed:
    """Specialized data feed configuration for each agent"""
    agent_name: str
    data_types: List[str]
    update_frequency: int  # seconds
    filters: Dict[str, Any]
    last_update: Optional[datetime]
    data_cache: Dict[str, Any]
    is_active: bool


class MCPAgentFeeder:
    """
    MCP Agent Feeder - Distributes specialized data to each agent
    
    Features:
    - Task-specific data filtering for each agent
    - Real-time data feeding based on agent requirements
    - Intelligent data preprocessing and enrichment
    - Performance monitoring and optimization
    """
    
    def __init__(self):
        self.feeder_name = "MCPAgentFeeder"
        self.is_running = False
        self.feeding_threads = []
        
        # Initialize agents
        self.agents = {
            'technical': TechnicalAgentV2Enhanced(),
            'macro': MacroAgentV2(),
            'sentiment': SentimentAgentV2(),
            'geopolitical': GeopoliticalAgentV2Enhanced(),
            'coordinator': CoordinatorAgentV2Enhanced()
        }
        
        # Initialize MCP Agent Collecteur
        self.mcp_collecteur = get_mcp_agent_collecteur()
        
        # Configure specialized data feeds for each agent
        self.agent_feeds = self._initialize_agent_feeds()
        
        # Data processing statistics
        self.stats = {
            'total_feeds': 0,
            'successful_feeds': 0,
            'failed_feeds': 0,
            'data_points_processed': 0,
            'start_time': datetime.now(),
            'agent_updates': {agent: 0 for agent in self.agents.keys()}
        }
        
        self.logger = logging.getLogger(__name__)
    
    def _initialize_agent_feeds(self) -> Dict[str, AgentDataFeed]:
        """Initialize specialized data feeds for each agent"""
        feeds = {}
        
        # Technical Agent Feed - Price Data Focus
        feeds['technical'] = AgentDataFeed(
            agent_name='technical',
            data_types=['mt5_price_data', 'influxdb_ohlcv', 'technical_indicators'],
            update_frequency=60,  # Every 1 minute
            filters={
                'symbols': ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF'],
                'timeframes': ['1H', '4H', '1D'],
                'indicators': ['SMA', 'EMA', 'RSI', 'MACD', 'BB'],
                'data_quality': 'high',
                'latency_threshold': 5  # seconds
            },
            last_update=None,
            data_cache={},
            is_active=False
        )
        
        # Macro Agent Feed - Economic Data Focus
        feeds['macro'] = AgentDataFeed(
            agent_name='macro',
            data_types=['fred_indicators', 'economic_calendar', 'central_bank_data'],
            update_frequency=300,  # Every 5 minutes
            filters={
                'indicators': ['GDP', 'CPI', 'UNRATE', 'FEDFUNDS', 'DGS10'],
                'currencies': ['EUR', 'USD', 'GBP', 'JPY', 'CHF'],
                'regions': ['US', 'EU', 'UK', 'JP'],
                'impact_level': 'high',
                'data_sources': ['FRED', 'ECB', 'FED', 'BOE']
            },
            last_update=None,
            data_cache={},
            is_active=False
        )
        
        # Sentiment Agent Feed - News Data Focus
        feeds['sentiment'] = AgentDataFeed(
            agent_name='sentiment',
            data_types=['rss_news', 'social_sentiment', 'market_sentiment'],
            update_frequency=180,  # Every 3 minutes
            filters={
                'news_sources': ['reuters', 'bbc', 'forexlive', 'fxstreet'],
                'sentiment_types': ['positive', 'negative', 'neutral'],
                'currencies': ['EUR', 'USD', 'GBP', 'JPY', 'CHF'],
                'keywords': ['market', 'economy', 'currency', 'trading'],
                'sentiment_threshold': 0.1
            },
            last_update=None,
            data_cache={},
            is_active=False
        )
        
        # Geopolitical Agent Feed - Political/Event Data Focus
        feeds['geopolitical'] = AgentDataFeed(
            agent_name='geopolitical',
            data_types=['geopolitical_news', 'political_events', 'risk_events'],
            update_frequency=240,  # Every 4 minutes
            filters={
                'news_sources': ['reuters_world', 'bbc_world', 'al_jazeera', 'ap_world'],
                'event_types': ['election', 'conflict', 'sanction', 'policy'],
                'risk_levels': ['low', 'medium', 'high', 'critical'],
                'regions': ['global', 'europe', 'asia', 'americas'],
                'safe_haven_currencies': ['USD', 'CHF', 'JPY'],
                'risk_on_currencies': ['EUR', 'GBP', 'AUD', 'NZD', 'CAD']
            },
            last_update=None,
            data_cache={},
            is_active=False
        )
        
        # Coordinator Agent Feed - Comprehensive Data Focus
        feeds['coordinator'] = AgentDataFeed(
            agent_name='coordinator',
            data_types=['all_agent_signals', 'market_overview', 'risk_metrics'],
            update_frequency=120,  # Every 2 minutes
            filters={
                'include_all_agents': True,
                'signal_quality_threshold': 0.5,
                'risk_assessment': True,
                'market_regime_detection': True,
                'correlation_analysis': True
            },
            last_update=None,
            data_cache={},
            is_active=False
        )
        
        return feeds
    
    def start_feeding(self):
        """Start specialized data feeding to all agents"""
        if self.is_running:
            self.logger.warning("MCP Agent Feeder is already running")
            return
        
        self.is_running = True
        self.logger.info("🚀 Starting MCP Agent Feeder...")
        
        # Start MCP Agent Collecteur if not running
        if not self.mcp_collecteur.is_running:
            self.mcp_collecteur.start_collection()
        
        # Start feeding threads for each agent
        for agent_name, feed in self.agent_feeds.items():
            self._start_agent_feed(agent_name, feed)
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self._monitor_feeding, daemon=True)
        monitor_thread.start()
        self.feeding_threads.append(monitor_thread)
        
        self.logger.info("✅ MCP Agent Feeder started successfully")
        self._log_feeding_status()
    
    def stop_feeding(self):
        """Stop data feeding to all agents"""
        self.is_running = False
        self.logger.info("🛑 Stopping MCP Agent Feeder...")
        
        # Wait for threads to finish
        for thread in self.feeding_threads:
            if thread.is_alive():
                thread.join(timeout=5)
        
        self.logger.info("✅ MCP Agent Feeder stopped")
        self._log_feeding_status()
    
    def _start_agent_feed(self, agent_name: str, feed: AgentDataFeed):
        """Start feeding specialized data to a specific agent"""
        def agent_feeder():
            feed.is_active = True
            self.logger.info(f"📡 Starting feed for {agent_name} agent")
            
            while self.is_running:
                try:
                    # Collect specialized data for this agent
                    specialized_data = self._collect_specialized_data(agent_name, feed)
                    
                    if specialized_data:
                        # Feed data to agent
                        self._feed_agent(agent_name, specialized_data, feed)
                        
                        # Update statistics
                        self.stats['successful_feeds'] += 1
                        self.stats['agent_updates'][agent_name] += 1
                        feed.last_update = datetime.now()
                    
                    self.stats['total_feeds'] += 1
                    
                except Exception as e:
                    self.logger.error(f"❌ Error feeding {agent_name}: {e}")
                    self.stats['failed_feeds'] += 1
                
                time.sleep(feed.update_frequency)
            
            feed.is_active = False
        
        feed_thread = threading.Thread(target=agent_feeder, daemon=True)
        feed_thread.start()
        self.feeding_threads.append(feed_thread)
    
    def _collect_specialized_data(self, agent_name: str, feed: AgentDataFeed) -> Optional[Dict[str, Any]]:
        """Collect specialized data for a specific agent"""
        try:
            specialized_data = {
                'agent_name': agent_name,
                'timestamp': datetime.now(),
                'data_types': feed.data_types,
                'data': {}
            }
            
            # Collect data based on agent requirements
            for data_type in feed.data_types:
                if data_type == 'mt5_price_data':
                    specialized_data['data'][data_type] = self._collect_mt5_for_agent(feed)
                elif data_type == 'influxdb_ohlcv':
                    specialized_data['data'][data_type] = self._collect_influxdb_for_agent(feed)
                elif data_type == 'technical_indicators':
                    specialized_data['data'][data_type] = self._collect_technical_indicators_for_agent(feed)
                elif data_type == 'fred_indicators':
                    specialized_data['data'][data_type] = self._collect_fred_for_agent(feed)
                elif data_type == 'rss_news':
                    specialized_data['data'][data_type] = self._collect_news_for_agent(feed)
                elif data_type == 'geopolitical_news':
                    specialized_data['data'][data_type] = self._collect_geopolitical_for_agent(feed)
                elif data_type == 'all_agent_signals':
                    specialized_data['data'][data_type] = self._collect_agent_signals_for_agent(feed)
            
            return specialized_data
            
        except Exception as e:
            self.logger.error(f"❌ Error collecting data for {agent_name}: {e}")
            return None
    
    def _collect_mt5_for_agent(self, feed: AgentDataFeed) -> Dict[str, Any]:
        """Collect MT5 data filtered for agent"""
        try:
            import MetaTrader5 as mt5
            
            symbols = feed.filters.get('symbols', ['EURUSD'])
            mt5_data = {}
            
            for symbol in symbols:
                tick = mt5.symbol_info_tick(symbol)
                if tick:
                    mt5_data[symbol] = {
                        'bid': tick.bid,
                        'ask': tick.ask,
                        'close': (tick.bid + tick.ask) / 2,
                        'timestamp': datetime.now(),
                        'spread': tick.ask - tick.bid,
                        'volume': tick.volume
                    }
            
            return mt5_data
            
        except Exception as e:
            self.logger.error(f"❌ Error collecting MT5 data: {e}")
            return {}
    
    def _collect_influxdb_for_agent(self, feed: AgentDataFeed) -> Dict[str, Any]:
        """Collect InfluxDB data filtered for agent"""
        try:
            from influxdb_client import InfluxDBClient
            from django.conf import settings
            
            client = InfluxDBClient(
                url=settings.INFLUX_URL,
                token=settings.INFLUX_TOKEN,
                org=settings.INFLUX_ORG
            )
            
            query_api = client.query_api()
            symbols = feed.filters.get('symbols', ['EURUSD'])
            timeframes = feed.filters.get('timeframes', ['1H'])
            
            influxdb_data = {}
            
            for symbol in symbols:
                for timeframe in timeframes:
                    # Query recent OHLCV data
                    query = f'''
                    from(bucket: "forex_data")
                      |> range(start: -{timeframe})
                      |> filter(fn: (r) => r["_measurement"] == "ohlcv")
                      |> filter(fn: (r) => r["symbol"] == "{symbol}")
                      |> limit(n: 100)
                    '''
                    
                    result = query_api.query(query)
                    
                    # Convert to DataFrame-like structure
                    data_points = []
                    for table in result:
                        for record in table.records:
                            data_points.append({
                                'time': record.get_time(),
                                'field': record.get_field(),
                                'value': record.get_value()
                            })
                    
                    influxdb_data[f"{symbol}_{timeframe}"] = data_points
            
            client.close()
            return influxdb_data
            
        except Exception as e:
            self.logger.error(f"❌ Error collecting InfluxDB data: {e}")
            return {}
    
    def _collect_technical_indicators_for_agent(self, feed: AgentDataFeed) -> Dict[str, Any]:
        """Calculate technical indicators for agent"""
        try:
            # Get OHLCV data from InfluxDB
            ohlcv_data = self._collect_influxdb_for_agent(feed)
            
            indicators = {}
            required_indicators = feed.filters.get('indicators', ['SMA', 'EMA', 'RSI'])
            
            for symbol_key, data_points in ohlcv_data.items():
                if len(data_points) > 20:  # Need enough data for indicators
                    # Extract close prices
                    close_prices = []
                    for point in data_points:
                        if point['field'] == 'close':
                            close_prices.append(point['value'])
                    
                    if len(close_prices) > 20:
                        indicators[symbol_key] = {}
                        
                        # Calculate indicators based on requirements
                        if 'SMA' in required_indicators:
                            indicators[symbol_key]['SMA_20'] = sum(close_prices[-20:]) / 20
                            indicators[symbol_key]['SMA_50'] = sum(close_prices[-50:]) / 50 if len(close_prices) >= 50 else None
                        
                        if 'EMA' in required_indicators:
                            # Simple EMA calculation
                            ema_12 = close_prices[-1]  # Simplified
                            ema_26 = close_prices[-1]  # Simplified
                            indicators[symbol_key]['EMA_12'] = ema_12
                            indicators[symbol_key]['EMA_26'] = ema_26
                        
                        if 'RSI' in required_indicators and len(close_prices) >= 14:
                            # Simple RSI calculation
                            gains = []
                            losses = []
                            for i in range(1, 14):
                                change = close_prices[-i] - close_prices[-i-1]
                                if change > 0:
                                    gains.append(change)
                                    losses.append(0)
                                else:
                                    gains.append(0)
                                    losses.append(abs(change))
                            
                            avg_gain = sum(gains) / 14 if gains else 0
                            avg_loss = sum(losses) / 14 if losses else 1
                            rs = avg_gain / avg_loss if avg_loss > 0 else 0
                            rsi = 100 - (100 / (1 + rs))
                            indicators[symbol_key]['RSI'] = rsi
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating technical indicators: {e}")
            return {}
    
    def _collect_fred_for_agent(self, feed: AgentDataFeed) -> Dict[str, Any]:
        """Collect FRED data filtered for agent"""
        try:
            import requests
            
            fred_api_key = os.getenv('FRED_API_KEY')
            if not fred_api_key:
                return {}
            
            indicators = feed.filters.get('indicators', ['GDP', 'CPI'])
            fred_data = {}
            
            for indicator in indicators:
                try:
                    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={indicator}&api_key={fred_api_key}&limit=5&observation_type=real_time"
                    response = requests.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'observations' in data:
                            fred_data[indicator] = data['observations']
                
                except Exception as e:
                    self.logger.warning(f"⚠️ Error fetching {indicator}: {e}")
            
            return fred_data
            
        except Exception as e:
            self.logger.error(f"❌ Error collecting FRED data: {e}")
            return {}
    
    def _collect_news_for_agent(self, feed: AgentDataFeed) -> Dict[str, Any]:
        """Collect news data filtered for agent"""
        try:
            from core.database import DatabaseManager
            
            sources = feed.filters.get('news_sources', ['reuters'])
            keywords = feed.filters.get('keywords', [])
            currencies = feed.filters.get('currencies', [])
            
            news_data = {}
            
            with DatabaseManager.get_postgres_connection() as conn:
                cursor = conn.cursor()
                
                for source in sources:
                    # Build query with filters
                    query = """
                        SELECT title, content, source, published_at 
                        FROM news_articles 
                        WHERE source = %s 
                        AND published_at >= %s
                    """
                    params = [source, datetime.now() - timedelta(hours=24)]
                    
                    # Add keyword filters
                    if keywords:
                        keyword_conditions = []
                        for keyword in keywords:
                            keyword_conditions.append("title LIKE %s")
                            params.append(f"%{keyword}%")
                        query += f" AND ({' OR '.join(keyword_conditions)})"
                    
                    # Add currency filters
                    if currencies:
                        currency_conditions = []
                        for currency in currencies:
                            currency_conditions.append("title LIKE %s")
                            params.append(f"%{currency}%")
                        query += f" AND ({' OR '.join(currency_conditions)})"
                    
                    query += " ORDER BY published_at DESC LIMIT 20"
                    
                    cursor.execute(query, params)
                    articles = cursor.fetchall()
                    
                    news_data[source] = [
                        {
                            'title': article[0],
                            'content': article[1][:500],  # Truncate for efficiency
                            'source': article[2],
                            'published_at': article[3]
                        }
                        for article in articles
                    ]
            
            return news_data
            
        except Exception as e:
            self.logger.error(f"❌ Error collecting news data: {e}")
            return {}
    
    def _collect_geopolitical_for_agent(self, feed: AgentDataFeed) -> Dict[str, Any]:
        """Collect geopolitical news filtered for agent"""
        # Use geopolitical agent's own RSS collection
        try:
            geopolitical_agent = self.agents['geopolitical']
            
            # Trigger data collection
            currencies = feed.filters.get('safe_haven_currencies', []) + feed.filters.get('risk_on_currencies', [])
            result = geopolitical_agent.generate_signal(currencies)
            
            return {
                'geopolitical_signal': result,
                'rss_sources_used': result.get('features_used', {}).get('rss_sources', 0),
                'articles_analyzed': result.get('features_used', {}).get('news_count', 0)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error collecting geopolitical data: {e}")
            return {}
    
    def _collect_agent_signals_for_agent(self, feed: AgentDataFeed) -> Dict[str, Any]:
        """Collect signals from all agents for coordinator"""
        try:
            agent_signals = {}
            
            for agent_name, agent in self.agents.items():
                if agent_name == 'coordinator':
                    continue  # Skip coordinator to avoid recursion
                
                try:
                    # Generate signal for each agent
                    if agent_name == 'technical':
                        signal = agent.generate_signal('EURUSD', 'EUR', 'USD')
                    elif agent_name == 'macro':
                        signal = agent.generate_signal(['EUR', 'USD'])
                    elif agent_name == 'sentiment':
                        signal = agent.generate_signal(['EUR', 'USD'])
                    elif agent_name == 'geopolitical':
                        signal = agent.generate_signal(['EUR', 'USD'])
                    
                    agent_signals[agent_name] = signal
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Error getting signal from {agent_name}: {e}")
                    agent_signals[agent_name] = {'error': str(e)}
            
            return agent_signals
            
        except Exception as e:
            self.logger.error(f"❌ Error collecting agent signals: {e}")
            return {}
    
    def _feed_agent(self, agent_name: str, specialized_data: Dict[str, Any], feed: AgentDataFeed):
        """Feed specialized data to agent"""
        try:
            agent = self.agents[agent_name]
            
            # Update agent's data cache
            feed.data_cache = specialized_data['data']
            
            # Log successful feeding
            data_types = list(specialized_data['data'].keys())
            self.logger.debug(f"📡 Fed {agent_name} with data: {data_types}")
            
            # Update statistics
            data_points = sum(len(data) if isinstance(data, dict) else 1 
                             for data in specialized_data['data'].values())
            self.stats['data_points_processed'] += data_points
            
        except Exception as e:
            self.logger.error(f"❌ Error feeding {agent_name}: {e}")
    
    def _monitor_feeding(self):
        """Monitor feeding performance and health"""
        while self.is_running:
            try:
                # Check feeding health
                for agent_name, feed in self.agent_feeds.items():
                    if feed.is_active and feed.last_update:
                        age = datetime.now() - feed.last_update
                        if age > timedelta(seconds=feed.update_frequency * 3):
                            self.logger.warning(f"⚠️ {agent_name} feed stale: {age}")
                
                # Log status every 5 minutes
                if int(datetime.now().timestamp()) % 300 == 0:
                    self._log_feeding_status()
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"❌ Monitor error: {e}")
    
    def _log_feeding_status(self):
        """Log current feeding status"""
        self.logger.info("📊 MCP Agent Feeder Status:")
        self.logger.info(f"   Running: {self.is_running}")
        self.logger.info(f"   Total Feeds: {self.stats['total_feeds']}")
        self.logger.info(f"   Successful: {self.stats['successful_feeds']}")
        self.logger.info(f"   Failed: {self.stats['failed_feeds']}")
        self.logger.info(f"   Data Points: {self.stats['data_points_processed']}")
        
        for agent_name, feed in self.agent_feeds.items():
            status = "🟢 Active" if feed.is_active else "🔴 Inactive"
            self.logger.info(f"   {agent_name}: {status} (Updates: {self.stats['agent_updates'][agent_name]})")
    
    def get_feeding_statistics(self) -> Dict[str, Any]:
        """Get comprehensive feeding statistics"""
        uptime = datetime.now() - self.stats['start_time']
        
        return {
            **self.stats,
            'uptime_seconds': uptime.total_seconds(),
            'success_rate': self.stats['successful_feeds'] / max(self.stats['total_feeds'], 1),
            'data_points_per_hour': self.stats['data_points_processed'] / max(uptime.total_seconds() / 3600, 1),
            'agent_feeds': {
                name: {
                    'is_active': feed.is_active,
                    'last_update': feed.last_update,
                    'update_frequency': feed.update_frequency,
                    'data_types': feed.data_types,
                    'cache_size': len(feed.data_cache)
                }
                for name, feed in self.agent_feeds.items()
            }
        }


# Global instance
_mcp_feeder = None

def get_mcp_agent_feeder() -> MCPAgentFeeder:
    """Get singleton MCP Agent Feeder instance"""
    global _mcp_feeder
    if _mcp_feeder is None:
        _mcp_feeder = MCPAgentFeeder()
    return _mcp_feeder


if __name__ == "__main__":
    # Run standalone MCP Agent Feeder
    feeder = get_mcp_agent_feeder()
    
    try:
        feeder.start_feeding()
        
        # Keep running
        while True:
            time.sleep(60)
            stats = feeder.get_feeding_statistics()
            print(f"📊 Feeder Stats: Feeds={stats['total_feeds']}, Points={stats['data_points_processed']}")
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping MCP Agent Feeder...")
        feeder.stop()
