"""
Enhanced Geopolitical Agent V2 - Real Political & Geopolitical Analysis
Connects to real news sources for political events, conflicts, elections, etc.
"""
import requests
import feedparser
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd
from data_layer.news_loader_fixed import NewsLoader


class GeopoliticalAgentV2Enhanced:
    """
    Enhanced Geopolitical Analysis Agent with Real Data Sources
    
    Analyzes REAL political events from:
    - Reuters World News RSS
    - BBC World News RSS  
    - Al Jazeera RSS
    - Associated Press World News
    - Financial Times Geopolitical News
    """
    
    def __init__(self):
        self.news_loader = NewsLoader()
        self.safe_haven_currencies = ['USD', 'CHF', 'JPY']
        self.risk_on_currencies = ['EUR', 'GBP', 'AUD', 'NZD', 'CAD']
        
        # Real RSS feeds for geopolitical news
        self.geopolitical_rss_feeds = {
            'reuters_world': 'https://www.reuters.com/rssFeed/worldNews',
            'bbc_world': 'http://feeds.bbci.co.uk/news/world/rss.xml',
            'al_jazeera': 'https://www.aljazeera.com/xml/rss/all.xml',
            'ap_world': 'https://feeds.apnews.com/rss/world',
            'ft_world': 'https://www.ft.com/rss/world'
        }
        
        # Enhanced geopolitical keywords
        self.geopolitical_keywords = {
            'high_risk': [
                'war', 'conflict', 'tension', 'sanction', 'crisis', 'attack',
                'election', 'political', 'protest', 'unrest', 'turmoil', 'invasion',
                'missile', 'nuclear', 'terrorism', 'cyber attack', 'trade war',
                'geopolitical', 'diplomatic', 'embargo', 'border', 'refugee'
            ],
            'safe_haven': [
                'flight to safety', 'safe haven', 'risk aversion', 'uncertainty',
                'market volatility', 'investors flee', 'capital flight'
            ],
            'central_bank': [
                'federal reserve', 'ecb', 'bank of england', 'bank of japan',
                'central bank', 'monetary policy', 'interest rate', 'inflation'
            ]
        }
        
    def generate_signal(
        self,
        currencies: List[str],
        lookback_hours: int = 72  # 3 days for geopolitical events
    ) -> Dict:
        """
        Generate geopolitical signal using REAL data sources
        
        Returns:
            {
                'signal': 1 (BUY), -1 (SELL), 0 (NEUTRAL),
                'confidence': 0.0-1.0,
                'features_used': {...},
                'deterministic_reason': 'Explanation based on real events'
            }
        """
        try:
            # Get real geopolitical news from RSS feeds
            geopolitical_news = self._fetch_geopolitical_news(lookback_hours)
            
            # Get existing news from database
            db_news = self.news_loader.load_news(
                currencies=currencies,
                start_time=datetime.now() - timedelta(hours=lookback_hours),
                limit=500
            )
            
            # Combine real RSS news with database news
            all_news = self._combine_news_sources(geopolitical_news, db_news)
            
            if all_news.empty:
                return {
                    'signal': 0,
                    'confidence': 0.0,
                    'features_used': {},
                    'deterministic_reason': 'No real geopolitical data available'
                }
            
            # Filter for relevant geopolitical content
            relevant_news = self._filter_geopolitical_content(all_news, currencies)
            
            if relevant_news.empty:
                return {
                    'signal': 0,
                    'confidence': 0.0,
                    'features_used': {'news_count': 0, 'geopolitical_score': 0.0},
                    'deterministic_reason': 'No relevant geopolitical events found'
                }
            
            # Analyze geopolitical content
            geopolitical_score = self._analyze_geopolitical_content(relevant_news, currencies)
            
            # Determine safe-haven vs risk-on bias
            safe_haven_bias = self._calculate_safe_haven_bias(currencies, geopolitical_score)
            
            # Generate signal based on currency composition
            signal = self._generate_currency_signal(currencies, safe_haven_bias)
            
            # Calculate confidence based on data quality
            confidence = self._calculate_confidence(relevant_news, geopolitical_score)
            
            return {
                'signal': signal,
                'confidence': confidence,
                'features_used': {
                    'geopolitical_score': geopolitical_score,
                    'safe_haven_bias': safe_haven_bias,
                    'news_count': len(relevant_news),
                    'rss_sources': len(geopolitical_news) if not geopolitical_news.empty else 0,
                    'timeframe_hours': lookback_hours
                },
                'deterministic_reason': self._generate_reasoning(
                    signal, geopolitical_score, safe_haven_bias, currencies, relevant_news
                )
            }
            
        except Exception as e:
            return {
                'signal': 0,
                'confidence': 0.0,
                'features_used': {},
                'deterministic_reason': f'Geopolitical analysis failed: {str(e)}'
            }
    
    def _fetch_geopolitical_news(self, lookback_hours: int) -> pd.DataFrame:
        """Fetch real news from geopolitical RSS feeds"""
        articles = []
        cutoff_time = datetime.now() - timedelta(hours=lookback_hours)
        
        for source, feed_url in self.geopolitical_rss_feeds.items():
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries:
                    # Parse publication date
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        pub_date = datetime(*entry.updated_parsed[:6])
                    else:
                        continue
                    
                    # Only include recent articles
                    if pub_date >= cutoff_time:
                        articles.append({
                            'title': entry.title if hasattr(entry, 'title') else '',
                            'content': entry.summary if hasattr(entry, 'summary') else entry.description if hasattr(entry, 'description') else '',
                            'source': source,
                            'published_at': pub_date,
                            'url': entry.link if hasattr(entry, 'link') else ''
                        })
                        
            except Exception as e:
                # Continue with other feeds if one fails
                continue
        
        return pd.DataFrame(articles)
    
    def _combine_news_sources(self, rss_news: pd.DataFrame, db_news: pd.DataFrame) -> pd.DataFrame:
        """Combine RSS news with database news"""
        if rss_news.empty and db_news.empty:
            return pd.DataFrame()
        
        # Standardize column names
        if not rss_news.empty:
            rss_news = rss_news.rename(columns={'published_at': 'timestamp'})
        
        if not db_news.empty:
            db_news = db_news.rename(columns={'published_at': 'timestamp'})
        
        # Combine both sources
        combined = pd.concat([rss_news, db_news], ignore_index=True)
        
        # Ensure we have required columns
        if 'content' not in combined.columns:
            combined['content'] = combined.get('summary', combined.get('description', ''))
        
        if 'title' not in combined.columns:
            combined['title'] = ''
        
        # Remove duplicates based on title and timestamp
        if not combined.empty:
            combined = combined.drop_duplicates(subset=['title', 'timestamp'])
        
        return combined
    
    def _filter_geopolitical_content(self, news_df: pd.DataFrame, currencies: List[str]) -> pd.DataFrame:
        """Filter news for geopolitical relevance to specific currencies"""
        if news_df.empty:
            return pd.DataFrame()
        
        relevant_articles = []
        
        # Create text for analysis (title + content)
        for _, article in news_df.iterrows():
            text = f"{article.get('title', '')} {article.get('content', '')}".lower()
            
            # Check for geopolitical keywords
            has_geopolitical = any(keyword in text for keyword in self.geopolitical_keywords['high_risk'])
            has_safe_haven = any(keyword in text for keyword in self.geopolitical_keywords['safe_haven'])
            has_central_bank = any(keyword in text for keyword in self.geopolitical_keywords['central_bank'])
            
            # Check for currency relevance
            currency_relevant = any(currency.lower() in text for currency in currencies)
            
            # Include if geopolitically relevant and currency-relevant
            if (has_geopolitical or has_safe_haven or has_central_bank) and currency_relevant:
                relevant_articles.append(article)
        
        return pd.DataFrame(relevant_articles)
    
    def _analyze_geopolitical_content(self, news_df: pd.DataFrame, currencies: List[str]) -> float:
        """Analyze news content for geopolitical relevance"""
        if news_df.empty:
            return 0.0
        
        total_score = 0.0
        relevant_articles = 0
        
        for _, article in news_df.iterrows():
            text = f"{article.get('title', '')} {article.get('content', '')}".lower()
            
            article_score = 0.0
            
            # Check for high-risk keywords (higher weight)
            for keyword in self.geopolitical_keywords['high_risk']:
                if keyword in text:
                    article_score += 2.0
            
            # Check for safe-haven keywords  
            for keyword in self.geopolitical_keywords['safe_haven']:
                if keyword in text:
                    article_score += 1.0
            
            # Check for central bank keywords
            for keyword in self.geopolitical_keywords['central_bank']:
                if keyword in text:
                    article_score += 0.5
            
            if article_score > 0:
                total_score += article_score
                relevant_articles += 1
        
        return total_score / max(relevant_articles, 1)
    
    def _calculate_safe_haven_bias(self, currencies: List[str], geopolitical_score: float) -> float:
        """Calculate bias towards safe-haven vs risk-on currencies"""
        if geopolitical_score < 0.5:
            return 0.0  # No significant geopolitical impact
        
        # Count safe-haven vs risk-on currencies in the pair
        safe_haven_count = sum(1 for c in currencies if c in self.safe_haven_currencies)
        risk_on_count = sum(1 for c in currencies if c in self.risk_on_currencies)
        
        if safe_haven_count == risk_on_count:
            return 0.0  # Balanced pair
        
        # Higher geopolitical score increases safe-haven appeal
        bias_strength = min(geopolitical_score / 5.0, 1.0)  # Normalize to 0-1
        
        if safe_haven_count > risk_on_count:
            return bias_strength  # Positive bias = favor safe-haven
        else:
            return -bias_strength  # Negative bias = favor risk-on
    
    def _generate_currency_signal(self, currencies: List[str], safe_haven_bias: float) -> int:
        """Generate trading signal based on safe-haven bias"""
        if abs(safe_haven_bias) < 0.3:  # Low bias threshold
            return 0  # NEUTRAL
        
        safe_haven_count = sum(1 for c in currencies if c in self.safe_haven_currencies)
        risk_on_count = sum(1 for c in currencies if c in self.risk_on_currencies)
        
        if safe_haven_count > risk_on_count:
            # Pair has more safe-haven currencies
            return 1 if safe_haven_bias > 0 else -1  # BUY for safe-haven demand, SELL for risk-on
        else:
            # Pair has more risk-on currencies
            return -1 if safe_haven_bias > 0 else 1  # SELL for safe-haven demand, BUY for risk-on
    
    def _calculate_confidence(self, news_df: pd.DataFrame, geopolitical_score: float) -> float:
        """Calculate confidence based on data quality and relevance"""
        if news_df.empty:
            return 0.0
        
        # Base confidence from article count
        article_confidence = min(len(news_df) / 20.0, 1.0)  # More articles = higher confidence
        
        # Boost confidence if geopolitical relevance is high
        relevance_boost = min(geopolitical_score / 3.0, 0.5)
        
        # Time decay - more recent articles have higher confidence
        now = datetime.now()
        time_weights = []
        
        for _, article in news_df.iterrows():
            timestamp = article.get('timestamp', article.get('published_at', now))
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except:
                    timestamp = now
            
            age_hours = (now - timestamp).total_seconds() / 3600
            time_weight = max(0, 1 - (age_hours / 72))  # Linear decay over 3 days
            time_weights.append(time_weight)
        
        time_confidence = sum(time_weights) / len(time_weights) if time_weights else 0
        
        # Combine confidence factors
        final_confidence = (article_confidence * 0.4 + relevance_boost * 0.3 + time_confidence * 0.3)
        
        return min(final_confidence, 1.0)
    
    def _generate_reasoning(
        self, 
        signal: int, 
        geopolitical_score: float, 
        safe_haven_bias: float, 
        currencies: List[str],
        news_df: pd.DataFrame
    ) -> str:
        """Generate deterministic reasoning for the signal"""
        signal_map = {1: 'BUY', -1: 'SELL', 0: 'NEUTRAL'}
        
        if signal == 0:
            return f"NEUTRAL: Low geopolitical impact (score: {geopolitical_score:.2f})"
        
        direction = "safe-haven demand" if safe_haven_bias > 0 else "risk appetite"
        
        # Get most recent relevant event for context
        recent_events = []
        if not news_df.empty:
            recent_news = news_df.nlargest(3, 'timestamp')  # Top 3 most recent
            for _, article in recent_news.iterrows():
                title = article.get('title', '')[:50] + '...' if len(article.get('title', '')) > 50 else article.get('title', '')
                recent_events.append(title)
        
        events_context = f" Recent events: {', '.join(recent_events[:2])}" if recent_events else ""
        
        return (
            f"{signal_map[signal]}: High geopolitical activity (score: {geopolitical_score:.2f}) "
            f"driving {direction}. {'Safe-haven' if safe_haven_bias > 0 else 'Risk-on'} "
            f"currencies showing strength.{events_context}"
        )
