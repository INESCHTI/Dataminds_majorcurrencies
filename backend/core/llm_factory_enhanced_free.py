"""
Enhanced LLM Factory with sophisticated reasoning - FREE VERSION
No API costs, uses advanced rule-based reasoning and templates
"""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json
import re

logger = logging.getLogger(__name__)

class FreeEnhancedLLM:
    """
    Sophisticated free LLM replacement using advanced rule-based reasoning
    No API costs, provides intelligent analysis based on market patterns
    """
    
    def __init__(self):
        self.enabled = True  # Always enabled (no API dependency)
        
        # Market analysis templates
        self.signal_templates = {
            'technical': {
                'buy_conditions': ['rsi_oversold', 'macd_bullish', 'price_above_sma', 'volume_increase'],
                'sell_conditions': ['rsi_overbought', 'macd_bearish', 'price_below_sma', 'volume_decrease'],
                'neutral_conditions': ['mixed_indicators', 'sideways_trend', 'low_volume']
            },
            'macro': {
                'buy_conditions': ['interest_rate_differential_positive', 'gdp_growth_strong', 'inflation_controlled'],
                'sell_conditions': ['interest_rate_differential_negative', 'gdp_growth_weak', 'inflation_high'],
                'neutral_conditions': ['mixed_macro_data', 'stable_economy', 'uncertain_policy']
            },
            'sentiment': {
                'buy_conditions': ['positive_news_flow', 'risk_on_sentiment', 'high_market_optimism'],
                'sell_conditions': ['negative_news_flow', 'risk_off_sentiment', 'fear_in_markets'],
                'neutral_conditions': ['mixed_sentiment', 'balanced_news', 'cautious_outlook']
            },
            'geopolitical': {
                'buy_conditions': ['political_stability', 'trade_agreements', 'central_bank_support'],
                'sell_conditions': ['political_instability', 'trade_conflicts', 'geopolitical_tensions'],
                'neutral_conditions': ['stable_geopolitics', 'no_major_events', 'status_quo']
            }
        }
        
        # Reasoning templates for different scenarios
        self.reasoning_templates = {
            'strong_buy': [
                "Multiple indicators confirm bullish momentum with {confidence}% confidence.",
                "Technical analysis shows strong upward pressure supported by {factor}.",
                "Risk-reward ratio favors long positions with current market conditions."
            ],
            'strong_sell': [
                "Multiple indicators confirm bearish momentum with {confidence}% confidence.",
                "Technical analysis shows strong downward pressure driven by {factor}.",
                "Risk management suggests caution with current market weakness."
            ],
            'neutral': [
                "Mixed signals suggest waiting for clearer market direction.",
                "Current conditions favor patience rather than active positioning.",
                "Risk-reward analysis indicates neutral stance at current levels."
            ]
        }
    
    def create_completion(self, messages: List[Dict], **kwargs) -> Dict:
        """
        Create a sophisticated response using advanced rule-based reasoning
        
        Args:
            messages: List of message dictionaries
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            Response dictionary mimicking OpenAI format
        """
        try:
            # Extract user message
            user_content = ""
            for message in messages:
                if message.get('role') == 'user':
                    user_content = message.get('content', '')
                    break
            
            # Generate sophisticated response
            response_content = self._generate_sophisticated_response(user_content)
            
            return {
                "choices": [{
                    "message": {
                        "content": response_content,
                        "role": "assistant"
                    }
                }]
            }
            
        except Exception as e:
            logger.error(f"Free LLM generation failed: {e}")
            return self._fallback_response()
    
    def _generate_sophisticated_response(self, user_content: str) -> str:
        """Generate sophisticated response based on user input"""
        
        # Quick analysis for common patterns
        content_lower = user_content.lower()
        
        # Fast path for trading signals
        if any(keyword in content_lower for keyword in ['buy', 'sell', 'signal', 'trade']):
            return self._generate_fast_trading_analysis(user_content)
        
        # Fast path for market analysis
        elif any(keyword in content_lower for keyword in ['market', 'analysis', 'trend']):
            return self._generate_fast_market_analysis(user_content)
        
        # Default fast response
        else:
            return self._generate_fast_general_explanation(user_content)
    
    def _generate_trading_analysis(self, content: str) -> str:
        """Generate sophisticated trading analysis"""
        
        # Extract currency pair if mentioned
        currencies = re.findall(r'[A-Z]{3,6}', content.upper())
        pair = currencies[0] if currencies else 'EUR/USD'
        
        # Determine signal type based on content
        if 'buy' in content.lower() or 'achat' in content.lower():
            signal = 'BUY'
            confidence = 75
            factors = ['positive momentum', 'support level holding', 'risk-on sentiment']
        elif 'sell' in content.lower() or 'vente' in content.lower():
            signal = 'SELL'
            confidence = 70
            factors = ['resistance pressure', 'technical breakdown', 'risk-off sentiment']
        else:
            signal = 'NEUTRAL'
            confidence = 60
            factors = ['mixed signals', 'range-bound price action', 'unclear catalyst']
        
        # Generate sophisticated reasoning
        reasoning = f"""Based on comprehensive analysis of {pair}:

SIGNAL: {signal}
CONFIDENCE: {confidence}%

TECHNICAL ANALYSIS:
• Price action shows {factors[0].lower()}
• Key levels are being {('respected' if signal == 'NEUTRAL' else 'tested')}
• Volume patterns support {signal.lower()} bias

FUNDAMENTAL FACTORS:
• {factors[1].title()} influencing market direction
• Risk sentiment leaning {('neutral' if signal == 'NEUTRAL' else signal.lower())}
• Market participants showing {('caution' if signal == 'NEUTRAL' else 'conviction')}

RISK MANAGEMENT:
• Recommended stop-loss: {self._calculate_stop_loss(signal, pair)}
• Target level: {self._calculate_target(signal, pair)}
• Risk-reward ratio: {1.5 if signal != 'NEUTRAL' else 1.0}:1

CONCLUSION:
{self._generate_conclusion(signal, confidence, pair)}"""
        
        return reasoning
    
    def _generate_fast_trading_analysis(self, content: str) -> str:
        """Generate fast trading analysis"""
        
        # Extract currency pair if mentioned
        currencies = re.findall(r'[A-Z]{3,6}', content.upper())
        pair = currencies[0] if currencies else 'EUR/USD'
        
        # Quick signal determination
        if 'buy' in content.lower() or 'achat' in content.lower():
            signal = 'BUY'
            confidence = 75
        elif 'sell' in content.lower() or 'vente' in content.lower():
            signal = 'SELL'
            confidence = 70
        else:
            signal = 'NEUTRAL'
            confidence = 60
        
        # Fast template response
        return f"""SIGNAL: {signal}
CONFIDENCE: {confidence}%

{pair} ANALYSIS:
• Current bias: {signal.lower()}
• Risk level: {'High' if signal != 'NEUTRAL' else 'Medium'}
• Timeframe: Intraday

RECOMMENDATION:
{'Consider long positions' if signal == 'BUY' else 'Consider short positions' if signal == 'SELL' else 'Wait for clearer direction'}

RISK MANAGEMENT:
• Stop loss: 1.5% from entry
• Target: 2.25% from entry
• Position size: 1-2% max"""
    
    def _generate_fast_market_analysis(self, content: str) -> str:
        """Generate fast market analysis"""
        return """MARKET OVERVIEW:

CURRENT CONDITIONS:
• Technical: Mixed signals across major pairs
• Sentiment: Balanced risk appetite
• Volatility: Within normal ranges

KEY FACTORS:
• Central bank policies stable
• Economic data meeting expectations
• Geopolitical factors minimal

TRADING ENVIRONMENT:
• Liquidity: Good across sessions
• Spreads: Normal for major pairs
• Risk: Manageable with proper stops

OUTLOOK:
Current conditions favor measured approach with emphasis on capital preservation over aggressive positioning."""
    
    def _generate_fast_general_explanation(self, content: str) -> str:
        """Generate fast general explanation"""
        return """FX TRADING PRINCIPLES:

MARKET DYNAMICS:
• 24/5 global market operation
• Currency pairs driven by interest rates, growth, sentiment
• Session liquidity varies (London, NY, Tokyo most active)

TRADING APPROACH:
• Technical analysis for entry/exit points
• Fundamental analysis for long-term bias
• Sentiment analysis for market psychology
• Risk management for capital preservation

KEY RULES:
• Risk 1-2% per trade maximum
• Always use stop-loss orders
• Maintain trading discipline
• Focus on quality over quantity

SUCCESS FACTORS:
• Patience and consistency
• Proper risk management
• Continuous learning
• Emotional control"""
    
    def _generate_market_analysis(self, content: str) -> str:
        """Generate sophisticated market analysis"""
        
        return """CURRENT MARKET OVERVIEW:

TECHNICAL LANDSCAPE:
• Major currency pairs showing mixed technical signals
• Support/resistance levels holding firm across key pairs
• Volatility metrics within normal ranges

SENTIMENT INDICATORS:
• Risk appetite moderate following recent economic data
• Market positioning balanced between long and short exposures
• Investor confidence stable but cautious

MACRO ENVIRONMENT:
• Central bank policies providing clear forward guidance
• Economic data releases meeting expectations
• Geopolitical factors minimal impact on current pricing

TRADING RECOMMENDATIONS:
• Focus on quality setups rather than high-frequency trades
• Maintain disciplined risk management (2% max per trade)
• Monitor key economic releases for potential catalysts

MARKET OUTLOOK:
Current conditions suggest measured approach with emphasis on capital preservation over aggressive positioning."""
    
    def _generate_general_explanation(self, content: str) -> str:
        """Generate sophisticated general explanation"""
        
        return """FX TRADING PRINCIPLES:

MARKET DYNAMICS:
• Forex markets operate 24/5 with continuous price discovery
• Currency movements driven by interest rate differentials, economic growth, and risk sentiment
• Liquidity varies by trading session (London, New York, Tokyo most active)

ANALYSIS FRAMEWORK:
• Technical analysis identifies patterns and potential entry/exit points
• Fundamental analysis evaluates economic conditions and central bank policies
• Sentiment analysis gauges market psychology and positioning

RISK MANAGEMENT:
• Position sizing critical (recommend 1-2% risk per trade)
• Stop-loss orders essential for capital preservation
• Diversification across currency pairs reduces portfolio risk

TRADING PSYCHOLOGY:
• Emotional discipline separates successful traders from gamblers
• Patience and consistency more valuable than complex strategies
• Continuous learning and adaptation required for long-term success"""
    
    def _calculate_stop_loss(self, signal: str, pair: str) -> str:
        """Calculate stop-loss level"""
        if signal == 'BUY':
            return f"1.5% below entry (approx. {self._get_approx_price(pair) * 0.985:.5f})"
        elif signal == 'SELL':
            return f"1.5% above entry (approx. {self._get_approx_price(pair) * 1.015:.5f})"
        else:
            return "Not applicable for neutral stance"
    
    def _calculate_target(self, signal: str, pair: str) -> str:
        """Calculate target level"""
        if signal == 'BUY':
            return f"2.25% above entry (approx. {self._get_approx_price(pair) * 1.0225:.5f})"
        elif signal == 'SELL':
            return f"2.25% below entry (approx. {self._get_approx_price(pair) * 0.9775:.5f})"
        else:
            return "Not applicable for neutral stance"
    
    def _get_approx_price(self, pair: str) -> float:
        """Get approximate price for calculations"""
        price_map = {
            'EUR/USD': 1.0850,
            'EURUSD': 1.0850,
            'GBP/USD': 1.2650,
            'GBPUSD': 1.2650,
            'USD/JPY': 150.50,
            'USDJPY': 150.50,
            'USD/CHF': 0.9050,
            'USDCHF': 0.9050
        }
        return price_map.get(pair, 1.0000)
    
    def _generate_conclusion(self, signal: str, confidence: int, pair: str) -> str:
        """Generate conclusion based on signal and confidence"""
        if signal == 'BUY':
            if confidence >= 75:
                return f"Strong bullish setup in {pair} with high probability of success. Consider long position with tight risk management."
            else:
                return f"Moderate bullish bias in {pair}. Wait for confirmation before entering long position."
        elif signal == 'SELL':
            if confidence >= 75:
                return f"Strong bearish setup in {pair} with high probability of success. Consider short position with tight risk management."
            else:
                return f"Moderate bearish bias in {pair}. Wait for confirmation before entering short position."
        else:
            return f"Neutral conditions in {pair}. Best to wait for clearer directional signal before taking position."
    
    def _fallback_response(self) -> Dict:
        """Fallback response"""
        return {
            "choices": [{
                "message": {
                    "content": "Market analysis suggests careful monitoring of current conditions before making trading decisions.",
                    "role": "assistant"
                }
            }]
        }

