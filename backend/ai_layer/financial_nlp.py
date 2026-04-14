"""
Financial NLP with Fine-tuned Models
Uses FinBERT and domain-specific financial sentiment analysis
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
    TRANSFORMERS_AVAILABLE = True
except (ImportError, OSError) as e:
    TRANSFORMERS_AVAILABLE = False
    logging.warning(f"Transformers not available for financial NLP: {e}")

logger = logging.getLogger(__name__)


@dataclass
class SentimentResult:
    text: str
    sentiment: str  # bullish, bearish, neutral
    confidence: float
    scores: Dict[str, float]
    entities: List[str]
    aspects: List[str]


class FinBERTAnalyzer:
    """
    Financial sentiment analysis using FinBERT
    FinBERT is pre-trained on financial corpus and fine-tuned for sentiment
    """
    
    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.sentiment_pipeline = None
        self._load_model()
        
        # Financial keywords for entity extraction
        self.currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'CAD', 'NZD', 'CNY']
        self.central_banks = ['Fed', 'ECB', 'BoE', 'BoJ', 'SNB', 'RBA', 'RBNZ', 'PBoC']
        self.indicators = ['GDP', 'CPI', 'PPI', 'NFP', 'PMI', 'unemployment', 'inflation', 'rates']
    
    def _load_model(self):
        """Load FinBERT model"""
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("Transformers library not available")
            return
        
        try:
            # Use FinBERT model (pre-trained on financial text)
            model_name = "yiyanghkust/finbert-tone"  # Fine-tuned for financial tone
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer,
                max_length=512,
                truncation=True
            )
            
            logger.info("✅ FinBERT model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading FinBERT: {e}")
            # Fallback to general sentiment
            self._load_fallback_model()
    
    def _load_fallback_model(self):
        """Load fallback sentiment model"""
        try:
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                max_length=512,
                truncation=True
            )
            logger.info("✅ Fallback sentiment model loaded")
        except Exception as e:
            logger.error(f"Error loading fallback model: {e}")
    
    def analyze_sentiment(self, text: str) -> SentimentResult:
        """
        Analyze financial sentiment of text
        
        Returns:
            SentimentResult with sentiment label, confidence, and extracted entities
        """
        if not self.sentiment_pipeline:
            return SentimentResult(
                text=text,
                sentiment='neutral',
                confidence=0.5,
                scores={},
                entities=[],
                aspects=[]
            )
        
        try:
            # Truncate text if too long
            text = text[:1000]  # Keep first 1000 chars
            
            # Get sentiment from pipeline
            result = self.sentiment_pipeline(text)[0]
            
            # Map to financial sentiment
            label = result['label'].lower()
            confidence = result['score']
            
            # Convert to financial terms
            if 'positive' in label or 'bullish' in label:
                sentiment = 'bullish'
            elif 'negative' in label or 'bearish' in label:
                sentiment = 'bearish'
            else:
                sentiment = 'neutral'
            
            # Extract entities
            entities = self._extract_entities(text)
            aspects = self._extract_aspects(text)
            
            # Calculate aspect-based sentiment scores
            scores = self._calculate_sentiment_scores(text, entities)
            
            return SentimentResult(
                text=text[:200] + "..." if len(text) > 200 else text,
                sentiment=sentiment,
                confidence=confidence,
                scores=scores,
                entities=entities,
                aspects=aspects
            )
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return SentimentResult(
                text=text[:100],
                sentiment='neutral',
                confidence=0.0,
                scores={},
                entities=[],
                aspects=[]
            )
    
    def analyze_batch(self, texts: List[str]) -> List[SentimentResult]:
        """Analyze sentiment for batch of texts"""
        if not self.sentiment_pipeline:
            return [self.analyze_sentiment(t) for t in texts]
        
        try:
            # Truncate texts
            truncated_texts = [t[:1000] for t in texts]
            
            # Batch prediction
            results = self.sentiment_pipeline(truncated_texts)
            
            sentiment_results = []
            for text, result in zip(texts, results):
                label = result['label'].lower()
                confidence = result['score']
                
                if 'positive' in label or 'bullish' in label:
                    sentiment = 'bullish'
                elif 'negative' in label or 'bearish' in label:
                    sentiment = 'bearish'
                else:
                    sentiment = 'neutral'
                
                entities = self._extract_entities(text)
                aspects = self._extract_aspects(text)
                scores = self._calculate_sentiment_scores(text, entities)
                
                sentiment_results.append(SentimentResult(
                    text=text[:200] + "..." if len(text) > 200 else text,
                    sentiment=sentiment,
                    confidence=confidence,
                    scores=scores,
                    entities=entities,
                    aspects=aspects
                ))
            
            return sentiment_results
            
        except Exception as e:
            logger.error(f"Error in batch sentiment analysis: {e}")
            return [self.analyze_sentiment(t) for t in texts]
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract financial entities from text"""
        entities = []
        text_upper = text.upper()
        
        # Extract currency pairs
        for curr in self.currencies:
            if curr in text_upper:
                entities.append(curr)
        
        # Extract central banks
        for bank in self.central_banks:
            if bank in text:
                entities.append(bank)
        
        # Extract indicators
        for indicator in self.indicators:
            if indicator.upper() in text_upper:
                entities.append(indicator)
        
        return list(set(entities))
    
    def _extract_aspects(self, text: str) -> List[str]:
        """Extract financial aspects/topics from text"""
        aspects = []
        text_lower = text.lower()
        
        aspect_keywords = {
            'monetary_policy': ['rate', 'interest', 'policy', 'hawkish', 'dovish'],
            'economic_growth': ['gdp', 'growth', 'expansion', 'recession'],
            'inflation': ['inflation', 'cpi', 'ppi', 'deflation'],
            'employment': ['employment', 'unemployment', 'nfp', 'jobs'],
            'trade': ['trade', 'tariff', 'export', 'import', 'trade war'],
            'geopolitics': ['election', 'war', 'conflict', 'sanction', 'brexit']
        }
        
        for aspect, keywords in aspect_keywords.items():
            if any(kw in text_lower for kw in keywords):
                aspects.append(aspect)
        
        return aspects
    
    def _calculate_sentiment_scores(self, text: str, entities: List[str]) -> Dict[str, float]:
        """Calculate sentiment scores for different aspects"""
        scores = {
            'overall': 0.0,
            'monetary_policy': 0.0,
            'economic': 0.0,
            'market': 0.0
        }
        
        text_lower = text.lower()
        
        # Overall sentiment based on keywords
        bullish_keywords = ['rise', 'gain', 'growth', 'strong', 'bullish', 'rally', 'surge']
        bearish_keywords = ['fall', 'drop', 'decline', 'weak', 'bearish', 'crash', 'plunge']
        
        bullish_count = sum(1 for kw in bullish_keywords if kw in text_lower)
        bearish_count = sum(1 for kw in bearish_keywords if kw in text_lower)
        
        if bullish_count > bearish_count:
            scores['overall'] = min(1.0, 0.5 + (bullish_count - bearish_count) * 0.1)
        elif bearish_count > bullish_count:
            scores['overall'] = max(-1.0, -0.5 - (bearish_count - bullish_count) * 0.1)
        else:
            scores['overall'] = 0.0
        
        return scores


