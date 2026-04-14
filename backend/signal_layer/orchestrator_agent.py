"""
Orchestrator Agent - LLM as a Judge for Intelligent Query Routing

This agent:
1. Receives the query
2. Uses LLM to analyze query type and context
3. Routes query to ONLY the relevant specialized agents
4. Returns routing decision to Coordinator for aggregation

LLM acts as a JUDGE to determine which agents should participate
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class QueryCategory(Enum):
    """Categories of trading queries"""
    TECHNICAL = "technical"           # Chart patterns, indicators, price action
    MACRO_ECONOMIC = "macro"         # Interest rates, GDP, inflation, PMI
    SENTIMENT = "sentiment"          # News, market mood, risk appetite
    GEOPOLITICAL = "geopolitical"    # Political events, trade wars, elections
    COMBINED = "combined"            # Multi-factor analysis
    GENERAL = "general"              # Generic market question


@dataclass
class AgentRoutingDecision:
    """Decision for which agents to invoke"""
    query_category: QueryCategory
    primary_agents: List[str] = field(default_factory=list)
    secondary_agents: List[str] = field(default_factory=list)
    reasoning: str = ""
    confidence: float = 0.0
    urgency_level: str = "normal"  # low, normal, high, critical
    expected_complexity: str = "medium"  # low, medium, high


class OrchestratorAgent:
    """
    Orchestrator Agent - The "Gatekeeper" that routes queries intelligently
    
    Uses LLM to:
    - Classify query intent
    - Determine which specialized agents are relevant
    - Set priority and complexity levels
    - Provide routing justification
    
    Example:
    - "EURUSD just broke resistance" → TechnicalAgent (high priority)
    - "Fed raised rates, what's next?" → MacroAgent + SentimentAgent
    - "Election in France affecting EUR" → GeopoliticalAgent + MacroAgent
    - "Should I buy EURUSD now?" → All agents (combined analysis)
    """
    
    AVAILABLE_AGENTS = {
        'technical': {
            'name': 'TechnicalAgentV2',
            'description': 'Technical analysis - RSI, MACD, Bollinger Bands, chart patterns, support/resistance',
            'best_for': [
                'chart patterns', 'technical indicators', 'price levels', 
                'trend analysis', 'breakouts', 'support resistance',
                'moving averages', 'momentum', 'volume analysis'
            ],
            'typical_response_time': 'fast',
            'weight_default': 0.30
        },
        'macro': {
            'name': 'MacroAgentV2',
            'description': 'Macroeconomic analysis - FRED data, interest rates, GDP, inflation, PMI',
            'best_for': [
                'interest rates', 'central bank policy', 'inflation', 'GDP',
                'economic indicators', 'monetary policy', 'carry trade',
                'economic calendar', 'rate differentials', 'recession signals'
            ],
            'typical_response_time': 'medium',
            'weight_default': 0.25
        },
        'sentiment': {
            'name': 'SentimentAgentV2',
            'description': 'Sentiment analysis - News, social media, market positioning, risk appetite',
            'best_for': [
                'market sentiment', 'news analysis', 'risk on risk off',
                'market positioning', 'fear greed', 'news sentiment',
                'headlines', 'market mood', 'speculative positioning'
            ],
            'typical_response_time': 'fast',
            'weight_default': 0.20
        },
        'geopolitical': {
            'name': 'GeopoliticalAgentV2',
            'description': 'Geopolitical analysis - Political stability, trade policies, elections, conflicts',
            'best_for': [
                'elections', 'trade wars', 'sanctions', 'political instability',
                'geopolitical risk', 'government policy', 'wars conflicts',
                'diplomatic tensions', 'regional stability', 'brexit'
            ],
            'typical_response_time': 'medium',
            'weight_default': 0.25
        }
    }
    
    def __init__(self):
        self.llm_classifier = None
        self._init_llm()
    
    def _init_llm(self):
        """Initialize LLM for classification"""
        try:
            from core.llm_factory_enhanced_free import FreeEnhancedLLM
            self.llm_classifier = FreeEnhancedLLM()
            logger.info("Orchestrator LLM initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize LLM classifier: {e}")
            self.llm_classifier = None
    
    def analyze_and_route(
        self, 
        query: str, 
        symbol: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> AgentRoutingDecision:
        """
        Main orchestration method - LLM as Judge
        
        Args:
            query: The user query or trading question
            symbol: Optional currency pair (e.g., "EURUSD")
            context: Additional context (timeframe, market conditions, etc.)
        
        Returns:
            AgentRoutingDecision with selected agents and reasoning
        """
        logger.info(f"Orchestrator analyzing query: {query[:100]}...")
        
        # Step 1: Classify query using LLM
        classification = self._classify_with_llm(query, symbol, context)
        
        # Step 2: Determine which agents to invoke
        routing_decision = self._determine_agent_selection(
            classification, query, symbol, context
        )
        
        logger.info(
            f"Routing decision: {routing_decision.query_category.value} | "
            f"Primary: {routing_decision.primary_agents} | "
            f"Secondary: {routing_decision.secondary_agents}"
        )
        
        return routing_decision
    
    def _classify_with_llm(
        self, 
        query: str, 
        symbol: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Use LLM to classify the query intent
        
        Returns classification with confidence scores for each category
        """
        if self.llm_classifier is None:
            # Fallback to rule-based classification
            return self._rule_based_classification(query, symbol)
        
        # Build classification prompt
        agent_descriptions = "\n".join([
            f"- {key.upper()}: {info['description']}\n  Best for: {', '.join(info['best_for'][:3])}"
            for key, info in self.AVAILABLE_AGENTS.items()
        ])
        
        prompt = f"""You are an intelligent query classifier for a multi-agent forex trading system.

QUERY: "{query}"
SYMBOL: {symbol or 'Not specified'}
CONTEXT: {context or 'None'}

AVAILABLE AGENTS:
{agent_descriptions}

Analyze this query and classify it. Determine:
1. PRIMARY category (the main topic)
2. Which agents are MOST relevant (primary)
3. Which agents might provide additional context (secondary)
4. Urgency level (low/normal/high/critical)
5. Complexity (low/medium/high)

Respond in this exact JSON format:
{{
    "category": "technical|macro|sentiment|geopolitical|combined|general",
    "primary_agents": ["agent_key1", "agent_key2"],
    "secondary_agents": ["agent_key3"],
    "confidence": 0.85,
    "urgency": "normal",
    "complexity": "medium",
    "reasoning": "Brief explanation of why these agents were selected"
}}

Your response (JSON only):"""

        try:
            messages = [{"role": "user", "content": prompt}]
            response = self.llm_classifier.create_completion(messages)
            
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Extract JSON from response
            json_match = self._extract_json(content)
            if json_match:
                classification = json.loads(json_match)
                return classification
            
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
        
        # Fallback to rule-based
        return self._rule_based_classification(query, symbol)
    
    def _rule_based_classification(
        self, 
        query: str, 
        symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fallback rule-based classification when LLM fails"""
        query_lower = query.lower()
        
        # Keyword matching for each category
        technical_keywords = [
            'rsi', 'macd', 'bollinger', 'support', 'resistance', 'trend', 
            'chart', 'pattern', 'breakout', 'moving average', 'ema', 'sma',
            'fibonacci', 'candlestick', 'doji', 'hammer', 'wedge', 'triangle'
        ]
        
        macro_keywords = [
            'fed', 'ecb', 'interest rate', 'gdp', 'inflation', 'cpi', 'ppi',
            'pmi', 'employment', 'nfp', 'unemployment', 'recession', 'growth',
            'monetary policy', 'hawkish', 'dovish', 'rate cut', 'rate hike'
        ]
        
        sentiment_keywords = [
            'sentiment', 'news', 'headline', 'risk on', 'risk off', 'fear',
            'greed', 'market mood', 'investor positioning', 'speculative',
            'bullish sentiment', 'bearish sentiment', 'confidence'
        ]
        
        geopolitical_keywords = [
            'election', 'war', 'conflict', 'sanctions', 'trade war', 'brexit',
            'political', 'government', 'diplomatic', 'tension', 'trump',
            'biden', 'putin', 'eu', 'nato', 'g7', 'g20', 'china', 'tariff'
        ]
        
        # Count matches
        tech_score = sum(1 for kw in technical_keywords if kw in query_lower)
        macro_score = sum(1 for kw in macro_keywords if kw in query_lower)
        sent_score = sum(1 for kw in sentiment_keywords if kw in query_lower)
        geo_score = sum(1 for kw in geopolitical_keywords if kw in query_lower)
        
        scores = {
            'technical': tech_score,
            'macro': macro_score,
            'sentiment': sent_score,
            'geopolitical': geo_score
        }
        
        # Determine primary category
        max_score = max(scores.values())
        if max_score == 0:
            category = 'combined'
            primary = ['technical', 'macro']
            secondary = ['sentiment']
        elif scores['geopolitical'] >= 2:
            category = 'geopolitical'
            primary = ['geopolitical', 'macro']
            secondary = ['sentiment']
        elif scores['macro'] >= 2:
            category = 'macro'
            primary = ['macro', 'technical']
            secondary = ['sentiment']
        elif scores['technical'] >= 2:
            category = 'technical'
            primary = ['technical', 'sentiment']
            secondary = ['macro']
        elif scores['sentiment'] >= 2:
            category = 'sentiment'
            primary = ['sentiment', 'technical']
            secondary = ['macro']
        else:
            category = 'combined'
            primary = list(scores.keys())
            secondary = []
        
        return {
            'category': category,
            'primary_agents': primary,
            'secondary_agents': secondary,
            'confidence': 0.7 if max_score > 0 else 0.5,
            'urgency': 'normal',
            'complexity': 'medium',
            'reasoning': f"Rule-based classification: {scores}"
        }
    
    def _determine_agent_selection(
        self,
        classification: Dict[str, Any],
        query: str,
        symbol: Optional[str],
        context: Optional[Dict]
    ) -> AgentRoutingDecision:
        """Convert classification to routing decision"""
        
        category = QueryCategory(classification.get('category', 'combined'))
        primary = classification.get('primary_agents', [])
        secondary = classification.get('secondary_agents', [])
        
        # Validate agent names
        valid_agents = set(self.AVAILABLE_AGENTS.keys())
        primary = [p for p in primary if p in valid_agents]
        secondary = [s for s in secondary if s in valid_agents]
        
        # Ensure at least one primary agent
        if not primary:
            primary = ['technical', 'macro']
        
        return AgentRoutingDecision(
            query_category=category,
            primary_agents=primary,
            secondary_agents=secondary,
            reasoning=classification.get('reasoning', 'No reasoning provided'),
            confidence=classification.get('confidence', 0.5),
            urgency_level=classification.get('urgency', 'normal'),
            expected_complexity=classification.get('complexity', 'medium')
        )
    
    def _extract_json(self, text: str) -> Optional[str]:
        """Extract JSON from LLM response"""
        try:
            # Find JSON block
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1 and end > start:
                return text[start:end+1]
        except Exception:
            pass
        return None
    
    def get_agent_metadata(self, agent_key: str) -> Dict:
        """Get metadata for an agent"""
        return self.AVAILABLE_AGENTS.get(agent_key, {})
    
    def explain_routing(
        self, 
        decision: AgentRoutingDecision,
        query: str
    ) -> str:
        """Generate human-readable explanation of routing decision"""
        
        lines = [
            f"Query Analysis: '{query[:50]}...'",
            f"",
            f"Category: {decision.query_category.value.upper()}",
            f"Confidence: {decision.confidence:.0%}",
            f"Urgency: {decision.urgency_level}",
            f"",
            f"Selected Agents:",
        ]
        
        for agent_key in decision.primary_agents:
            agent_info = self.AVAILABLE_AGENTS.get(agent_key, {})
            lines.append(f"  • {agent_info.get('name', agent_key)} (PRIMARY)")
        
        for agent_key in decision.secondary_agents:
            agent_info = self.AVAILABLE_AGENTS.get(agent_key, {})
            lines.append(f"  • {agent_info.get('name', agent_key)} (secondary)")
        
        lines.extend([
            f"",
            f"Reasoning: {decision.reasoning}"
        ])
        
        return "\n".join(lines)


# Singleton instance
_orchestrator_instance = None

def get_orchestrator() -> OrchestratorAgent:
    """Get orchestrator singleton"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = OrchestratorAgent()
    return _orchestrator_instance


def orchestrate_query(
    query: str, 
    symbol: Optional[str] = None,
    context: Optional[Dict] = None
) -> AgentRoutingDecision:
    """Convenience function to orchestrate a query"""
    orchestrator = get_orchestrator()
    return orchestrator.analyze_and_route(query, symbol, context)
