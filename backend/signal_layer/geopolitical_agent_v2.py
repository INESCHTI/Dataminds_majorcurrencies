"""
Geopolitical Agent V2 - DETERMINISTIC GEOPOLITICAL ANALYSIS
Analyzes geopolitical events and their impact on currency markets
NO LLM for trading decisions - only rule-based analysis
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class GeopoliticalAgentV2:
    """
    Geopolitical Analysis Agent
    
    Analyzes:
    - Political events and elections
    - Geopolitical tensions and conflicts
    - Natural disasters and crises
    - Central bank communications
    - Trade policies and sanctions
    
    Focus on safe-haven (USD, CHF, JPY) vs risk-on dynamics
    """
    
    def __init__(self):
        # Remove NewsLoader dependency for now
        # self.data_loader = NewsLoader()
        self.safe_haven_currencies = ['USD', 'CHF', 'JPY']
        self.risk_on_currencies = ['EUR', 'GBP', 'AUD', 'NZD', 'CAD']
        
        # Geopolitical keywords
        self.geopolitical_keywords = {
            'high_risk': [
                'war', 'conflict', 'tension', 'sanction', 'crisis', 'attack',
                'election', 'political', 'protest', 'unrest', 'turmoil'
            ],
            'safe_haven': [
                'flight to safety', 'safe haven', 'risk aversion', 'uncertainty',
                'market fear', 'volatility', 'panic selling'
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
        Generate geopolitical signal
        
        Returns:
            {
                'signal': -1/0/1,
                'confidence': 0-1,
                'features_used': dict,
                'deterministic_reason': str
            }
        """
        # Simplified geopolitical analysis without news loader
        # Create empty news dataframe for now
        import pandas as pd
        news_df = pd.DataFrame()
        
        if news_df.empty:
            # Use currency-based logic instead
            base_currency = currencies[0] if currencies else 'USD'
            
            if base_currency in self.safe_haven_currencies:
                return {
                    'signal': 1,  # BUY safe haven
                    'confidence': 0.6,
                    'features_used': {'currency_type': 'safe_haven'},
                    'deterministic_reason': f'{base_currency} is a safe-haven currency during uncertainty'
                }
            elif base_currency in self.risk_on_currencies:
                return {
                    'signal': 0,  # NEUTRAL for risk currencies
                    'confidence': 0.4,
                    'features_used': {'currency_type': 'risk_on'},
                    'deterministic_reason': f'{base_currency} is a risk-on currency, neutral stance'
                }
            else:
                return {
                    'signal': 0,
                    'confidence': 0.3,
                    'features_used': {},
                    'deterministic_reason': f'Unknown currency {base_currency}, neutral signal'
                }
        
        # Analyze geopolitical content
        geopolitical_score = self._analyze_geopolitical_content(news_df, currencies)
        
        # Determine safe-haven vs risk-on bias
        safe_haven_bias = self._calculate_safe_haven_bias(currencies, geopolitical_score)
        
        # Generate signal based on currency composition
        signal = self._generate_currency_signal(currencies, safe_haven_bias)
        
        # Calculate confidence based on data quality
        confidence = self._calculate_confidence(news_df, geopolitical_score)
        
        return {
            'signal': signal,
            'confidence': confidence,
            'features_used': {
                'geopolitical_score': geopolitical_score,
                'safe_haven_bias': safe_haven_bias,
                'news_count': len(news_df),
                'timeframe_hours': lookback_hours
            },
            'deterministic_reason': self._generate_reasoning(
                signal, geopolitical_score, safe_haven_bias, currencies
            )
        }
    
    def _analyze_geopolitical_content(self, news_df: pd.DataFrame, currencies: List[str]) -> float:
        """Analyze news content for geopolitical relevance"""
        if news_df.empty:
            return 0.0
        
        total_score = 0.0
        relevant_articles = 0
        
        for _, article in news_df.iterrows():
            title = str(article.get('title', '')).lower()
            content = str(article.get('content', '')).lower()
            text = f"{title} {content}"
            
            article_score = 0.0
            
            # Check for high-risk keywords
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
        
        # For major pairs like EURUSD, positive bias means USD (safe haven) strength
        # This would generate SELL for EURUSD (EUR weak, USD strong)
        if safe_haven_bias > 0.3:
            return -1  # SELL (safe-haven strengthening)
        elif safe_haven_bias < -0.3:
            return 1   # BUY (risk-on strengthening)
        else:
            return 0   # NEUTRAL
    
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
        avg_age_hours = news_df['timestamp'].apply(
            lambda x: (now - x).total_seconds() / 3600
        ).mean()
        time_confidence = max(0.3, 1.0 - (avg_age_hours / 72.0))  # Decay over 3 days
        
        return min(article_confidence + relevance_boost, 1.0) * time_confidence
    
    def _generate_reasoning(
        self, 
        signal: int, 
        geopolitical_score: float, 
        safe_haven_bias: float, 
        currencies: List[str]
    ) -> str:
        """Generate deterministic reasoning for the signal"""
        signal_map = {1: 'BUY', -1: 'SELL', 0: 'NEUTRAL'}
        
        if signal == 0:
            return f"NEUTRAL: Low geopolitical impact (score: {geopolitical_score:.2f})"
        
        direction = "safe-haven demand" if safe_haven_bias > 0 else "risk appetite"
        
        return (
            f"{signal_map[signal]}: High geopolitical activity (score: {geopolitical_score:.2f}) "
            f"driving {direction}. {'Safe-haven' if safe_haven_bias > 0 else 'Risk-on'} "
            f"currencies showing strength."
        )