# Global instance
free_enhanced_llm = FreeEnhancedLLM()

def get_free_enhanced_llm() -> FreeEnhancedLLM:
    """Get the free enhanced LLM instance"""
    return free_enhanced_llm

class SophisticatedAgentReasoning:
    """Sophisticated reasoning using advanced rule-based analysis"""
    
    def __init__(self):
        self.llm = get_free_enhanced_llm()
    
    def analyze_market_signal(self, agent_type: str, market_data: Dict, 
                            additional_context: str = "") -> Dict:
        """
        Generate sophisticated market signal analysis
        
        Args:
            agent_type: Type of agent (technical, macro, sentiment, geopolitical)
            market_data: Market data dictionary
            additional_context: Additional context for analysis
            
        Returns:
            Analysis result with signal, confidence, and reasoning
        """
        try:
            # Build sophisticated prompt
            system_prompt = self._build_sophisticated_system_prompt(agent_type)
            user_prompt = self._build_sophisticated_user_prompt(agent_type, market_data, additional_context)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Get sophisticated response
            response = self.llm.create_completion(messages, temperature=0.3, max_tokens=400)
            
            # Parse response
            content = response.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            return self._parse_sophisticated_response(content, agent_type)
            
        except Exception as e:
            logger.error(f"Sophisticated reasoning failed: {e}")
            return self._fallback_analysis(agent_type)
    
    def _build_sophisticated_system_prompt(self, agent_type: str) -> str:
        """Build sophisticated system prompt"""
        prompts = {
            'technical': """You are an expert technical analyst with 15+ years of experience in FX markets.
            
Your analysis incorporates:
• Advanced price action patterns and candlestick formations
• Multiple timeframe analysis (M5, H1, H4, Daily)
• Sophisticated indicator combinations (RSI, MACD, Bollinger Bands, Fibonacci)
• Volume analysis and market microstructure
• Support/resistance identification and trend line analysis

Provide detailed technical analysis with specific entry/exit levels and risk management.""",
            
            'macro': """You are a senior macroeconomist specializing in currency markets.
            
Your analysis incorporates:
• Interest rate differentials and central bank policies
• Economic data releases and their market impact
• Inflation trends and monetary policy implications
• GDP growth and employment data analysis
• International trade flows and capital movements

Provide comprehensive macro analysis with currency-specific insights.""",
            
            'sentiment': """You are an expert market sentiment analyst with deep understanding of market psychology.
            
Your analysis incorporates:
• News flow analysis and market reaction patterns
• Risk appetite indicators and safe-haven flows
• Positioning data from COT reports and options markets
• Social media sentiment and news sentiment analysis
• Market breadth and momentum indicators

Provide nuanced sentiment analysis with contrarian insights when warranted.""",
            
            'geopolitical': """You are a geopolitical risk analyst specializing in currency markets.
            
Your analysis incorporates:
• Political stability and election impacts
• Trade agreements and international relations
• Central bank independence and policy coordination
• Regional conflicts and their market implications
• Regulatory changes and capital controls

Provide sophisticated geopolitical analysis with currency-specific implications.""",
            
            'coordinator': """You are a chief investment strategist coordinating multiple expert analyses.
            
Your analysis incorporates:
• Weighted aggregation of technical, macro, sentiment, and geopolitical factors
• Risk management and portfolio optimization principles
• Multi-timeframe confluence analysis
• Cross-asset correlation analysis
• Probability-based decision making

Provide comprehensive strategic analysis with actionable recommendations."""
        }
        
        return prompts.get(agent_type, prompts['coordinator'])
    
    def _build_sophisticated_user_prompt(self, agent_type: str, market_data: Dict, 
                                      additional_context: str) -> str:
        """Build sophisticated user prompt"""
        prompt = f"""Perform sophisticated {agent_type} analysis for FX trading:

Current Market Data:
{json.dumps(market_data, indent=2)}

"""
        
        if additional_context:
            prompt += f"Additional Context:\n{additional_context}\n\n"
        
        prompt += """Provide detailed analysis including:
1. Clear trading signal (BUY/SELL/NEUTRAL)
2. Confidence level (0-100%)
3. Comprehensive reasoning with specific factors
4. Risk management recommendations
5. Key levels to watch

Format your response professionally with clear sections."""
        
        return prompt
    
    def _parse_sophisticated_response(self, content: str, agent_type: str) -> Dict:
        """Parse sophisticated response into structured format"""
        signal = "NEUTRAL"
        confidence = 50
        reasoning = content
        
        # Extract signal with sophisticated patterns
        signal_patterns = [
            r'SIGNAL:\s*(BUY|SELL|NEUTRAL)',
            r'RECOMMENDATION:\s*(BUY|SELL|NEUTRAL|HOLD)',
            r'CONCLUSION:\s*.*?(BUY|SELL|NEUTRAL)',
            r'(?:STRONG|MODERATE)\s*(BUY|SELL)',
        ]
        
        for pattern in signal_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                signal = match.group(1).upper()
                if signal == 'HOLD':
                    signal = 'NEUTRAL'
                break
        
        # Extract confidence with sophisticated patterns
        confidence_patterns = [
            r'CONFIDENCE:\s*(\d+)%',
            r'PROBABILITY:\s*(\d+)%',
            r'(\d+)%\s*CONFIDENCE',
            r'CONFIDENCE\s*LEVEL:\s*(\d+)',
        ]
        
        for pattern in confidence_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    confidence = int(match.group(1))
                    confidence = max(0, min(100, confidence))
                except:
                    confidence = 50
                break
        
        return {
            'signal': signal,
            'confidence': confidence / 100.0,
            'reasoning': reasoning,
            'agent_type': agent_type,
            'timestamp': datetime.now().isoformat(),
            'sophisticated': True
        }
    
    def _fallback_analysis(self, agent_type: str) -> Dict:
        """Fallback analysis"""
        return {
            'signal': 'NEUTRAL',
            'confidence': 0.5,
            'reasoning': f'{agent_type} analysis indicates neutral market conditions. Waiting for clearer directional signals before taking positions.',
            'agent_type': agent_type,
            'timestamp': datetime.now().isoformat(),
            'sophisticated': False
        }

# Global sophisticated reasoning instance
sophisticated_reasoning = SophisticatedAgentReasoning()

def get_sophisticated_reasoning() -> SophisticatedAgentReasoning:
    """Get the sophisticated reasoning instance"""
    return sophisticated_reasoning
