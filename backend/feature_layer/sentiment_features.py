"""
Sentiment Feature Engine - Lightweight Version
Uses free APIs and rule-based analysis
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Import lightweight LLM
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.llm_factory_lightweight import get_lightweight_llm


class SentimentFeatureEngine:
    """
    Sentiment analysis using lightweight methods
    Avoids heavy PyTorch/Transformers dependencies
    """
    
    def __init__(self):
        self.llm = get_lightweight_llm()
        self.currencies = ['EUR', 'GBP', 'USD', 'JPY', 'CHF', 'AUD', 'CAD']
        
        # Sentiment weights for different sources
        self.source_weights = {
            'reuters': 0.9,
            'bloomberg': 0.9,
            'forexfactory': 0.8,
            'dailyfx': 0.8,
            'investing': 0.7,
            'sample': 0.6,
            'rule_based': 0.5
        }
    
    def calculate_sentiment_batch(self, news_df: pd.DataFrame, currencies: List[str]) -> pd.DataFrame:
        """
        Calculate sentiment for a batch of news articles
        """
        if news_df.empty:
            return pd.DataFrame()
        
        results = []
        
        for _, article in news_df.iterrows():
            title = str(article.get('title', ''))
            content = str(article.get('content', ''))
            source = str(article.get('source', 'unknown')).lower()
            
            # Combine title and content for analysis
            full_text = f"{title} {content}"
            
            # Analyze sentiment
            sentiment_result = self.llm.analyze_sentiment(full_text)
            
            # Extract currency relevance
            mentioned_currencies = self.llm.extract_currencies(full_text)
            
            # Calculate sentiment score (-1 to 1)
            sentiment_label = sentiment_result.get('label', 'NEUTRAL')
            sentiment_score = sentiment_result.get('score', 0.5)
            
            if sentiment_label == 'POSITIVE':
                normalized_score = sentiment_score
            elif sentiment_label == 'NEGATIVE':
                normalized_score = -sentiment_score
            else:
                normalized_score = 0.0
            
            # Apply source weight
            source_weight = self.source_weights.get(source, 0.5)
            weighted_score = normalized_score * source_weight
            
            results.append({
                'title': title,
                'source': source,
                'sentiment_label': sentiment_label,
                'sentiment_score': sentiment_score,
                'normalized_score': normalized_score,
                'weighted_score': weighted_score,
                'mentioned_currencies': mentioned_currencies,
                'timestamp': article.get('timestamp', datetime.now())
            })
        
        return pd.DataFrame(results)
    
    def aggregate_sentiment(self, sentiment_df: pd.DataFrame) -> Dict:
        """
        Aggregate sentiment scores into final signal
        """
        if sentiment_df.empty:
            return {
                'signal': 0,
                'confidence': 0.0,
                'features_used': {},
                'deterministic_reason': 'No sentiment data available',
                'agent': 'SentimentV2'
            }
        
        # Filter for recent articles (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        recent_df = sentiment_df[sentiment_df['timestamp'] > cutoff_time]
        
        if recent_df.empty:
            recent_df = sentiment_df  # Use all data if no recent data
        
        # Calculate overall sentiment
        avg_weighted_score = recent_df['weighted_score'].mean()
        total_articles = len(recent_df)
        
        # Calculate confidence based on article count and consensus
        article_confidence = min(1.0, total_articles / 10.0)  # More articles = higher confidence
        
        # Check for consensus (articles with similar sentiment)
        positive_count = len(recent_df[recent_df['normalized_score'] > 0.1])
        negative_count = len(recent_df[recent_df['normalized_score'] < -0.1])
        neutral_count = total_articles - positive_count - negative_count
        
        if positive_count > negative_count * 1.5:
            consensus_strength = positive_count / total_articles
        elif negative_count > positive_count * 1.5:
            consensus_strength = negative_count / total_articles
        else:
            consensus_strength = 0.5  # No clear consensus
        
        # Final confidence
        final_confidence = article_confidence * consensus_strength
        
        # Generate signal
        if avg_weighted_score > 0.2 and final_confidence > 0.3:
            signal = 1  # BUY
            reason = f"Positive sentiment detected: {positive_count} positive vs {negative_count} negative articles"
        elif avg_weighted_score < -0.2 and final_confidence > 0.3:
            signal = -1  # SELL
            reason = f"Negative sentiment detected: {negative_count} negative vs {positive_count} positive articles"
        else:
            signal = 0  # NEUTRAL
            reason = f"Mixed or neutral sentiment: {neutral_count} neutral articles"
        
        return {
            'signal': signal,
            'confidence': final_confidence,
            'features_used': {
                'total_articles': total_articles,
                'avg_sentiment_score': avg_weighted_score,
                'positive_articles': positive_count,
                'negative_articles': negative_count,
                'neutral_articles': neutral_count,
                'consensus_strength': consensus_strength
            },
            'deterministic_reason': reason,
            'agent': 'SentimentV2'
        }
    
    @staticmethod
    def _generate_reason(signal: int, avg_sent: float, count: int) -> str:
        """Generate deterministic explanation"""
        if signal == 1:
            return f"Bullish sentiment: {avg_sent:.2f} from {count} articles"
        elif signal == -1:
            return f"Bearish sentiment: {avg_sent:.2f} from {count} articles"
        else:
            return f"Neutral sentiment: {avg_sent:.2f} from {count} articles"
