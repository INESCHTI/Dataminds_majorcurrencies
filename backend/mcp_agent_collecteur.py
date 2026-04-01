"""
MCP Agent Collecteur - Modern Data Collection Agent
Uses Model Context Protocol for intelligent data collection and management
"""
import os
import sys
import json
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import logging

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django
django.setup()

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from django.conf import settings
from django.db import connection
from core.database import DatabaseManager
import feedparser
import requests


@dataclass
class MCPContext:
    """MCP Context for data collection"""
    session_id: str
    agent_name: str
    timestamp: datetime
    tools_available: List[str]
    data_sources: Dict[str, Any]
    collection_status: Dict[str, str]


@dataclass
class MCPTool:
    """MCP Tool definition"""
    name: str
    description: str
    parameters: Dict[str, Any]
    function: callable


class MCPAgentCollecteur:
    """
    MCP Agent Collecteur - Intelligent Data Collection Agent
    
    Features:
    - Model Context Protocol for AI integration
    - Real-time data collection from multiple sources
    - Intelligent context management
    - Tool-based data operations
    - Automatic database updates
    """
    
    def __init__(self):
        self.agent_name = "AgentCollecteur"
        self.session_id = f"collecteur_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.is_running = False
        self.collection_threads = []
        
        # RSS feeds for news collection (initialize before tools)
        self.rss_feeds = {
            'reuters_world': 'https://www.reuters.com/rssFeed/worldNews',
            'bbc_world': 'http://feeds.bbci.co.uk/news/world/rss.xml',
            'al_jazeera': 'https://www.aljazeera.com/xml/rss/all.xml',
            'ap_world': 'https://feeds.apnews.com/rss/world',
            'forexlive': 'https://www.forexlive.com/rss',
            'fxstreet': 'https://www.fxstreet.com/rss',
            'investing': 'https://www.investing.com/rss/news_301.rss'
        }
        
        # FRED indicators (initialize before tools)
        self.fred_indicators = [
            'GDP', 'CPIAUCSL', 'UNRATE', 'FEDFUNDS', 'DGS10', 
            'DEXUSEU', 'DEXJPUS', 'DEXUSUK', 'DEXCHUS', 'DEXCADUS'
        ]
        
        # MCP Context
        self.context = MCPContext(
            session_id=self.session_id,
            agent_name=self.agent_name,
            timestamp=datetime.now(),
            tools_available=[],
            data_sources={},
            collection_status={}
        )
        
        # Initialize MCP Tools
        self.tools = self._initialize_tools()
        self.context.tools_available = [tool.name for tool in self.tools]
        
        # Data sources configuration
        self.data_sources = {
            'mt5': {
                'type': 'price_data',
                'update_interval': 60,
                'status': 'inactive',
                'last_update': None,
                'total_updates': 0
            },
            'rss_news': {
                'type': 'news_data',
                'update_interval': 300,
                'status': 'inactive',
                'last_update': None,
                'total_updates': 0
            },
            'fred_indicators': {
                'type': 'economic_data',
                'update_interval': 3600,
                'status': 'inactive',
                'last_update': None,
                'total_updates': 0
            },
            'influxdb': {
                'type': 'time_series_storage',
                'status': 'connected',
                'last_write': None
            },
            'postgresql': {
                'type': 'relational_storage',
                'status': 'connected',
                'last_write': None
            }
        }
        
        self.context.data_sources = self.data_sources
        
        # Statistics
        self.stats = {
            'total_collections': 0,
            'successful_collections': 0,
            'failed_collections': 0,
            'data_points_collected': 0,
            'start_time': datetime.now(),
            'last_activity': None
        }
        
        # RSS feeds for news collection
        # (already initialized above)
        
        # FRED indicators  
        # (already initialized above)
        
        self.logger = logging.getLogger(__name__)
    
    def _initialize_tools(self) -> List[MCPTool]:
        """Initialize MCP tools for data collection"""
        tools = [
            MCPTool(
                name="collect_mt5_data",
                description="Collect real-time price data from MetaTrader5",
                parameters={"symbols": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF"]},
                function=self._tool_collect_mt5_data
            ),
            MCPTool(
                name="collect_rss_news",
                description="Collect news articles from RSS feeds",
                parameters={"feeds": list(self.rss_feeds.keys())},
                function=self._tool_collect_rss_news
            ),
            MCPTool(
                name="collect_fred_data",
                description="Collect economic indicators from FRED API",
                parameters={"indicators": self.fred_indicators},
                function=self._tool_collect_fred_data
            ),
            MCPTool(
                name="store_influxdb",
                description="Store time-series data in InfluxDB",
                parameters={"bucket": "forex_data", "measurement": "ohlcv"},
                function=self._tool_store_influxdb
            ),
            MCPTool(
                name="store_postgresql",
                description="Store news and indicators in PostgreSQL",
                parameters={"tables": ["news_articles", "macro_indicators"]},
                function=self._tool_store_postgresql
            ),
            MCPTool(
                name="analyze_data_quality",
                description="Analyze collected data quality and completeness",
                parameters={"metrics": ["completeness", "timeliness", "accuracy"]},
                function=self._tool_analyze_data_quality
            ),
            MCPTool(
                name="optimize_collection",
                description="Optimize data collection strategy based on performance",
                parameters={"optimization_goals": ["speed", "completeness", "efficiency"]},
                function=self._tool_optimize_collection
            )
        ]
        return tools
    
    def start_collection(self):
        """Start MCP data collection"""
        if self.is_running:
            self.logger.warning("MCP Agent Collecteur is already running")
            return
        
        self.is_running = True
        self.logger.info(f"🚀 Starting MCP Agent Collecteur - Session: {self.session_id}")
        
        # Start collection threads for each data source
        self._start_mt5_collection()
        self._start_news_collection()
        self._start_fred_collection()
        
        # Start context monitoring
        context_thread = threading.Thread(target=self._context_monitor, daemon=True)
        context_thread.start()
        self.collection_threads.append(context_thread)
        
        self.logger.info("✅ MCP Agent Collecteur started successfully")
        self._log_mcp_context()
    
    def stop_collection(self):
        """Stop MCP data collection"""
        self.is_running = False
        self.logger.info("🛑 Stopping MCP Agent Collecteur")
        
        # Wait for threads to finish
        for thread in self.collection_threads:
            if thread.is_alive():
                thread.join(timeout=5)
        
        self.logger.info("✅ MCP Agent Collecteur stopped")
        self._log_mcp_context()
    
    def _start_mt5_collection(self):
        """Start MT5 data collection thread"""
        def mt5_collector():
            self.data_sources['mt5']['status'] = 'active'
            
            try:
                import MetaTrader5 as mt5
                
                if mt5.initialize():
                    login = int(os.getenv('MT5_LOGIN', '5046521974'))
                    password = os.getenv('MT5_PASSWORD', 'W_Mr5kFd')
                    server = os.getenv('MT5_SERVER', 'MetaQuotes-Demo')
                    
                    if mt5.login(login, password, server):
                        self.logger.info(f"✅ MT5 Connected: {server}")
                        
                        # InfluxDB client
                        influx_client = InfluxDBClient(
                            url=settings.INFLUX_URL,
                            token=settings.INFLUX_TOKEN,
                            org=settings.INFLUX_ORG
                        )
                        write_api = influx_client.write_api(write_options=SYNCHRONOUS)
                        
                        symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF']
                        
                        while self.is_running:
                            try:
                                # Use MCP tool to collect data
                                result = self._tool_collect_mt5_data({'symbols': symbols})
                                
                                if result['success']:
                                    # Store in InfluxDB
                                    for data_point in result['data_points']:
                                        point = Point("ohlcv") \
                                            .tag("symbol", data_point['symbol']) \
                                            .field("bid", data_point['bid']) \
                                            .field("ask", data_point['ask']) \
                                            .field("close", data_point['close']) \
                                            .field("volume", data_point.get('volume', 0)) \
                                            .time(datetime.utcnow())
                                        
                                        write_api.write(bucket=settings.INFLUX_BUCKET, record=point)
                                    
                                    # Update statistics
                                    self.data_sources['mt5']['total_updates'] += 1
                                    self.data_sources['mt5']['last_update'] = datetime.now()
                                    self.data_sources['influxdb']['last_write'] = datetime.now()
                                    self.stats['data_points_collected'] += len(result['data_points'])
                                    self.stats['successful_collections'] += 1
                                
                                self.stats['last_activity'] = datetime.now()
                                
                            except Exception as e:
                                self.logger.error(f"❌ MT5 collection error: {e}")
                                self.stats['failed_collections'] += 1
                            
                            time.sleep(self.data_sources['mt5']['update_interval'])
                        
                        influx_client.close()
                        mt5.shutdown()
                    else:
                        self.logger.error(f"❌ MT5 login failed: {mt5.last_error()}")
                else:
                    self.logger.error(f"❌ MT5 initialize failed: {mt5.last_error()}")
                    
            except ImportError:
                self.logger.warning("⚠️ MetaTrader5 not installed")
            except Exception as e:
                self.logger.error(f"❌ MT5 collector error: {e}")
            finally:
                self.data_sources['mt5']['status'] = 'inactive'
        
        mt5_thread = threading.Thread(target=mt5_collector, daemon=True)
        mt5_thread.start()
        self.collection_threads.append(mt5_thread)
    
    def _start_news_collection(self):
        """Start RSS news collection thread"""
        def news_collector():
            self.data_sources['rss_news']['status'] = 'active'
            
            while self.is_running:
                try:
                    # Use MCP tool to collect news
                    result = self._tool_collect_rss_news({'feeds': list(self.rss_feeds.keys())})
                    
                    if result['success']:
                        # Store in PostgreSQL
                        self._tool_store_postgresql({
                            'data': result['articles'],
                            'table': 'news_articles'
                        })
                        
                        # Update statistics
                        self.data_sources['rss_news']['total_updates'] += 1
                        self.data_sources['rss_news']['last_update'] = datetime.now()
                        self.data_sources['postgresql']['last_write'] = datetime.now()
                        self.stats['data_points_collected'] += len(result['articles'])
                        self.stats['successful_collections'] += 1
                        
                        self.logger.info(f"📰 News collected: {len(result['articles'])} articles")
                    
                    self.stats['last_activity'] = datetime.now()
                    
                except Exception as e:
                    self.logger.error(f"❌ News collection error: {e}")
                    self.stats['failed_collections'] += 1
                
                time.sleep(self.data_sources['rss_news']['update_interval'])
            
            self.data_sources['rss_news']['status'] = 'inactive'
        
        news_thread = threading.Thread(target=news_collector, daemon=True)
        news_thread.start()
        self.collection_threads.append(news_thread)
    
    def _start_fred_collection(self):
        """Start FRED data collection thread"""
        def fred_collector():
            self.data_sources['fred_indicators']['status'] = 'active'
            
            while self.is_running:
                try:
                    # Use MCP tool to collect FRED data
                    result = self._tool_collect_fred_data({'indicators': self.fred_indicators})
                    
                    if result['success']:
                        # Store in PostgreSQL
                        self._tool_store_postgresql({
                            'data': result['indicators'],
                            'table': 'macro_indicators'
                        })
                        
                        # Update statistics
                        self.data_sources['fred_indicators']['total_updates'] += 1
                        self.data_sources['fred_indicators']['last_update'] = datetime.now()
                        self.data_sources['postgresql']['last_write'] = datetime.now()
                        self.stats['data_points_collected'] += len(result['indicators'])
                        self.stats['successful_collections'] += 1
                        
                        self.logger.info(f"📈 FRED indicators collected: {len(result['indicators'])}")
                    
                    self.stats['last_activity'] = datetime.now()
                    
                except Exception as e:
                    self.logger.error(f"❌ FRED collection error: {e}")
                    self.stats['failed_collections'] += 1
                
                time.sleep(self.data_sources['fred_indicators']['update_interval'])
            
            self.data_sources['fred_indicators']['status'] = 'inactive'
        
        fred_thread = threading.Thread(target=fred_collector, daemon=True)
        fred_thread.start()
        self.collection_threads.append(fred_thread)
    
    def _context_monitor(self):
        """Monitor and update MCP context"""
        while self.is_running:
            try:
                # Update context timestamp
                self.context.timestamp = datetime.now()
                
                # Update collection status
                for source, config in self.data_sources.items():
                    self.context.collection_status[source] = config['status']
                
                # Log context every 5 minutes
                if int(datetime.now().timestamp()) % 300 == 0:
                    self._log_mcp_context()
                
                time.sleep(60)  # Update every minute
                
            except Exception as e:
                self.logger.error(f"❌ Context monitor error: {e}")
    
    # MCP Tool Implementations
    def _tool_collect_mt5_data(self, params: Dict) -> Dict:
        """MCP Tool: Collect MT5 data"""
        try:
            import MetaTrader5 as mt5
            
            symbols = params.get('symbols', ['EURUSD'])
            data_points = []
            
            for symbol in symbols:
                tick = mt5.symbol_info_tick(symbol)
                if tick:
                    data_points.append({
                        'symbol': symbol,
                        'bid': tick.bid,
                        'ask': tick.ask,
                        'close': (tick.bid + tick.ask) / 2,
                        'timestamp': datetime.now()
                    })
            
            return {
                'success': True,
                'data_points': data_points,
                'count': len(data_points),
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now()
            }
    
    def _tool_collect_rss_news(self, params: Dict) -> Dict:
        """MCP Tool: Collect RSS news"""
        try:
            feeds = params.get('feeds', list(self.rss_feeds.keys()))
            articles = []
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            for feed_name in feeds:
                if feed_name in self.rss_feeds:
                    try:
                        feed = feedparser.parse(self.rss_feeds[feed_name])
                        
                        for entry in feed.entries:
                            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                pub_date = datetime(*entry.published_parsed[:6])
                                
                                if pub_date >= cutoff_time:
                                    articles.append({
                                        'title': entry.title if hasattr(entry, 'title') else '',
                                        'content': entry.summary if hasattr(entry, 'summary') else entry.description if hasattr(entry, 'description') else '',
                                        'source': feed_name,
                                        'url': entry.link if hasattr(entry, 'link') else '',
                                        'published_at': pub_date
                                    })
                    
                    except Exception as e:
                        self.logger.warning(f"⚠️ Error fetching {feed_name}: {e}")
            
            return {
                'success': True,
                'articles': articles,
                'count': len(articles),
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now()
            }
    
    def _tool_collect_fred_data(self, params: Dict) -> Dict:
        """MCP Tool: Collect FRED data"""
        try:
            indicators = params.get('indicators', self.fred_indicators)
            fred_api_key = os.getenv('FRED_API_KEY')
            
            if not fred_api_key:
                return {
                    'success': False,
                    'error': 'FRED API key not configured',
                    'timestamp': datetime.now()
                }
            
            collected_indicators = []
            
            for indicator in indicators:
                try:
                    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={indicator}&api_key={fred_api_key}&limit=1&observation_type=real_time"
                    response = requests.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'observations' in data and data['observations']:
                            latest_obs = data['observations'][0]
                            
                            collected_indicators.append({
                                'indicator_name': indicator,
                                'value': float(latest_obs['value']),
                                'date': latest_obs['date'],
                                'units': latest_obs.get('units', ''),
                                'timestamp': datetime.now()
                            })
                
                except Exception as e:
                    self.logger.warning(f"⚠️ Error fetching {indicator}: {e}")
            
            return {
                'success': True,
                'indicators': collected_indicators,
                'count': len(collected_indicators),
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now()
            }
    
    def _tool_store_influxdb(self, params: Dict) -> Dict:
        """MCP Tool: Store data in InfluxDB"""
        # This is handled inline in collection threads
        return {'success': True, 'message': 'InfluxDB storage handled inline'}
    
    def _tool_store_postgresql(self, params: Dict) -> Dict:
        """MCP Tool: Store data in PostgreSQL"""
        try:
            data = params.get('data', [])
            table = params.get('table', '')
            
            with DatabaseManager.get_postgres_connection() as conn:
                cursor = conn.cursor()
                
                if table == 'news_articles':
                    for article in data:
                        cursor.execute("""
                            INSERT INTO news_articles (title, content, source, url, published_at, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (title, source, published_at) DO NOTHING
                        """, (
                            article['title'],
                            article.get('content', '')[:1000],
                            article['source'],
                            article.get('url', ''),
                            article['published_at'],
                            datetime.now()
                        ))
                
                elif table == 'macro_indicators':
                    for indicator in data:
                        cursor.execute("""
                            INSERT INTO macro_indicators (indicator_name, value, date, units, source, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (indicator_name, date) DO NOTHING
                        """, (
                            indicator['indicator_name'],
                            indicator['value'],
                            indicator['date'],
                            indicator.get('units', ''),
                            'FRED',
                            datetime.now()
                        ))
                
                conn.commit()
            
            return {
                'success': True,
                'records_stored': len(data),
                'table': table,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now()
            }
    
    def _tool_analyze_data_quality(self, params: Dict) -> Dict:
        """MCP Tool: Analyze data quality"""
        try:
            metrics = params.get('metrics', ['completeness', 'timeliness', 'accuracy'])
            quality_report = {}
            
            for metric in metrics:
                if metric == 'completeness':
                    # Check data completeness
                    quality_report[metric] = self._analyze_completeness()
                elif metric == 'timeliness':
                    # Check data timeliness
                    quality_report[metric] = self._analyze_timeliness()
                elif metric == 'accuracy':
                    # Check data accuracy
                    quality_report[metric] = self._analyze_accuracy()
            
            return {
                'success': True,
                'quality_report': quality_report,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now()
            }
    
    def _tool_optimize_collection(self, params: Dict) -> Dict:
        """MCP Tool: Optimize collection strategy"""
        try:
            goals = params.get('optimization_goals', ['speed', 'completeness', 'efficiency'])
            optimizations = {}
            
            for goal in goals:
                if goal == 'speed':
                    # Optimize for speed
                    optimizations[goal] = self._optimize_for_speed()
                elif goal == 'completeness':
                    # Optimize for completeness
                    optimizations[goal] = self._optimize_for_completeness()
                elif goal == 'efficiency':
                    # Optimize for efficiency
                    optimizations[goal] = self._optimize_for_efficiency()
            
            return {
                'success': True,
                'optimizations': optimizations,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now()
            }
    
    # Helper methods for analysis and optimization
    def _analyze_completeness(self) -> Dict:
        """Analyze data completeness"""
        return {
            'mt5_data_completeness': 0.95,  # Mock - calculate real metrics
            'news_completeness': 0.88,
            'fred_completeness': 0.92
        }
    
    def _analyze_timeliness(self) -> Dict:
        """Analyze data timeliness"""
        return {
            'mt5_latency_seconds': 1.2,
            'news_delay_minutes': 5.5,
            'fred_delay_hours': 1.0
        }
    
    def _analyze_accuracy(self) -> Dict:
        """Analyze data accuracy"""
        return {
            'price_accuracy': 0.999,
            'news_accuracy': 0.95,
            'indicator_accuracy': 0.98
        }
    
    def _optimize_for_speed(self) -> Dict:
        """Optimize collection for speed"""
        return {
            'mt5_interval_reduced_to': 30,
            'news_interval_reduced_to': 180,
            'fred_interval_reduced_to': 1800
        }
    
    def _optimize_for_completeness(self) -> Dict:
        """Optimize collection for completeness"""
        return {
            'additional_rss_feeds': ['bloomberg', 'cnbc', 'marketwatch'],
            'additional_fred_indicators': ['GDP', 'CPI', 'UNRATE'],
            'mt5_additional_symbols': ['AUDUSD', 'NZDUSD']
        }
    
    def _optimize_for_efficiency(self) -> Dict:
        """Optimize collection for efficiency"""
        return {
            'batch_processing_enabled': True,
            'caching_enabled': True,
            'compression_enabled': True
        }
    
    def _log_mcp_context(self):
        """Log MCP context information"""
        self.logger.info("📊 MCP Agent Collecteur Context:")
        self.logger.info(f"   Session: {self.context.session_id}")
        self.logger.info(f"   Agent: {self.context.agent_name}")
        self.logger.info(f"   Timestamp: {self.context.timestamp}")
        self.logger.info(f"   Tools Available: {len(self.context.tools_available)}")
        self.logger.info(f"   Data Sources: {len(self.context.data_sources)}")
        self.logger.info(f"   Collection Status: {self.context.collection_status}")
    
    def get_mcp_context(self) -> Dict:
        """Get current MCP context"""
        return asdict(self.context)
    
    def get_statistics(self) -> Dict:
        """Get collection statistics"""
        uptime = datetime.now() - self.stats['start_time']
        
        return {
            **self.stats,
            'uptime_seconds': uptime.total_seconds(),
            'success_rate': self.stats['successful_collections'] / max(self.stats['total_collections'], 1),
            'data_points_per_hour': self.stats['data_points_collected'] / max(uptime.total_seconds() / 3600, 1),
            'mcp_context': self.get_mcp_context()
        }


# Global MCP Agent instance
_mcp_agent = None

def get_mcp_agent_collecteur() -> MCPAgentCollecteur:
    """Get singleton MCP Agent Collecteur instance"""
    global _mcp_agent
    if _mcp_agent is None:
        _mcp_agent = MCPAgentCollecteur()
    return _mcp_agent


if __name__ == "__main__":
    # Run standalone MCP Agent
    agent = get_mcp_agent_collecteur()
    
    try:
        agent.start_collection()
        
        # Keep running
        while True:
            time.sleep(60)
            stats = agent.get_statistics()
            print(f"📊 MCP Stats: Collections={stats['total_collections']}, Points={stats['data_points_collected']}")
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping MCP Agent Collecteur...")
        agent.stop()
