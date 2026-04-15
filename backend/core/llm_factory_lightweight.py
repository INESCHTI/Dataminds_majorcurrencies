"""
Lightweight LLM Factory for FX Alpha Platform
Uses TokenFactory (Llama-3.1-70B) for high-quality LLM outputs
Falls back to lightweight models for basic tasks
"""

import os
import json
import requests
import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class TokenFactoryClient:
    """
    Client for TokenFactory API (Esprit LLM Platform)
    Uses Llama-3.1-70B-Instruct for high-quality generation
    """
    
    def __init__(self):
        self.api_key = os.getenv('TOKENFACTORY_API_KEY')
        self.base_url = os.getenv('TOKENFACTORY_BASE_URL', 'https://tokenfactory.esprit.tn/api')
        self.model = 'hosted_vllm/Llama-3.1-70B-Instruct'
        self.enabled = bool(self.api_key)
        
        if not self.enabled:
            logger.warning("TokenFactory API key not configured. Set TOKENFACTORY_API_KEY environment variable.")
    
    def chat_completion(self, messages: List[Dict], temperature: float = 0.7, max_tokens: int = 500) -> Optional[str]:
        """
        Generate chat completion using TokenFactory API
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text or None if failed
        """
        if not self.enabled:
            logger.debug("TokenFactory not enabled, skipping API call")
            return None
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': self.model,
                'messages': messages,
                'temperature': temperature,
                'max_tokens': max_tokens,
                'top_p': 0.9,
                'frequency_penalty': 0.0,
                'presence_penalty': 0.0
            }
            
            response = requests.post(
                f'{self.base_url}/chat/completions',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content']
                    logger.info(f"TokenFactory API call successful ({len(content)} chars)")
                    return content
                else:
                    logger.warning("TokenFactory response missing choices")
                    return None
            else:
                logger.warning(f"TokenFactory API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("TokenFactory API timeout")
            return None
        except Exception as e:
            logger.error(f"TokenFactory API error: {e}")
            return None
    
    def generate_text(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Optional[str]:
        """
        Simple text generation wrapper
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters (temperature, max_tokens)
            
        Returns:
            Generated text or None
        """
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})
        
        return self.chat_completion(
            messages=messages,
            temperature=kwargs.get('temperature', 0.7),
            max_tokens=kwargs.get('max_tokens', 500)
        )


class LightweightLLMFactory:
    """
    Lightweight LLM implementation with TokenFactory integration
    Uses Llama-3.1-70B for high-quality explanations
    Falls back to lightweight models for basic tasks
    """
    
    def __init__(self):
        self.huggingface_key = os.getenv('HUGGINGFACE_API_KEY')
        self.models = {
            'sentiment': 'nlptown/bert-base-multilingual-uncased-sentiment',
            'classification': 'distilbert-base-uncased-finetuned-sst-2-english',
            'explanation': 't5-small'
        }
        # Initialize TokenFactory client for high-quality generation
        self.tokenfactory = TokenFactoryClient()
        self.use_llama_for_explanations = self.tokenfactory.enabled
    
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
        Uses Llama-3.1-70B via TokenFactory when available, falls back to template-based
        """
        try:
            signal = signal_data.get('signal', 'NEUTRAL')
            confidence = signal_data.get('confidence', 0.5)
            agent_signals = signal_data.get('agent_signals', {})
            pair = signal_data.get('pair', 'EURUSD')
            
            signal_map = {1: 'BUY', -1: 'SELL', 0: 'NEUTRAL'}
            signal_str = signal_map.get(signal, 'NEUTRAL')
            
            # Try TokenFactory/Llama-3.1 for high-quality explanation
            if self.use_llama_for_explanations:
                llm_explanation = self._generate_llm_explanation(
                    pair=pair,
                    signal=signal_str,
                    confidence=confidence,
                    agent_signals=agent_signals
                )
                if llm_explanation:
                    return llm_explanation
            
            # Fallback to template-based explanation
            return self._generate_template_explanation(signal_str, confidence, agent_signals)
            
        except Exception as e:
            logger.error(f"Explanation generation error: {e}")
            return f"Generated {signal_str} signal for {pair} with {confidence:.0%} confidence."
    
    def _generate_llm_explanation(self, pair: str, signal: str, confidence: float, agent_signals: Dict) -> Optional[str]:
        """
        Generate explanation using Llama-3.1-70B via TokenFactory
        """
        try:
            # Build agent context
            agent_context = []
            for agent_name, data in agent_signals.items():
                agent_signal = {1: 'BUY', -1: 'SELL', 0: 'NEUTRAL'}.get(data.get('signal', 0), 'NEUTRAL')
                agent_conf = data.get('confidence', 0.5)
                agent_context.append(f"- {agent_name}: {agent_signal} ({agent_conf:.0%} confidence)")
            
            agents_text = "\n".join(agent_context) if agent_context else "No detailed agent data available."
            
            system_prompt = """You are an expert forex trading analyst. Provide clear, concise trading signal explanations.
Focus on the key factors driving the signal. Be professional but accessible. Keep explanations under 150 words."""
            
            user_prompt = f"""Generate a trading signal explanation for {pair}.

Signal Details:
- Direction: {signal}
- Confidence: {confidence:.0%}

Agent Contributions:
{agents_text}

Provide a clear explanation of this trading signal, mentioning the consensus across agents and any important nuances."""
            
            explanation = self.tokenfactory.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=300
            )
            
            if explanation:
                logger.info(f"Generated Llama-3.1 explanation ({len(explanation)} chars)")
                return explanation.strip()
            
            return None
            
        except Exception as e:
            logger.error(f"LLM explanation generation failed: {e}")
            return None
    
    def _generate_template_explanation(self, signal_str: str, confidence: float, agent_signals: Dict) -> str:
        """
        Fallback template-based explanation generation
        """
        explanation_parts = []
        
        # Main signal statement
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
                agent_signal = {1: 'BUY', -1: 'SELL', 0: 'NEUTRAL'}.get(data.get('signal', 0), 'NEUTRAL')
                
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
    
    # ==================== LLAMA-3.1 POWERED FEATURES ====================
    
    def analyze_news_with_llm(self, headline: str, content: str = "") -> Dict:
        """
        Analyze financial news using Llama-3.1-70B
        Returns sentiment, impact assessment, and key insights
        """
        if not self.use_llama_for_explanations:
            # Fallback to basic sentiment
            full_text = f"{headline} {content}".strip()
            return self.analyze_sentiment(full_text)
        
        try:
            system_prompt = """You are a financial news analyst. Analyze the given news and provide:
1. Sentiment (POSITIVE, NEGATIVE, or NEUTRAL)
2. Confidence score (0.0-1.0)
3. Market impact assessment (HIGH, MEDIUM, LOW)
4. Key insights (2-3 bullet points)

Respond in JSON format only."""
            
            user_prompt = f"News Headline: {headline}\n\nContent: {content[:500]}\n\nAnalyze this financial news."
            
            response = self.tokenfactory.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=400
            )
            
            if response:
                # Try to extract JSON from response
                try:
                    json_match = re.search(r'\{.*\}', response, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                        return {
                            'label': result.get('sentiment', 'NEUTRAL'),
                            'score': result.get('confidence', 0.5),
                            'impact': result.get('impact', 'MEDIUM'),
                            'insights': result.get('insights', []),
                            'source': 'llama-3.1-70b',
                            'raw_response': response
                        }
                except:
                    pass
                
                # Fallback: parse text response
                return self._parse_llm_news_analysis(response, headline)
            
            # Fallback to basic sentiment
            return self.analyze_sentiment(f"{headline} {content}")
            
        except Exception as e:
            logger.error(f"LLM news analysis failed: {e}")
            return self.analyze_sentiment(f"{headline} {content}")
    
    def _parse_llm_news_analysis(self, response: str, headline: str) -> Dict:
        """Parse text response from LLM into structured format"""
        response_lower = response.lower()
        
        # Determine sentiment
        if 'positive' in response_lower or 'bullish' in response_lower:
            sentiment = 'POSITIVE'
            score = 0.75
        elif 'negative' in response_lower or 'bearish' in response_lower:
            sentiment = 'NEGATIVE'
            score = 0.75
        else:
            sentiment = 'NEUTRAL'
            score = 0.5
        
        # Determine impact
        if 'high' in response_lower:
            impact = 'HIGH'
        elif 'low' in response_lower:
            impact = 'LOW'
        else:
            impact = 'MEDIUM'
        
        return {
            'label': sentiment,
            'score': score,
            'impact': impact,
            'insights': [line.strip('- ') for line in response.split('\n') if line.strip().startswith('-')][:3],
            'source': 'llama-3.1-70b',
            'raw_response': response
        }
    
    def generate_tactical_report(self, pair: str, signals: List[Dict], market_data: Dict) -> str:
        """
        Generate comprehensive tactical report using Llama-3.1-70B
        """
        if not self.use_llama_for_explanations:
            return self._generate_template_tactical_report(pair, signals, market_data)
        
        try:
            # Build signal summary
            signal_summary = []
            for sig in signals[:5]:  # Last 5 signals
                direction = sig.get('direction', 'NEUTRAL')
                conf = sig.get('confidence', 0.5)
                time = sig.get('timestamp', 'recent')
                signal_summary.append(f"- {direction} ({conf:.0%} confidence) at {time}")
            
            signals_text = "\n".join(signal_summary) if signal_summary else "No recent signals."
            
            system_prompt = """You are a senior forex strategist. Generate a tactical trading report that includes:
1. Current market situation summary
2. Key technical and macro factors
3. Trading recommendation with clear rationale
4. Risk considerations
5. Key levels to watch

Be concise but thorough. Professional tone."""
            
            user_prompt = f"""Generate a tactical report for {pair}.

Recent Signals:
{signals_text}

Market Data:
- Current Trend: {market_data.get('trend', 'Unknown')}
- Volatility: {market_data.get('volatility', 'Normal')}
- Support: {market_data.get('support', 'N/A')}
- Resistance: {market_data.get('resistance', 'N/A')}

Provide a comprehensive tactical analysis."""
            
            report = self.tokenfactory.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=800
            )
            
            if report:
                logger.info(f"Generated Llama-3.1 tactical report ({len(report)} chars)")
                return report.strip()
            
            return self._generate_template_tactical_report(pair, signals, market_data)
            
        except Exception as e:
            logger.error(f"LLM tactical report generation failed: {e}")
            return self._generate_template_tactical_report(pair, signals, market_data)
    
    def _generate_template_tactical_report(self, pair: str, signals: List[Dict], market_data: Dict) -> str:
        """Fallback template-based tactical report"""
        trend = market_data.get('trend', 'Unknown')
        volatility = market_data.get('volatility', 'Normal')
        
        report_parts = [
            f"# Tactical Report: {pair}",
            "",
            f"## Market Situation",
            f"Current trend: {trend}. Volatility: {volatility}.",
            "",
            "## Recent Signals",
        ]
        
        for sig in signals[:5]:
            direction = sig.get('direction', 'NEUTRAL')
            conf = sig.get('confidence', 0.5)
            report_parts.append(f"- {direction} signal ({conf:.0%} confidence)")
        
        report_parts.extend([
            "",
            "## Key Levels",
            f"- Support: {market_data.get('support', 'N/A')}",
            f"- Resistance: {market_data.get('resistance', 'N/A')}",
            "",
            "*Report generated by FX Alpha Platform*"
        ])
        
        return "\n".join(report_parts)
    
    def query_llm(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Optional[str]:
        """
        Direct access to Llama-3.1-70B for custom queries
        """
        if not self.use_llama_for_explanations:
            logger.warning("TokenFactory not available for LLM query")
            return None
        
        return self.tokenfactory.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=kwargs.get('temperature', 0.7),
            max_tokens=kwargs.get('max_tokens', 500)
        )


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
