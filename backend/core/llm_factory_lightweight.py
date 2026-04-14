"""
Lightweight LLM Factory for FX Alpha Platform
Uses only free, lightweight models without heavy dependencies
"""

import os
import json
import requests
import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class LightweightLLMFactory:
    """
    Lightweight LLM implementation using free APIs
    Avoids heavy PyTorch/Transformers dependencies
    """
    
    def __init__(self):
        self.huggingface_key = os.getenv('HUGGINGFACE_API_KEY')
        self.models = {
            'sentiment': 'nlptown/bert-base-multilingual-uncased-sentiment',
            'classification': 'distilbert-base-uncased-finetuned-sst-2-english',
            'explanation': 't5-small'
        }
    
    def analyze_sentiment(self, text: str) -> Dict:
        """
        Analyze sentiment using HuggingFace Inference API (free tier)
        Returns: {'label': 'POSITIVE'/'NEGATIVE'/'NEUTRAL', 'score': float}
        """
        try:
            if not self.huggingface_key:
                # Fallback to simple rule-based sentiment
                return self._rule_based_sentiment(text)
            
            # Try multiple models in order of preference
            models_to_try = [
                'nlptown/bert-base-multilingual-uncased-sentiment',
                'cardiffnlp/twitter-roberta-base-sentiment-latest',
                'distilbert-base-uncased-finetuned-sst-2-english'
            ]
            
            for model_name in models_to_try:
                try:
                    API_URL = f"https://api-inference.huggingface.co/models/{model_name}"
                    headers = {"Authorization": f"Bearer {self.huggingface_key}"}
                    
                    response = requests.post(API_URL, headers=headers, json={"inputs": text})
                    
                    if response.status_code == 200:
                        result = response.json()[0]
                        logger.info(f"Successfully used model: {model_name}")
                        return {
                            'label': result['label'],
                            'score': result['score'],
                            'source': 'huggingface',
                            'model': model_name
                        }
                    else:
                        logger.warning(f"Model {model_name} returned status: {response.status_code}")
                        continue
                        
                except Exception as e:
                    logger.warning(f"Model {model_name} failed: {e}")
                    continue
            
            # If all models fail, fallback to rule-based
            logger.warning("All HuggingFace models failed, using rule-based sentiment")
            return self._rule_based_sentiment(text)
                
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return self._rule_based_sentiment(text)
    
    def _rule_based_sentiment(self, text: str) -> Dict:
        """Fallback rule-based sentiment analysis"""
        positive_words = ['good', 'great', 'excellent', 'positive', 'bullish', 'rise', 'gain', 'profit', 'strong', 'growth']
        negative_words = ['bad', 'terrible', 'negative', 'bearish', 'fall', 'loss', 'weak', 'decline', 'risk', 'concern']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return {'label': 'POSITIVE', 'score': min(0.8, 0.5 + positive_count * 0.1), 'source': 'rule_based'}
        elif negative_count > positive_count:
            return {'label': 'NEGATIVE', 'score': min(0.8, 0.5 + negative_count * 0.1), 'source': 'rule_based'}
        else:
            return {'label': 'NEUTRAL', 'score': 0.5, 'source': 'rule_based'}
    
    def classify_text(self, text: str, labels: List[str] = None) -> Dict:
        """
        Classify text into categories
        Uses simple keyword matching for free implementation
        """
        if labels is None:
            labels = ['BUY', 'SELL', 'NEUTRAL']
        
        text_lower = text.lower()
        scores = {}
        
        # Simple keyword-based classification
        buy_keywords = ['buy', 'bullish', 'rise', 'gain', 'upward', 'positive', 'strong', 'growth', 'opportunity']
        sell_keywords = ['sell', 'bearish', 'fall', 'loss', 'downward', 'negative', 'weak', 'decline', 'risk']
        neutral_keywords = ['hold', 'neutral', 'stable', 'sideways', 'range', 'wait', 'monitor']
        
        for label in labels:
            if label.upper() == 'BUY':
                score = sum(1 for word in buy_keywords if word in text_lower)
            elif label.upper() == 'SELL':
                score = sum(1 for word in sell_keywords if word in text_lower)
            else:  # NEUTRAL
                score = sum(1 for word in neutral_keywords if word in text_lower)
            
            scores[label] = score / len(text_lower.split())  # Normalize by text length
        
        # Get the best label
        best_label = max(scores, key=scores.get)
        confidence = min(0.9, scores[best_label] * 10)  # Scale confidence
        
        return {
            'label': best_label,
            'confidence': confidence,
            'scores': scores,
            'source': 'keyword_based'
        }
    
    def generate_explanation(self, signal_data: Dict) -> str:
        """
        Generate human-readable explanation for trading signal
        Uses template-based approach for free implementation
        """
        try:
            signal = signal_data.get('signal', 'NEUTRAL')
            confidence = signal_data.get('confidence', 0.5)
            agent_signals = signal_data.get('agent_signals', {})
            
            explanation_parts = []
            
            # Main signal statement
            signal_map = {1: 'BUY', -1: 'SELL', 0: 'NEUTRAL'}
            signal_str = signal_map.get(signal, 'NEUTRAL')
            
            if signal_str == 'BUY':
                explanation_parts.append(f"The system generates a {signal_str} signal with {confidence:.0%} confidence.")
            elif signal_str == 'SELL':
                explanation_parts.append(f"The system generates a {signal_str} signal with {confidence:.0%} confidence.")
            else:
                explanation_parts.append(f"The system remains {signal_str} due to mixed signals.")
            
            # Agent contributions
            if agent_signals:
                agent_explanations = []
                for agent, data in agent_signals.items():
                    agent_signal = signal_map.get(data.get('signal', 0), 'NEUTRAL')
                    agent_conf = data.get('confidence', 0.5)
                    
                    if 'technical' in agent.lower():
                        if agent_signal == 'BUY':
                            agent_explanations.append(f"Technical indicators show bullish momentum")
                        elif agent_signal == 'SELL':
                            agent_explanations.append(f"Technical indicators suggest bearish pressure")
                        else:
                            agent_explanations.append(f"Technical indicators are mixed")
                    
                    elif 'macro' in agent.lower():
                        if agent_signal == 'BUY':
                            agent_explanations.append(f"Macroeconomic factors support the currency")
                        elif agent_signal == 'SELL':
                            agent_explanations.append(f"Macroeconomic data weighs on the currency")
                        else:
                            agent_explanations.append(f"Macroeconomic indicators are neutral")
                    
                    elif 'sentiment' in agent.lower():
                        if agent_signal == 'BUY':
                            agent_explanations.append(f"Market sentiment is positive")
                        elif agent_signal == 'SELL':
                            agent_explanations.append(f"Market sentiment is negative")
                        else:
                            agent_explanations.append(f"Market sentiment is balanced")
                
                if agent_explanations:
                    explanation_parts.append("Agent analysis: " + "; ".join(agent_explanations) + ".")
            
            # Risk disclaimer
            if confidence < 0.7:
                explanation_parts.append("Note: Confidence is moderate, consider additional confirmation before trading.")
            
            return " ".join(explanation_parts)
            
        except Exception as e:
            logger.error(f"Explanation generation error: {e}")
            return f"Generated {signal} signal based on multi-agent analysis with {confidence:.0%} confidence."
    
    def extract_currencies(self, text: str) -> List[str]:
        """Extract currency pairs from text"""
        currency_pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD']
        currencies = ['EUR', 'GBP', 'USD', 'JPY', 'CHF', 'AUD', 'CAD']
        
        found_pairs = []
        text_upper = text.upper()
        
        # Direct pair matching
        for pair in currency_pairs:
            if pair in text_upper:
                found_pairs.append(pair)
        
        # Individual currency matching
        found_currencies = []
        for currency in currencies:
            if currency in text_upper:
                found_currencies.append(currency)
        
        # Combine USD with other currencies to form pairs
        if 'USD' in found_currencies:
            for currency in currencies:
                if currency != 'USD' and currency in found_currencies:
                    pair = f"{currency}USD" if currency in ['EUR', 'GBP', 'AUD'] else f"USD{currency}"
                    if pair not in found_pairs:
                        found_pairs.append(pair)
        
        return list(set(found_pairs))


# Global lightweight LLM instance
lightweight_llm = LightweightLLMFactory()


def get_lightweight_llm():
    """Get the lightweight LLM instance"""
    return lightweight_llm


# Compatibility functions for existing code
def get_llm_model(model_name: str = 'sentiment'):
    """Get LLM model (lightweight version)"""
    return lightweight_llm


def analyze_sentiment(text: str):
    """Analyze sentiment (lightweight version)"""
    return lightweight_llm.analyze_sentiment(text)


def generate_explanation(signal_data: Dict):
    """Generate explanation (lightweight version)"""
    return lightweight_llm.generate_explanation(signal_data)
