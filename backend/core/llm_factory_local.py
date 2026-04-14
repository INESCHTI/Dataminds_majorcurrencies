"""
Local LLM Factory - Models Running Locally
No external API dependencies, fully offline operation
"""
import os
import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Try to import transformers for local models
try:
    # Disable transformers to avoid DLL issues
    LOCAL_MODELS_AVAILABLE = False
    print("⚠️ Transformers disabled for stability, using enhanced rule-based")
except ImportError:
    print("⚠️ Using enhanced rule-based sentiment only")
    LOCAL_MODELS_AVAILABLE = False


class LocalLLMFactory:
    """
    Local LLM implementation using downloaded models
    Fully offline, no rate limiting, stable operation
    """
    
    def __init__(self):
        self.device = "cpu"  # Force CPU for stability
        self.sentiment_pipeline = None
        self.classification_pipeline = None
        
        # Use enhanced rule-based only for stability
        logger.info("🚀 Using enhanced rule-based sentiment analysis (stable & fast)")
    
    def _initialize_local_models(self):
        """Initialize local sentiment and classification models"""
        try:
            # Lightweight sentiment model - fast and small
            model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
            
            logger.info(f"Loading local model: {model_name}")
            
            # Load tokenizer and model
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSequenceClassification.from_pretrained(model_name)
            
            # Create pipeline
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=model,
                tokenizer=tokenizer,
                device=0 if self.device == "cuda" else -1,
                return_all_scores=True
            )
            
            logger.info(f"✅ Local sentiment model loaded on {self.device}")
            
        except Exception as e:
            logger.warning(f"Failed to load local models: {e}")
            self.sentiment_pipeline = None
    
    def analyze_sentiment(self, text: str) -> Dict:
        """
        Analyze sentiment using enhanced rule-based analysis
        Returns: {'label': 'POSITIVE'/'NEGATIVE'/'NEUTRAL', 'score': float}
        """
        # Always use enhanced rule-based for stability
        return self._enhanced_rule_based_sentiment(text)
    
    def _enhanced_rule_based_sentiment(self, text: str) -> Dict:
        """Enhanced rule-based sentiment with financial keywords"""
        
        # Financial sentiment keywords
        positive_words = [
            'good', 'great', 'excellent', 'positive', 'bullish', 'rise', 'gain', 
            'profit', 'strong', 'growth', 'rally', 'surge', 'jump', 'boost',
            'recovery', 'optimistic', 'confidence', 'upbeat', 'encouraging',
            'beat', 'exceed', 'outperform', 'breakthrough', 'milestone'
        ]
        
        negative_words = [
            'bad', 'terrible', 'negative', 'bearish', 'fall', 'loss', 'weak', 
            'decline', 'risk', 'concern', 'slump', 'plunge', 'drop', 'crash',
            'recession', 'inflation', 'crisis', 'uncertainty', 'volatility',
            'disappoint', 'miss', 'underperform', 'warning', 'threat'
        ]
        
        # Financial context modifiers
        intensifiers = ['very', 'extremely', 'significantly', 'dramatically', 'sharply']
        diminishers = ['slightly', 'modestly', 'marginally', 'somewhat']
        
        text_lower = text.lower()
        
        # Count sentiment words
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        # Apply modifiers
        modifier = 1.0
        for intensifier in intensifiers:
            if intensifier in text_lower:
                modifier += 0.2
        for diminisher in diminishers:
            if diminisher in text_lower:
                modifier -= 0.1
        
        # Calculate sentiment
        total_words = positive_count + negative_count
        if total_words == 0:
            return {'label': 'NEUTRAL', 'score': 0.5, 'source': 'rule_based'}
        
        sentiment_ratio = (positive_count - negative_count) / total_words
        adjusted_score = (sentiment_ratio + 1) / 2 * modifier  # Normalize to [0,1]
        adjusted_score = max(0, min(1, adjusted_score))  # Clamp to [0,1]
        
        # Determine label
        if adjusted_score > 0.6:
            label = 'POSITIVE'
        elif adjusted_score < 0.4:
            label = 'NEGATIVE'
        else:
            label = 'NEUTRAL'
        
        return {
            'label': label, 
            'score': adjusted_score, 
            'source': 'enhanced_rule_based'
        }
    
    def classify_text(self, text: str, labels: List[str] = None) -> Dict:
        """
        Classify text into categories using rule-based approach
        Enhanced for financial text classification
        """
        if labels is None:
            labels = ['bullish', 'bearish', 'neutral', 'volatile', 'uncertain']
        
        text_lower = text.lower()
        
        # Classification rules
        rules = {
            'bullish': ['bullish', 'rise', 'gain', 'growth', 'rally', 'surge', 'up', 'increase', 'positive'],
            'bearish': ['bearish', 'fall', 'loss', 'decline', 'drop', 'down', 'decrease', 'negative'],
            'volatile': ['volatile', 'volatility', 'swing', 'fluctuate', 'unstable', 'erratic'],
            'uncertain': ['uncertain', 'unclear', 'unknown', 'mixed', 'conflicting', 'wait']
        }
        
        scores = {}
        for label in labels:
            if label in rules:
                matches = sum(1 for keyword in rules[label] if keyword in text_lower)
                scores[label] = matches / len(rules[label])
            else:
                scores[label] = 0.0
        
        # Find best match
        best_label = max(scores, key=scores.get)
        confidence = scores[best_label]
        
        return {
            'label': best_label,
            'confidence': confidence,
            'all_scores': scores,
            'source': 'rule_based_classification'
        }
    
    def extract_currencies(self, text: str) -> List[str]:
        """
        Extract currency codes from text
        Returns list of detected currency codes
        """
        # Common forex currency codes
        currencies = [
            'USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD',
            'SEK', 'NOK', 'DKK', 'PLN', 'CZK', 'HUF', 'RON'
        ]
        
        found_currencies = []
        text_upper = text.upper()
        
        for currency in currencies:
            if currency in text_upper:
                found_currencies.append(currency)
        
        return list(set(found_currencies))  # Remove duplicates
    
    def get_model_info(self) -> Dict:
        """Get information about loaded models"""
        return {
            'local_models_available': False,  # Disabled for stability
            'device': 'cpu',
            'sentiment_model_loaded': False,
            'classification_model_loaded': False,
            'models': {
                'sentiment': 'enhanced_rule_based',
                'classification': 'rule_based'
            },
            'stability': 'high',
            'approach': 'rule_based_fallback'
        }


# Global instance
_local_llm_factory = None

def get_local_llm_factory() -> LocalLLMFactory:
    """Get singleton LocalLLMFactory instance"""
    global _local_llm_factory
    if _local_llm_factory is None:
        _local_llm_factory = LocalLLMFactory()
    return _local_llm_factory
