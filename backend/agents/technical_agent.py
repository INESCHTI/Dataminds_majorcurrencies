"""
PHASE 3: Technical Agent
Analyzes technical indicators to generate trading signals
"""
from typing import Dict, Optional
from datetime import datetime, timedelta

# Import conditionnel pour éviter les erreurs
try:
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    PromptTemplate = None
    LLMChain = None

from agents.base_agent import BaseAgent, AgentOutput
from features.models import TechnicalFeatures


class TechnicalAgent(BaseAgent):
    """Agent that analyzes technical indicators"""
    
    AGENT_TYPE = 'technical'
    
    def __init__(self):
        super().__init__()
        # Prompt template conditionnel
        if LANGCHAIN_AVAILABLE and PromptTemplate:
            self.DECISION_PROMPT = PromptTemplate(
                input_variables=["symbol", "rsi", "macd", "bb_position", "trend", "volatility"],
                template="""You are a technical analysis expert. Analyze these indicators and make a trading decision.
        
        Symbol: {symbol}
        RSI: {rsi}
        MACD: {macd}
        Bollinger Band Position: {bb_position}
        Trend: {trend}
        Volatility: {volatility}
        
        Based on these indicators, should we BUY, SELL, or HOLD? Provide a brief explanation.
        
        Decision:
        Explanation:"""
            )
        else:
            self.DECISION_PROMPT = None
    
    def _create_decision_chain(self) -> Optional[LLMChain]:
        """Create LLM chain for decision making"""
        if not LANGCHAIN_AVAILABLE or not self.DECISION_PROMPT:
            return None
            
        llm_factory = LLMFactory()
        llm = llm_factory.get_llm()
        if llm:
            return LLMChain(llm=llm, prompt=self.DECISION_PROMPT)
        return None
    
    def analyze_indicators(self, symbol: str, rsi: float, macd: float, 
                          bb_position: float, trend: str, volatility: float) -> AgentOutput:
        """Analyze technical indicators and generate signal"""
        
        # Rule-based analysis as fallback
        signal = "NEUTRAL"
        confidence = 0.5
        reasoning = "No clear technical signal"
        
        # RSI analysis
        if rsi < 30:
            signal = "BUY"
            confidence = 0.7
            reasoning = "RSI oversold condition"
        elif rsi > 70:
            signal = "SELL"
            confidence = 0.7
            reasoning = "RSI overbought condition"
        
        # MACD confirmation
        if macd > 0 and signal == "BUY":
            confidence += 0.1
            reasoning += " with MACD bullish confirmation"
        elif macd < 0 and signal == "SELL":
            confidence += 0.1
            reasoning += " with MACD bearish confirmation"
        
        # Trend alignment
        if trend == "bullish" and signal == "BUY":
            confidence += 0.1
            reasoning += " aligned with uptrend"
        elif trend == "bearish" and signal == "SELL":
            confidence += 0.1
            reasoning += " aligned with downtrend"
        
        # Cap confidence
        confidence = min(confidence, 0.9)
        
        return AgentOutput(
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            timestamp=datetime.now()
        )
    
    def generate_signal(self, symbol: str) -> Dict:
        """Generate trading signal for symbol"""
        try:
            # Get latest technical features
            features = TechnicalFeatures.objects.filter(symbol=symbol).order_by('-timestamp').first()
            
            if not features:
                return AgentOutput(
                    signal="NEUTRAL",
                    confidence=0.0,
                    reasoning="No technical data available",
                    timestamp=datetime.now()
                ).to_dict()
            
            # Analyze indicators
            output = self.analyze_indicators(
                symbol=symbol,
                rsi=features.rsi,
                macd=features.macd,
                bb_position=features.bb_position,
                trend=features.trend,
                volatility=features.volatility
            )
            
            return output.to_dict()
            
        except Exception as e:
            return AgentOutput(
                signal="NEUTRAL",
                confidence=0.0,
                reasoning=f"Error in technical analysis: {str(e)}",
                timestamp=datetime.now()
            ).to_dict()
