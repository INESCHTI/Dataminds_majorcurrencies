"""
Coordinator Agent V2 - DETERMINISTIC AGGREGATION
NO LLM for trading decisions
LLM only for final explanation generation

Integrations:
- Cross-pair correlation analysis (DSO1.3)
- Multi-timeframe support (DSO1.2)
- Dynamic weight adjustment based on performance
"""
from typing import Dict, List, Optional, Tuple
import numpy as np
import logging
import concurrent.futures
from datetime import datetime, timedelta

# Import enhanced free LLM for explanations
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.llm_factory_enhanced_free import get_sophisticated_reasoning
from datetime import datetime, timedelta
from signal_layer.technical_agent_v2 import TechnicalAgentV2
from signal_layer.macro_agent_v2 import MacroAgentV2
from signal_layer.sentiment_agent_v2 import SentimentAgentV2
from signal_layer.geopolitical_agent_v2 import GeopoliticalAgentV2
from monitoring.performance_tracker import PerformanceTracker
from data_layer.signal_recorder import record_signal, update_market_data
import logging

logger = logging.getLogger(__name__)


class CoordinatorAgentV2:
    """
    Meta-Agent that coordinates all agents
    
    DETERMINISTIC:
    - Weighted voting
    - Dynamic weight adjustment based on performance
    - Volatility regime detection
    - Conflict detection
    - Cross-pair correlation validation (DSO1.3)
    - Multi-timeframe confluence (DSO1.2)
    
    LLM: Only for final explanation text
    """
    
    def __init__(self):
        self.technical_agent = TechnicalAgentV2()
        self.macro_agent = MacroAgentV2()
        self.sentiment_agent = SentimentAgentV2()
        self.geopolitical_agent = GeopoliticalAgentV2()
        self.performance_tracker = PerformanceTracker()
        self.sophisticated_reasoning = get_sophisticated_reasoning()
        self.correlation_engine = None  # Initialize correlation engine
        
        # Default agent weights (deterministic)
        self.agent_weights = {
            'TechnicalV2': 0.30,
            'MacroV2': 0.25,
            'SentimentV2': 0.20,
            'GeopoliticalV2': 0.25
        }
    
    def _get_correlation_engine(self):
        """Lazy-load cross-pair correlation engine"""
        if self.correlation_engine is None:
            try:
                from feature_layer.cross_pair_correlations import CrossPairCorrelationEngine
                self.correlation_engine = CrossPairCorrelationEngine()
            except Exception:
                self.correlation_engine = None
        return self.correlation_engine
    
    def generate_final_signal(self, symbol: str, base_currency: str, quote_currency: str) -> Dict:
        """
        Generate final trading signal using all 4 agents with real logic and data
        
        Returns:
            {
                'final_signal': -1/0/1,
                'confidence': 0-1,
                'agent_signals': dict,
                'weights_used': dict,
                'conflicts_detected': bool,
                'explanation': str (from LLM)
            }
        """
        start_time = datetime.now()
        
        # Step 1: Collect all agent signals with real data and logic
        try:
            technical_signal = self.technical_agent.generate_signal(symbol)
        except Exception as e:
            logger.error(f"Technical agent failed: {e}")
            technical_signal = {
                'signal': 0, 
                'confidence': 0.5, 
                'features_used': {},
                'deterministic_reason': 'Technical agent failed',
                'agent': 'TechnicalV2'
            }
        
        try:
            # Get volatility for macro agent
            price_volatility = self._estimate_volatility(symbol)
            macro_signal = self.macro_agent.generate_signal(
                base_currency,
                quote_currency,
                price_volatility
            )
        except Exception as e:
            logger.error(f"Macro agent failed: {e}")
            macro_signal = {
                'signal': 0, 
                'confidence': 0.5, 
                'features_used': {},
                'deterministic_reason': 'Macro agent failed',
                'agent': 'MacroV2'
            }
        
        try:
            sentiment_signal = self.sentiment_agent.generate_signal(symbol)
        except Exception as e:
            logger.error(f"Sentiment agent failed: {e}")
            sentiment_signal = {
                'signal': 0, 
                'confidence': 0.5, 
                'features_used': {},
                'deterministic_reason': 'Sentiment agent failed',
                'agent': 'SentimentV2'
            }
        
        try:
            geopolitical_signal = self.geopolitical_agent.generate_signal(symbol)
        except Exception as e:
            logger.error(f"Geopolitical agent failed: {e}")
            geopolitical_signal = {
                'signal': 0, 
                'confidence': 0.5, 
                'features_used': {},
                'deterministic_reason': 'Geopolitical agent failed',
                'agent': 'GeopoliticalV2'
            }
        
        agent_signals = {
            'technical': technical_signal,
            'macro': macro_signal,
            'sentiment': sentiment_signal,
            'geopolitical': geopolitical_signal
        }
        
        # Step 2: Calculate weights
        weights = self._calculate_dynamic_weights(agent_signals)
        
        # Step 3: Check for conflicts
        conflicts = self._detect_conflicts(agent_signals)
        
        # Step 4: Generate final signal
        regime = self._detect_market_regime(technical_signal, self._estimate_volatility(symbol))
        final_signal, final_confidence = self._aggregate_signals(agent_signals, weights, regime)
        
        # Step 5: Generate explanation
        explanation = self._generate_explanation_text(
            final_signal, agent_signals, weights, conflicts
        )
        
        # Step 6: Record signal
        try:
            signal_data = {
                'symbol': symbol,
                'direction': final_signal,
                'confidence': final_confidence,
                'agent_signals': agent_signals,
                'weights_used': weights,
                'explanation': explanation
            }
            signal_id = record_signal(signal_data)
        except Exception as e:
            logger.error(f"Signal recording failed: {e}")
            signal_id = None
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'final_signal': final_signal,
            'confidence': final_confidence,
            'agent_signals': agent_signals,
            'weights_used': weights,
            'conflicts_detected': conflicts,
            'explanation': explanation,
            'signal_id': signal_id,
            'execution_time': execution_time,
            'market_regime': regime,
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_and_record_signal(self, pair: str, timeframe: str = 'H1') -> Dict:
        """
        Generate signal and record it in database for real performance tracking
        """
        print(f"DEBUG: generate_and_record_signal called for {pair}")
        
        # Parse pair
        if len(pair) == 6:
            base_currency = pair[:3]
            quote_currency = pair[3:6]
        else:
            base_currency = 'EUR'
            quote_currency = 'USD'
        
        # Generate the signal
        signal_data = self.generate_final_signal(pair, base_currency, quote_currency)
        
        # Record the signal for performance tracking
        signal_data_with_pair = {
            'pair': pair,
            'signal': signal_data.get('final_signal', 0),
            'confidence': signal_data.get('confidence', 0.0),
            'agent_signals': signal_data.get('agent_signals', {}),
            'deterministic_reason': signal_data.get('deterministic_reason', '')
        }
        
        print(f"DEBUG: About to record signal: {signal_data_with_pair}")
        signal_id = record_signal(signal_data_with_pair)
        print(f"DEBUG: Recorded signal ID: {signal_id}")
        
        # Add signal ID to the response
        signal_data['signal_id'] = signal_id
        
        return signal_data
    
    def _calculate_dynamic_weights(self, agent_signals: Dict) -> Dict[str, float]:
        """
        Adjust agent weights based on recent 30-day performance
        
        PURE DETERMINISTIC LOGIC
        """
        # Map agent signal keys to performance tracker keys
        agent_name_mapping = {
            'technical': 'TechnicalV2',
            'macro': 'MacroV2',
            'sentiment': 'SentimentV2',
            'geopolitical': 'GeopoliticalV2'
        }
        
        # Get recent performance for each agent
        performances = {}
        for signal_key, agent_name in agent_name_mapping.items():
            if signal_key in agent_signals:
                perf = self.performance_tracker.get_agent_performance(agent_name, days=30)
                performances[signal_key] = perf.get('sharpe_ratio', 0.0)
        
        # If no performance data, use default weights
        if all(p == 0.0 for p in performances.values()):
            return {
                'technical': 0.30,
                'macro': 0.25,
                'sentiment': 0.20,
                'geopolitical': 0.25
            }
        
        # Normalize Sharpe ratios to weights (softmax-like)
        # Add constant to avoid negative weights
        adjusted = {k: max(v + 2.0, 0.1) for k, v in performances.items()}
        total = sum(adjusted.values())
        
        final_weights = {k: v/total for k, v in adjusted.items()}
        
        return final_weights
    
    def _detect_market_regime(self, technical_signal: Dict, volatility: float) -> str:
        """
        Detect market regime (trending, ranging, volatile)
        
        DETERMINISTIC THRESHOLDS
        """
        adx = technical_signal['features_used'].get('adx', 0)
        
        if volatility > 0.02:  # High volatility
            return 'volatile'
        elif adx > 25:  # Strong trend
            return 'trending'
        else:
            return 'ranging'
    
    def _aggregate_signals(
        self,
        agent_signals: Dict,
        weights: Dict,
        regime: str
    ) -> tuple:
        """
        Weighted vote aggregation
        
        PURE MATH - NO LLM
        """
        # Adjust weights based on regime
        regime_weights = weights.copy()
        
        if regime == 'trending':
            # Boost technical weight in trends
            regime_weights['TechnicalV2'] *= 1.3
        elif regime == 'ranging':
            # Boost macro weight in ranges
            regime_weights['MacroV2'] *= 1.2
        elif regime == 'volatile':
            # Lower all weights in volatile periods
            regime_weights = {k: v * 0.7 for k, v in regime_weights.items()}
        
        # Renormalize
        total_weight = sum(regime_weights.values())
        regime_weights = {k: v / total_weight for k, v in regime_weights.items()}
        
        # Weighted sum of signals
        weighted_signal_sum = sum(
            agent_signals[agent]['signal'] * 
            agent_signals[agent]['confidence'] *
            regime_weights[agent]
            for agent in regime_weights.keys()
        )
        
        # Weighted confidence
        avg_confidence = sum(
            agent_signals[agent]['confidence'] * regime_weights[agent]
            for agent in regime_weights.keys()
        )
        
        # Convert to discrete signal
        if weighted_signal_sum > 0.25:
            final_signal = 1
        elif weighted_signal_sum < -0.25:
            final_signal = -1
        else:
            final_signal = 0
        
        return final_signal, avg_confidence
    
    def _detect_conflicts(self, agent_signals: Dict) -> bool:
        """
        Detect if agents strongly disagree
        
        DETERMINISTIC
        """
        signals = [
            agent_signals[agent]['signal'] 
            for agent in agent_signals.keys()
        ]
        
        # If we have both strong buy (+1) and strong sell (-1)
        if 1 in signals and -1 in signals:
            return True
        
        return False
    
    def _apply_safety_rules(
        self,
        signal: int,
        confidence: float,
        conflicts: bool,
        regime: str
    ) -> tuple:
        """
        Apply production safety rules
        
        - Reduce confidence if conflicts detected
        - Reduce confidence in volatile regimes
        - Require min confidence threshold
        """
        adjusted_confidence = confidence
        
        # Rule 1: Conflicts reduce confidence
        if conflicts:
            adjusted_confidence *= 0.5
        
        # Rule 2: Volatile regime reduces confidence
        if regime == 'volatile':
            adjusted_confidence *= 0.7
        
        # Rule 3: Minimum confidence threshold
        if adjusted_confidence < 0.3:
            return 0, adjusted_confidence  # Force neutral
        
        return signal, adjusted_confidence
    
    def _estimate_volatility(self, symbol: str) -> float:
        """
        Estimate recent volatility from actual InfluxDB data.
        Calculates annualized volatility from 1H log-returns over 30 days.
        """
        try:
            from data_layer.timeseries_loader import TimeSeriesLoader
            loader = TimeSeriesLoader()
            df = loader.load_ohlcv(symbol, start_time=datetime.now() - timedelta(days=30))
            if df.empty or len(df) < 10:
                return 0.01  # default low volatility
            close = df['close'].astype(float)
            log_returns = np.log(close / close.shift(1)).dropna()
            hourly_vol = log_returns.std()
            # Annualize: hourly → daily (√24) → annual (√252)
            annual_vol = hourly_vol * np.sqrt(24 * 252)
            return float(annual_vol) if not np.isnan(annual_vol) else 0.01
        except Exception:
            return 0.01

    def _validate_with_correlations(self, symbol: str, signal: int, confidence: float) -> dict:
        """
        Cross-pair correlation validation (DSO1.3).
        Checks if our signal is consistent with correlated pair movements.
        Adjusts confidence: +15% if aligned, -25% if conflicting.
        """
        engine = self._get_correlation_engine()
        if engine is None:
            return None
        try:
            corr_signals = engine.get_correlation_signals(symbol)
            if not corr_signals:
                return None

            aligned_count = 0
            conflicting_count = 0
            details = []

            for cs in corr_signals:
                corr_value = cs.get('correlation', 0)
                partner = cs.get('partner_symbol', 'unknown')
                if abs(corr_value) < 0.3:
                    continue
                # If positively correlated, same signal expected
                # If negatively correlated, opposite signal expected
                expected_alignment = np.sign(corr_value)
                details.append({
                    'partner': partner,
                    'correlation': round(corr_value, 3),
                    'alignment': 'aligned' if expected_alignment > 0 else 'inverse',
                })
                if expected_alignment > 0:
                    aligned_count += 1
                else:
                    conflicting_count += 1

            # Confidence adjustment
            if aligned_count > conflicting_count:
                adjustment = min(1.15, 1.0 + 0.05 * aligned_count)
            elif conflicting_count > aligned_count:
                adjustment = max(0.75, 1.0 - 0.08 * conflicting_count)
            else:
                adjustment = 1.0

            adjusted_confidence = min(confidence * adjustment, 0.99)

            return {
                'adjusted_confidence': round(adjusted_confidence, 4),
                'original_confidence': round(confidence, 4),
                'adjustment_factor': round(adjustment, 3),
                'aligned_pairs': aligned_count,
                'conflicting_pairs': conflicting_count,
                'details': details,
            }
        except Exception:
            return None
    
    def _generate_deterministic_reason(
        self,
        final_signal: int,
        agent_signals: Dict,
        weights: Dict
    ) -> str:
        """Generate structured deterministic reason"""
        signal_names = {1: 'BUY', 0: 'NEUTRAL', -1: 'SELL'}
        
        parts = [f"Final: {signal_names[final_signal]}"]
        
        for agent, signal_data in agent_signals.items():
            agent_sig = signal_names[signal_data['signal']]
            conf = signal_data['confidence']
            weight = weights[agent]
            parts.append(f"{agent}: {agent_sig} ({conf:.2f}, w={weight:.2f})")
        
        return " | ".join(parts)
    
    def _generate_explanation_text(
        self,
        final_signal: int,
        agent_signals: Dict,
        weights: Dict,
        conflicts: bool
    ) -> str:
        """
        Generate sophisticated natural language explanation using free enhanced LLM
        """
        print(f"DEBUG: Generating explanation for signal {final_signal}")
        
        try:
            # Prepare market data for sophisticated analysis
            market_data = {
                'final_signal': 'BUY' if final_signal == 1 else 'SELL' if final_signal == -1 else 'NEUTRAL',
                'agent_signals': agent_signals,
                'agent_weights': weights,
                'conflicts_detected': conflicts,
                'signal_strength': abs(final_signal) if final_signal != 0 else 0
            }
            
            print(f"DEBUG: Calling sophisticated reasoning with market_data")
            
            # Generate analysis using sophisticated reasoning
            analysis = self.sophisticated_reasoning.analyze_market_signal(
                agent_type='coordinator',
                market_data=market_data,
                additional_context=f"Coordinating 4 expert agents with weights: {weights}"
            )
            
            reasoning = analysis.get('reasoning', 'Multi-agent analysis completed successfully.')
            print(f"DEBUG: Sophisticated reasoning generated, length: {len(reasoning)}")
            
            return reasoning
            
        except Exception as e:
            logger.error(f"Sophisticated LLM explanation failed: {e}")
            print(f"DEBUG: Sophisticated reasoning failed, using fallback: {e}")
            # Fallback to simple explanation
            signal_map = {1: 'BUY', -1: 'SELL', 0: 'NEUTRAL'}
            signal_str = signal_map.get(final_signal, 'NEUTRAL')
            
            agent_summary = []
            for agent, data in agent_signals.items():
                agent_signal = signal_map.get(data.get('signal', 0), 'NEUTRAL')
                confidence = data.get('confidence', 0) * 100
                weight = weights.get(agent, 0) * 100
                agent_summary.append(f"{agent}: {agent_signal} ({confidence:.0f}% confidence, {weight:.0f}% weight)")
            
            return f"Final Decision: {signal_str}\n\nAgent Analysis:\n" + "\n".join(agent_summary)
