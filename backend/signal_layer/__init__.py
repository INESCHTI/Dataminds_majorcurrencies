"""
Signal Layer - Deterministic signal generation
Agents use PURE LOGIC - no LLM for decisions

NEW: OrchestratorAgent - LLM as Judge for intelligent query routing
"""
from .technical_agent_v2 import TechnicalAgentV2
from .macro_agent_v2 import MacroAgentV2
from .sentiment_agent_v2 import SentimentAgentV2
from .geopolitical_agent_v2 import GeopoliticalAgentV2
from .coordinator_agent_v2 import CoordinatorAgentV2
from .orchestrator_agent import OrchestratorAgent, AgentRoutingDecision, orchestrate_query

__all__ = [
    'TechnicalAgentV2', 
    'MacroAgentV2', 
    'SentimentAgentV2', 
    'GeopoliticalAgentV2',
    'CoordinatorAgentV2',
    'OrchestratorAgent',
    'AgentRoutingDecision',
    'orchestrate_query'
]
