"""
Sentiment Agent (DSO1.3)
Analyzes news sentiment using NLP to gauge market psychology
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import subprocess
import io
import re
from .base_agent import BaseAgent, Signal


class SentimentAgent(BaseAgent):
    """
    Sentiment Analysis Agent
    Analyzes financial news sentiment using keyword-based and rule-based NLP
    Future: Integrate FinBERT transformer model for advanced sentiment
    """
    
    def __init__(self, 
                 name: str = "Sentiment Agent",
                 weight: float = 1.0,
                 lookback_days: int = 7):
        """
        Initialize Sentiment Agent
        
        Args:
            name: Agent name
            weight: Agent weight in ensemble
            lookback_days: Number of days to look back for news
        """
        super().__init__(name, weight)
        self.lookback_days = lookback_days
        
        # Sentiment lexicon (simplified - can be expanded)
        self.positive_words = {
            'bullish', 'rally', 'surge', 'gain', 'rise', 'soar', 'jump', 
            'strengthen', 'boost', 'optimistic', 'positive', 'upbeat', 
            'recovery', 'growth', 'improve', 'strong', 'robust', 'advance',
            'outperform', 'beat', 'better', 'upgrade', 'buy', 'confidence'
        }
        
        self.negative_words = {
            'bearish', 'crash', 'plunge', 'fall', 'drop', 'decline', 'slump',
            'weaken', 'concern', 'pessimistic', 'negative', 'worry', 'fear',
            'recession', 'slowdown', 'worse', 'weak', 'deteriorate', 'risk',
            'downgrade', 'sell', 'loss', 'miss', 'disappoint', 'crisis'
        }
        
        # Intensity modifiers
        self.intensifiers = {
            'very', 'extremely', 'highly', 'significantly', 'substantially',
            'dramatically', 'sharply', 'strongly', 'severely'
        }
        
        self.diminishers = {
            'slightly', 'somewhat', 'marginally', 'moderately', 'partially'
        }
    
    def get_required_data(self) -> List[str]:
        """Required news data columns"""
        return ['published_at', 'title', 'content', 'source', 'currencies']
    
    def fetch_news_data(self, days_back: int = 7) -> pd.DataFrame:
        """
        Fetch news articles from PostgreSQL via Docker
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            DataFrame with news articles
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            query = f"""
            COPY (
                SELECT * FROM news_articles 
                WHERE published_at >= '{cutoff_date}'
                ORDER BY published_at DESC
            ) TO STDOUT WITH CSV HEADER
            """
            
            result = subprocess.run(
                ['docker', 'exec', 'forex-postgres', 'psql', '-U', 'forex_user',
                 '-d', 'forex_metadata', '-c', query],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                df = pd.read_csv(io.StringIO(result.stdout))
                df['published_at'] = pd.to_datetime(df['published_at'])
                return df
            else:
                return pd.DataFrame()
        except Exception as e:
            print(f"Error fetching news data: {e}")
            return pd.DataFrame()
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if pd.isna(text):
            return ""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)  # Remove punctuation
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        return text.strip()
    
    def calculate_sentiment_score(self, text: str) -> float:
        """
        Calculate sentiment score for text using lexicon-based approach
        
        Args:
            text: Input text (title or content)
            
        Returns:
            Sentiment score from -1 (very negative) to +1 (very positive)
        """
        if not text:
            return 0.0
        
        cleaned_text = self.clean_text(text)
        words = cleaned_text.split()
        
        if not words:
            return 0.0
        
        positive_count = 0
        negative_count = 0
        intensity_modifier = 1.0
        
        for i, word in enumerate(words):
            # Check for intensifiers/diminishers
            if word in self.intensifiers:
                intensity_modifier = 1.5
                continue
            elif word in self.diminishers:
                intensity_modifier = 0.5
                continue
            
            # Count sentiment words
            if word in self.positive_words:
                positive_count += intensity_modifier
            elif word in self.negative_words:
                negative_count += intensity_modifier
            
            # Reset intensity modifier
            intensity_modifier = 1.0
        
        # Calculate net sentiment
        total_sentiment_words = positive_count + negative_count
        
        if total_sentiment_words == 0:
            return 0.0
        
        net_sentiment = (positive_count - negative_count) / total_sentiment_words
        
        # Normalize to [-1, 1]
        return np.clip(net_sentiment, -1.0, 1.0)
    
    def filter_news_for_currency(self, news_df: pd.DataFrame, currency: str) -> pd.DataFrame:
        """
        Filter news articles relevant to a specific currency
        
        Args:
            news_df: News DataFrame
            currency: Currency code (e.g., 'USD', 'EUR')
            
        Returns:
            Filtered DataFrame
        """
        if 'currencies' not in news_df.columns:
            return news_df
        
        # Filter by currency tag
        relevant_news = news_df[
            news_df['currencies'].str.contains(currency, case=False, na=False)
        ]
        
        # Also check title/content for currency mention
        currency_mentions = news_df[
            news_df['title'].str.contains(currency, case=False, na=False) |
            news_df['content'].str.contains(currency, case=False, na=False)
        ]
        
        # Combine and remove duplicates
        combined = pd.concat([relevant_news, currency_mentions]).drop_duplicates()
        
        return combined
    
    def analyze(self, symbol: str, data: Optional[pd.DataFrame] = None, **kwargs) -> Signal:
        """
        Analyze news sentiment and generate signal
        
        Args:
            symbol: Currency pair (e.g., 'EURUSD')
            data: Optional news DataFrame. If None, fetches from database
            
        Returns:
            Signal with BUY/SELL/HOLD recommendation based on sentiment
        """
        # Fetch data if not provided
        if data is None or data.empty:
            data = self.fetch_news_data(self.lookback_days)
        
        if data.empty:
            return Signal(
                timestamp=datetime.now(),
                symbol=symbol,
                direction='HOLD',
                confidence=0.0,
                agent_name=self.name,
                reasoning="No news data available for sentiment analysis",
                indicators={}
            )
        
        # Extract currencies from symbol
        base_currency = symbol[:3] if len(symbol) >= 6 else 'USD'
        quote_currency = symbol[3:6] if len(symbol) >= 6 else 'USD'
        
        # Filter news for both currencies
        base_news = self.filter_news_for_currency(data, base_currency)
        quote_news = self.filter_news_for_currency(data, quote_currency)
        
        # Calculate sentiment scores
        base_sentiments = []
        quote_sentiments = []
        
        for _, article in base_news.iterrows():
            title_sentiment = self.calculate_sentiment_score(article['title'])
            content_sentiment = self.calculate_sentiment_score(article.get('content', ''))
            # Weight title more heavily (3:1)
            article_sentiment = (title_sentiment * 3 + content_sentiment) / 4
            base_sentiments.append(article_sentiment)
        
        for _, article in quote_news.iterrows():
            title_sentiment = self.calculate_sentiment_score(article['title'])
            content_sentiment = self.calculate_sentiment_score(article.get('content', ''))
            article_sentiment = (title_sentiment * 3 + content_sentiment) / 4
            quote_sentiments.append(article_sentiment)
        
        # Aggregate sentiment
        base_avg_sentiment = np.mean(base_sentiments) if base_sentiments else 0.0
        quote_avg_sentiment = np.mean(quote_sentiments) if quote_sentiments else 0.0
        
        # Calculate relative sentiment (base vs quote)
        # Positive = base currency stronger than quote
        relative_sentiment = base_avg_sentiment - quote_avg_sentiment
        
        # Determine signal
        indicator_values = {
            'base_currency': base_currency,
            'quote_currency': quote_currency,
            'base_sentiment': float(base_avg_sentiment),
            'quote_sentiment': float(quote_avg_sentiment),
            'relative_sentiment': float(relative_sentiment),
            'base_article_count': len(base_news),
            'quote_article_count': len(quote_news),
            'total_articles': len(data)
        }
        
        # Calculate confidence based on article count and sentiment strength
        article_confidence = min((len(base_news) + len(quote_news)) / 10, 1.0)
        sentiment_strength = abs(relative_sentiment)
        confidence = (article_confidence * 0.4 + sentiment_strength * 0.6)
        
        if len(base_news) == 0 and len(quote_news) == 0:
            return Signal(
                timestamp=datetime.now(),
                symbol=symbol,
                direction='HOLD',
                confidence=0.1,
                agent_name=self.name,
                reasoning=f"No specific news found for {base_currency} or {quote_currency}",
                indicators=indicator_values
            )
        
        if relative_sentiment > 0.2:
            direction = 'BUY'
            reasoning = (f"News sentiment positive for {base_currency} "
                        f"(+{base_avg_sentiment:.2f}) vs {quote_currency} "
                        f"({quote_avg_sentiment:+.2f}). "
                        f"Based on {len(base_news)} {base_currency} and "
                        f"{len(quote_news)} {quote_currency} articles.")
        elif relative_sentiment < -0.2:
            direction = 'SELL'
            reasoning = (f"News sentiment negative for {base_currency} "
                        f"({base_avg_sentiment:+.2f}) vs {quote_currency} "
                        f"(+{quote_avg_sentiment:.2f}). "
                        f"Based on {len(base_news)} {base_currency} and "
                        f"{len(quote_news)} {quote_currency} articles.")
        else:
            direction = 'HOLD'
            confidence *= 0.7  # Reduce confidence for neutral signals
            reasoning = (f"News sentiment neutral for {symbol}. "
                        f"{base_currency}: {base_avg_sentiment:+.2f}, "
                        f"{quote_currency}: {quote_avg_sentiment:+.2f}.")
        
        signal = Signal(
            timestamp=datetime.now(),
            symbol=symbol,
            direction=direction,
            confidence=min(confidence, 1.0),
            agent_name=self.name,
            reasoning=reasoning,
            indicators=indicator_values
        )
        
        self.record_signal(signal)
        return signal
