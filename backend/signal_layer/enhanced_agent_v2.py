"""
Enhanced Agent using TokenFactory LLM for sophisticated analysis
"""

from typing import Dict, List, Optional
import logging
from datetime import datetime
from core.llm_factory_tokenfactory import get_enhanced_reasoning

logger = logging.getLogger(__name__)

class EnhancedAgentV2:
    """
    Enhanced agent that uses TokenFactory LLM for sophisticated market analysis
    """
    
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.enhanced_reasoning = get_enhanced_reasoning()
    
    def generate_signal(self, market_data: Dict, additional_context: str = "") -> Dict:
        """
        Generate sophisticated trading signal using LLM analysis
        
        Args:
            market_data: Dictionary containing relevant market data
            additional_context: Additional context for analysis
            
        Returns:
            Signal dictionary with direction, confidence, and reasoning
        """
        try:
            # Use enhanced reasoning for analysis
            analysis = self.enhanced_reasoning.analyze_market_signal(
                agent_type=self.agent_type,
                market_data=market_data,
                additional_context=additional_context
            )
            
            # Convert signal to numeric format
            signal_map = {'BUY': 1, 'SELL': -1, 'NEUTRAL': 0}
            numeric_signal = signal_map.get(analysis.get('signal', 'NEUTRAL'), 0)
            
            return {
                'signal': numeric_signal,
                'confidence': analysis.get('confidence', 0.5),
                'reasoning': analysis.get('reasoning', f'{self.agent_type} analysis completed.'),
                'agent_type': self.agent_type,
                'timestamp': datetime.now().isoformat(),
                'llm_enhanced': True
            }
            
        except Exception as e:
            logger.error(f"Enhanced {self.agent_type} agent failed: {e}")
            return self._fallback_signal(market_data)
    
    def _fallback_signal(self, market_data: Dict) -> Dict:
        """Fallback signal generation when LLM fails"""
        return {
            'signal': 0,  # NEUTRAL
            'confidence': 0.3,
            'reasoning': f'{self.agent_type} analysis unavailable - using neutral stance.',
            'agent_type': self.agent_type,
            'timestamp': datetime.now().isoformat(),
            'llm_enhanced': False
        }

class EnhancedTechnicalAgent(EnhancedAgentV2):
    """Enhanced Technical Analysis Agent"""
    
    def __init__(self):
        super().__init__('technical')
    
    def generate_signal(self, ohlcv_data: Dict, indicators: Dict = None) -> Dict:
        """Generate technical signal with LLM enhancement"""
        market_data = {
            'price_data': ohlcv_data,
            'technical_indicators': indicators or {},
            'analysis_type': 'technical'
        }
        
        additional_context = "Focus on price action, support/resistance levels, and technical indicators."
        
        return super().generate_signal(market_data, additional_context)

class EnhancedMacroAgent(EnhancedAgentV2):
    """Enhanced Macro Economic Agent"""
    
    def __init__(self):
        super().__init__('macro')
    
    def generate_signal(self, economic_data: Dict, currency_pair: str) -> Dict:
        """Generate macro signal with LLM enhancement"""
        market_data = {
            'economic_indicators': economic_data,
            'currency_pair': currency_pair,
            'analysis_type': 'macroeconomic'
        }
        
        additional_context = f"Analyze macroeconomic factors affecting {currency_pair} including interest rates, inflation, and GDP."
        
        return super().generate_signal(market_data, additional_context)

class EnhancedSentimentAgent(EnhancedAgentV2):
    """Enhanced Market Sentiment Agent"""
    
    def __init__(self):
        super().__init__('sentiment')
    
    def generate_signal(self, sentiment_data: Dict, news_headlines: List[str] = None) -> Dict:
        """Generate sentiment signal with LLM enhancement"""
        market_data = {
            'sentiment_scores': sentiment_data,
            'news_headlines': news_headlines or [],
            'analysis_type': 'sentiment'
        }
        
        additional_context = "Analyze market sentiment, news sentiment, and social media indicators."
        
        return super().generate_signal(market_data, additional_context)

class EnhancedGeopoliticalAgent(EnhancedAgentV2):
    """Enhanced Geopolitical Analysis Agent"""
    
    def __init__(self):
        super().__init__('geopolitical')
    
    def generate_signal(self, currencies: List[str], geopolitical_events: List[str] = None) -> Dict:
        """Generate geopolitical signal with LLM enhancement"""
        market_data = {
            'currencies': currencies,
            'geopolitical_events': geopolitical_events or [],
            'analysis_type': 'geopolitical'
        }
        
        additional_context = f"Analyze geopolitical factors affecting {', '.join(currencies)} including political stability, trade relations, and central bank policies."
        
        return super().generate_signal(market_data, additional_context)

# Factory function
def create_enhanced_agent(agent_type: str) -> EnhancedAgentV2:
    """Create an enhanced agent of the specified type"""
    agents = {
        'technical': EnhancedTechnicalAgent,
        'macro': EnhancedMacroAgent,
        'sentiment': EnhancedSentimentAgent,
        'geopolitical': EnhancedGeopoliticalAgent
    }
    
    agent_class = agents.get(agent_type.lower())
    if not agent_class:
        raise ValueError(f"Unknown agent type: {agent_type}")
    
    return agent_class()