class FinancialNewsAnalyzer:
    """
    Specialized analyzer for financial news articles
    Combines sentiment analysis with relevance scoring
    """
    
    def __init__(self):
        self.finbert = FinBERTAnalyzer()
        
        # Relevance weights for different news categories
        self.category_weights = {
            'breaking': 1.0,
            'central_bank': 0.9,
            'economic_data': 0.85,
            'market_analysis': 0.7,
            'company_news': 0.5,
            'general': 0.3
        }
    
    def analyze_article(self, title: str, content: str, 
                       source: str = "unknown") -> Dict:
        """
        Analyze a financial news article
        
        Returns:
            Comprehensive analysis with sentiment, relevance, and impact score
        """
        # Combine title and content
        full_text = f"{title}. {content}"
        
        # Analyze sentiment
        sentiment_result = self.finbert.analyze_sentiment(full_text)
        
        # Calculate relevance
        relevance = self._calculate_relevance(full_text, source)
        
        # Calculate impact score (sentiment * relevance)
        impact_score = sentiment_result.confidence * relevance
        if sentiment_result.sentiment == 'bearish':
            impact_score *= -1
        
        # Determine news category
        category = self._categorize_news(full_text)
        
        return {
            'title': title[:200],
            'sentiment': sentiment_result.sentiment,
            'sentiment_confidence': sentiment_result.confidence,
            'relevance': relevance,
            'impact_score': impact_score,
            'category': category,
            'entities': sentiment_result.entities,
            'aspects': sentiment_result.aspects,
            'source': source,
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_relevance(self, text: str, source: str) -> float:
        """Calculate relevance score based on content and source"""
        relevance = 0.5  # Base relevance
        text_lower = text.lower()
        
        # Check for high-impact keywords
        high_impact = ['breaking', 'urgent', 'alert', 'fed', 'ecb', 'rate decision', 'nfp']
        for kw in high_impact:
            if kw in text_lower:
                relevance += 0.1
        
        # Source reputation adjustment
        reputable_sources = ['reuters', 'bloomberg', 'ft.com', 'wsj', 'cnbc', 'forexlive']
        if any(s in source.lower() for s in reputable_sources):
            relevance += 0.2
        
        return min(1.0, relevance)
    
    def _categorize_news(self, text: str) -> str:
        """Categorize news into financial categories"""
        text_lower = text.lower()
        
        if any(kw in text_lower for kw in ['breaking', 'urgent', 'flash']):
            return 'breaking'
        elif any(kw in text_lower for kw in ['fed', 'ecb', 'boe', 'boj', 'central bank', 'rate']):
            return 'central_bank'
        elif any(kw in text_lower for kw in ['gdp', 'cpi', 'nfp', 'employment', 'inflation']):
            return 'economic_data'
        elif any(kw in text_lower for kw in ['technical analysis', 'chart', 'support', 'resistance']):
            return 'market_analysis'
        else:
            return 'general'


# Factory functions
def create_finbert_analyzer() -> FinBERTAnalyzer:
    """Create FinBERT analyzer"""
    return FinBERTAnalyzer()


def create_news_analyzer() -> FinancialNewsAnalyzer:
    """Create financial news analyzer"""
    return FinancialNewsAnalyzer()
