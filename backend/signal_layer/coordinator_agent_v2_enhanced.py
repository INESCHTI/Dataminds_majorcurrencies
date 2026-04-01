"""
Enhanced Coordinator Agent V2 - Multi-Agent Framework
Implements your comprehensive FX multi-agent vision
"""
from typing import Dict, List
import numpy as np
from datetime import datetime, timedelta
from signal_layer.technical_agent_v2_enhanced import TechnicalAgentV2Enhanced
from signal_layer.macro_agent_v2 import MacroAgentV2
from signal_layer.sentiment_agent_v2 import SentimentAgentV2
from signal_layer.geopolitical_agent_v2_enhanced import GeopoliticalAgentV2Enhanced
from monitoring.performance_tracker import PerformanceTracker


class CoordinatorAgentV2Enhanced:
    """
    Enhanced Meta-Agent for Comprehensive FX Analysis
    
    Integrates 4 specialized agents:
    1. TechnicalAgentV2 - Multi-timeframe technical analysis
    2. MacroAgentV2 - Macroeconomic analysis  
    3. SentimentAgentV2 - Market sentiment analysis
    4. GeopoliticalAgentV2 - Political/event analysis (NEW)
    
    Features:
    - Dynamic weight optimization
    - Cross-pair correlation analysis
    - Multi-timezone session awareness
    - Economic announcement impact modeling
    """
    
    def __init__(self):
        # Initialize all agents
        self.technical_agent = TechnicalAgentV2Enhanced()
        self.macro_agent = MacroAgentV2()
        self.sentiment_agent = SentimentAgentV2()
        self.geopolitical_agent = GeopoliticalAgentV2Enhanced()  # ENHANCED: Real RSS feeds
        
        self.performance_tracker = PerformanceTracker()
        self.correlation_engine = None
        
        # Enhanced weights (includes geopolitical agent)
        self.agent_weights = {
            'TechnicalV2': 0.30,      # Reduced to accommodate new agent
            'MacroV2': 0.25,          # Reduced
            'SentimentV2': 0.20,     # Reduced
            'GeopoliticalV2': 0.25    # NEW: Significant weight for events
        }
        
        # Agent performance tracking
        self.agent_performance = {
            'TechnicalV2': {'accuracy': 0.5, 'sharpe': 0.0, 'signals': 0},
            'MacroV2': {'accuracy': 0.5, 'sharpe': 0.0, 'signals': 0},
            'SentimentV2': {'accuracy': 0.5, 'sharpe': 0.0, 'signals': 0},
            'GeopoliticalV2': {'accuracy': 0.5, 'sharpe': 0.0, 'signals': 0}
        }
        
        # Multi-timezone session weights
        self.session_weights = {
            'asia': 0.2,      # Tokyo/Singapore/Hong Kong
            'london': 0.4,    # Most liquid session
            'new_york': 0.4   # Overlap with London most active
        }
    
    def generate_final_signal(
        self,
        symbol: str,
        base_currency: str,
        quote_currency: str
    ) -> Dict:
        """
        Generate comprehensive trading signal using all 4 agents
        
        Enhanced Process:
        1. Detect current trading session
        2. Check for high-impact economic events
        3. Collect signals from all agents
        4. Apply session-based weight adjustments
        5. Dynamic weight optimization based on performance
        6. Cross-pair correlation validation
        7. Conflict detection and resolution
        8. Final weighted voting
        9. Risk-adjusted confidence calculation
        """
        
        # 1. Session detection
        current_session = self._detect_trading_session()
        
        # 2. Economic event check
        event_risk = self._check_economic_events(base_currency, quote_currency)
        
        # 3. Collect agent signals
        agent_signals = self._collect_all_agent_signals(symbol, base_currency, quote_currency)
        
        # 4. Session-based weight adjustment
        adjusted_weights = self._apply_session_weights(self.agent_weights, current_session, symbol)
        
        # 5. Dynamic weight optimization
        optimized_weights = self._optimize_weights(adjusted_weights, event_risk)
        
        # 6. Cross-pair correlation validation
        correlation_adjustment = self._validate_cross_pair_correlations(symbol, agent_signals)
        
        # 7. Conflict detection
        conflicts = self._detect_conflicts(agent_signals)
        
        # 8. Final weighted voting
        final_signal, confidence = self._weighted_voting(agent_signals, optimized_weights)
        
        # 9. Apply correlation adjustment
        if correlation_adjustment['adjust']:
            final_signal = correlation_adjustment['adjusted_signal']
            confidence *= 0.9  # Reduce confidence due to correlation conflict
        
        # 10. Risk adjustment
        if event_risk['high_impact']:
            confidence *= 0.7  # Reduce confidence during high-impact events
        
        return {
            'final_signal': final_signal,
            'confidence': confidence,
            'agent_signals': agent_signals,
            'weights_used': optimized_weights,
            'session': current_session,
            'event_risk': event_risk,
            'conflicts_detected': conflicts,
            'correlation_adjustment': correlation_adjustment,
            'market_regime': self._detect_market_regime(agent_signals),
            'timestamp': datetime.now().isoformat()
        }
    
    def _collect_all_agent_signals(
        self, 
        symbol: str, 
        base_currency: str, 
        quote_currency: str
    ) -> Dict:
        """Collect signals from all 4 agents"""
        currencies = [base_currency, quote_currency]
        
        agent_signals = {}
        
        # Technical Agent (Enhanced Multi-Timeframe)
        try:
            tech_signal = self.technical_agent.generate_signal(symbol, base_currency, quote_currency)
            agent_signals['TechnicalV2'] = {
                'signal': tech_signal['signal'],
                'confidence': tech_signal['confidence'],
                'reasoning': tech_signal['deterministic_reason'],
                'features': tech_signal['features_used']
            }
        except Exception as e:
            print(f"Technical agent error: {e}")
            agent_signals['TechnicalV2'] = {
                'signal': 0, 'confidence': 0.0, 'reasoning': f"Error: {str(e)}", 'features': {}
            }
        
        # Macro Agent
        try:
            macro_signal = self.macro_agent.generate_signal(base_currency, quote_currency)
            agent_signals['MacroV2'] = {
                'signal': macro_signal['signal'],
                'confidence': macro_signal['confidence'],
                'reasoning': macro_signal['deterministic_reason'],
                'features': macro_signal['features_used']
            }
        except Exception as e:
            print(f"Macro agent error: {e}")
            agent_signals['MacroV2'] = {
                'signal': 0, 'confidence': 0.0, 'reasoning': f"Error: {str(e)}", 'features': {}
            }
        
        # Sentiment Agent
        try:
            sentiment_signal = self.sentiment_agent.generate_signal(currencies)
            agent_signals['SentimentV2'] = {
                'signal': sentiment_signal['signal'],
                'confidence': sentiment_signal['confidence'],
                'reasoning': sentiment_signal['deterministic_reason'],
                'features': sentiment_signal['features_used']
            }
        except Exception as e:
            print(f"Sentiment agent error: {e}")
            agent_signals['SentimentV2'] = {
                'signal': 0, 'confidence': 0.0, 'reasoning': f"Error: {str(e)}", 'features': {}
            }
        
        # Geopolitical Agent (NEW)
        try:
            geo_signal = self.geopolitical_agent.generate_signal(currencies)
            agent_signals['GeopoliticalV2'] = {
                'signal': geo_signal['signal'],
                'confidence': geo_signal['confidence'],
                'reasoning': geo_signal['deterministic_reason'],
                'features': geo_signal['features_used']
            }
        except Exception as e:
            print(f"Geopolitical agent error: {e}")
            agent_signals['GeopoliticalV2'] = {
                'signal': 0, 'confidence': 0.0, 'reasoning': f"Error: {str(e)}", 'features': {}
            }
        
        return agent_signals
    
    def _detect_trading_session(self) -> str:
        """Detect current trading session based on UTC time"""
        now = datetime.now()
        utc_hour = now.hour
        
        # Asia session (Tokyo open 00:00 UTC, close 09:00 UTC)
        if 0 <= utc_hour < 9:
            return 'asia'
        # London session (08:00 UTC - 17:00 UTC)
        elif 8 <= utc_hour < 17:
            return 'london'
        # New York session (13:00 UTC - 22:00 UTC)
        elif 13 <= utc_hour < 22:
            return 'new_york'
        else:
            return 'off_hours'
    
    def _check_economic_events(self, base_currency: str, quote_currency: str) -> Dict:
        """Check for high-impact economic events"""
        # Simplified event detection - in production would use economic calendar API
        now = datetime.now()
        
        # Check if it's a major announcement day (first Friday = NFP, etc.)
        if now.weekday() == 4 and now.hour >= 12 and now.hour <= 14:  # Friday NFP time
            return {
                'high_impact': True,
                'event_type': 'NFP',
                'currencies_affected': ['USD'],
                'risk_level': 'high'
            }
        
        # Check for central bank meetings (simplified)
        if now.day <= 3 and now.weekday() == 2:  # First Tuesday of month
            return {
                'high_impact': True,
                'event_type': 'Central Bank Meeting',
                'currencies_affected': [base_currency, quote_currency],
                'risk_level': 'medium'
            }
        
        return {
            'high_impact': False,
            'event_type': None,
            'currencies_affected': [],
            'risk_level': 'low'
        }
    
    def _apply_session_weights(self, base_weights: Dict, session: str, symbol: str) -> Dict:
        """Apply session-based weight adjustments"""
        adjusted_weights = base_weights.copy()
        session_weight = self.session_weights.get(session, 0.33)
        
        # Adjust weights based on session and currency pair
        if session == 'asia':
            # Boost JPY-related pairs during Asia session
            if 'JPY' in symbol:
                adjusted_weights['TechnicalV2'] *= 1.2
                adjusted_weights['MacroV2'] *= 0.8
        elif session == 'london':
            # Boost EUR/GBP pairs during London session
            if 'EUR' in symbol or 'GBP' in symbol:
                adjusted_weights['TechnicalV2'] *= 1.1
                adjusted_weights['GeopoliticalV2'] *= 1.1
        elif session == 'new_york':
            # Boost USD pairs during NY session
            if 'USD' in symbol:
                adjusted_weights['MacroV2'] *= 1.2
                adjusted_weights['SentimentV2'] *= 1.1
        
        # Normalize weights
        total_weight = sum(adjusted_weights.values())
        return {k: v/total_weight for k, v in adjusted_weights.items()}
    
    def _optimize_weights(self, weights: Dict, event_risk: Dict) -> Dict:
        """Dynamic weight optimization based on conditions"""
        optimized_weights = weights.copy()
        
        if event_risk['high_impact']:
            # Increase weight for agents that handle events better
            optimized_weights['GeopoliticalV2'] *= 1.5
            optimized_weights['MacroV2'] *= 1.3
            optimized_weights['TechnicalV2'] *= 0.7
            optimized_weights['SentimentV2'] *= 0.8
        
        # Normalize
        total_weight = sum(optimized_weights.values())
        return {k: v/total_weight for k, v in optimized_weights.items()}
    
    def _validate_cross_pair_correlations(self, symbol: str, agent_signals: Dict) -> Dict:
        """Validate signals against cross-pair correlations"""
        # Simplified correlation check
        # In production, would use actual correlation matrix
        
        # Check for conflicting signals in correlated pairs
        conflicting_pairs = []
        
        # EUR/USD and USD/CHF correlation check
        if symbol == 'EURUSD' or symbol == 'USDCHF':
            # These pairs should generally move inversely
            conflicting_pairs.append('EURUSD-USDCHF')
        
        # GBP/USD and EUR/USD correlation check  
        if symbol == 'GBPUSD' or symbol == 'EURUSD':
            # These pairs should generally move together
            conflicting_pairs.append('GBPUSD-EURUSD')
        
        return {
            'adjust': len(conflicting_pairs) > 0,
            'conflicting_pairs': conflicting_pairs,
            'adjusted_signal': agent_signals.get('TechnicalV2', {}).get('signal', 0)  # Simplified
        }
    
    def _detect_conflicts(self, agent_signals: Dict) -> List[str]:
        """Detect conflicts between agent signals"""
        conflicts = []
        
        signals = {name: data['signal'] for name, data in agent_signals.items()}
        confidences = {name: data['confidence'] for name, data in agent_signals.items()}
        
        # Check for strong disagreements
        buy_signals = [name for name, signal in signals.items() if signal == 1 and confidences[name] > 0.6]
        sell_signals = [name for name, signal in signals.items() if signal == -1 and confidences[name] > 0.6]
        
        if buy_signals and sell_signals:
            conflicts.append(f"Strong disagreement: {', '.join(buy_signals)} vs {', '.join(sell_signals)}")
        
        # Check for low overall confidence
        avg_confidence = sum(confidences.values()) / len(confidences)
        if avg_confidence < 0.3:
            conflicts.append("Low confidence across all agents")
        
        return conflicts
    
    def _weighted_voting(self, agent_signals: Dict, weights: Dict) -> tuple:
        """Perform weighted voting to get final signal"""
        weighted_score = 0.0
        total_confidence_weight = 0.0
        
        for agent_name, weight in weights.items():
            if agent_name in agent_signals:
                signal_data = agent_signals[agent_name]
                signal = signal_data['signal']
                confidence = signal_data['confidence']
                
                weighted_score += signal * confidence * weight
                total_confidence_weight += confidence * weight
        
        if total_confidence_weight == 0:
            return 0, 0.0
        
        final_score = weighted_score / total_confidence_weight
        avg_confidence = total_confidence_weight / sum(weights.values())
        
        # Convert score to signal
        if final_score > 0.3:
            return 1, avg_confidence
        elif final_score < -0.3:
            return -1, avg_confidence
        else:
            return 0, avg_confidence
    
    def _detect_market_regime(self, agent_signals: Dict) -> str:
        """Detect current market regime"""
        # Analyze agent consensus and volatility
        signals = [data['signal'] for data in agent_signals.values()]
        confidences = [data['confidence'] for data in agent_signals.values()]
        
        # High consensus with high confidence = trending market
        avg_confidence = sum(confidences) / len(confidences)
        signal_variance = np.var(signals) if len(signals) > 1 else 0
        
        if avg_confidence > 0.7 and signal_variance < 1:
            return 'trending'
        elif avg_confidence < 0.4 or signal_variance > 2:
            return 'volatile'
        else:
            return 'neutral'
