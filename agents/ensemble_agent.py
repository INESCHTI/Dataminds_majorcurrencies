"""
Ensemble Agent (DSO2.1)
Combines signals from multiple agents using weighted voting and conflict resolution
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime
from .base_agent import BaseAgent, Signal
from .technical_agent import TechnicalAgent
from .fundamental_agent import FundamentalAgent
from .sentiment_agent import SentimentAgent


class EnsembleAgent:
    """
    Ensemble System for Multi-Agent Decision Making
    Combines signals from Technical, Fundamental, and Sentiment agents
    Implements weighted voting and conflict resolution (DSO2.2)
    """
    
    def __init__(self,
                 technical_agent: Optional[TechnicalAgent] = None,
                 fundamental_agent: Optional[FundamentalAgent] = None,
                 sentiment_agent: Optional[SentimentAgent] = None,
                 voting_method: str = 'weighted',
                 conflict_resolution: str = 'confidence',
                 min_confidence_threshold: float = 0.3):
        """
        Initialize Ensemble Agent
        
        Args:
            technical_agent: Technical analysis agent
            fundamental_agent: Fundamental analysis agent
            sentiment_agent: Sentiment analysis agent
            voting_method: 'weighted', 'majority', or 'unanimous'
            conflict_resolution: 'confidence' or 'priority'
            min_confidence_threshold: Minimum confidence to act on signal
        """
        self.technical_agent = technical_agent or TechnicalAgent()
        self.fundamental_agent = fundamental_agent or FundamentalAgent()
        self.sentiment_agent = sentiment_agent or SentimentAgent()
        
        self.agents = [
            self.technical_agent,
            self.fundamental_agent,
            self.sentiment_agent
        ]
        
        self.voting_method = voting_method
        self.conflict_resolution = conflict_resolution
        self.min_confidence_threshold = min_confidence_threshold
        
        self.ensemble_signals_history: List[Dict] = []
    
    def weighted_voting(self, signals: List[Signal]) -> Dict:
        """
        Combine signals using weighted voting
        
        Args:
            signals: List of Signal objects from different agents
            
        Returns:
            Dictionary with ensemble decision
        """
        if not signals:
            return {
                'direction': 'HOLD',
                'confidence': 0.0,
                'reasoning': 'No signals available'
            }
        
        # Calculate weighted scores for each direction
        buy_score = 0.0
        sell_score = 0.0
        hold_score = 0.0
        
        weights_sum = sum(agent.weight for agent in self.agents)
        
        reasoning_parts = []
        
        for signal in signals:
            agent = next((a for a in self.agents if a.name == signal.agent_name), None)
            if not agent:
                continue
            
            weighted_confidence = signal.confidence * agent.weight
            
            if signal.direction == 'BUY':
                buy_score += weighted_confidence
                reasoning_parts.append(
                    f"{signal.agent_name}: BUY ({signal.confidence:.2f})"
                )
            elif signal.direction == 'SELL':
                sell_score += weighted_confidence
                reasoning_parts.append(
                    f"{signal.agent_name}: SELL ({signal.confidence:.2f})"
                )
            else:  # HOLD
                hold_score += weighted_confidence
                reasoning_parts.append(
                    f"{signal.agent_name}: HOLD ({signal.confidence:.2f})"
                )
        
        # Normalize scores
        total_score = buy_score + sell_score + hold_score
        if total_score > 0:
            buy_score /= weights_sum
            sell_score /= weights_sum
            hold_score /= weights_sum
        
        # Determine final direction
        max_score = max(buy_score, sell_score, hold_score)
        
        if max_score == buy_score and buy_score > self.min_confidence_threshold:
            direction = 'BUY'
            confidence = buy_score
        elif max_score == sell_score and sell_score > self.min_confidence_threshold:
            direction = 'SELL'
            confidence = sell_score
        else:
            direction = 'HOLD'
            confidence = hold_score if hold_score > 0 else 0.5
        
        reasoning = f"Ensemble {self.voting_method} voting: " + " | ".join(reasoning_parts)
        
        return {
            'direction': direction,
            'confidence': confidence,
            'reasoning': reasoning,
            'buy_score': float(buy_score),
            'sell_score': float(sell_score),
            'hold_score': float(hold_score),
            'individual_signals': [s.to_dict() for s in signals]
        }
    
    def majority_voting(self, signals: List[Signal]) -> Dict:
        """
        Simple majority voting (each agent gets one vote)
        
        Args:
            signals: List of Signal objects
            
        Returns:
            Dictionary with ensemble decision
        """
        if not signals:
            return {
                'direction': 'HOLD',
                'confidence': 0.0,
                'reasoning': 'No signals available'
            }
        
        buy_votes = sum(1 for s in signals if s.direction == 'BUY')
        sell_votes = sum(1 for s in signals if s.direction == 'SELL')
        hold_votes = sum(1 for s in signals if s.direction == 'HOLD')
        
        total_votes = len(signals)
        
        if buy_votes > sell_votes and buy_votes > hold_votes:
            direction = 'BUY'
            confidence = buy_votes / total_votes
        elif sell_votes > buy_votes and sell_votes > hold_votes:
            direction = 'SELL'
            confidence = sell_votes / total_votes
        else:
            direction = 'HOLD'
            confidence = hold_votes / total_votes if hold_votes > 0 else 0.5
        
        # Calculate average confidence from supporting signals
        supporting_signals = [s for s in signals if s.direction == direction]
        if supporting_signals:
            avg_confidence = np.mean([s.confidence for s in supporting_signals])
            confidence = (confidence + avg_confidence) / 2
        
        reasoning_parts = [
            f"{s.agent_name}: {s.direction}" for s in signals
        ]
        reasoning = f"Majority vote ({buy_votes}B/{sell_votes}S/{hold_votes}H): " + " | ".join(reasoning_parts)
        
        return {
            'direction': direction,
            'confidence': confidence,
            'reasoning': reasoning,
            'buy_votes': buy_votes,
            'sell_votes': sell_votes,
            'hold_votes': hold_votes,
            'individual_signals': [s.to_dict() for s in signals]
        }
    
    def resolve_conflicts(self, signals: List[Signal]) -> Signal:
        """
        Resolve conflicts when agents disagree (DSO2.2)
        
        Args:
            signals: List of conflicting signals
            
        Returns:
            Resolved Signal
        """
        if not signals:
            return Signal(
                timestamp=datetime.now(),
                symbol='',
                direction='HOLD',
                confidence=0.0,
                agent_name='Ensemble',
                reasoning='No signals to resolve',
                indicators={}
            )
        
        # Check for unanimous agreement
        directions = [s.direction for s in signals]
        if len(set(directions)) == 1:
            # All agents agree - high confidence
            avg_confidence = np.mean([s.confidence for s in signals])
            return signals[0]  # Return first signal with averaged confidence
        
        # Conflict detected - apply resolution strategy
        if self.conflict_resolution == 'confidence':
            # Choose signal with highest confidence
            best_signal = max(signals, key=lambda s: s.confidence * s.agent_name)
            return best_signal
        
        elif self.conflict_resolution == 'priority':
            # Priority order: Fundamental > Technical > Sentiment
            priority_order = ['Fundamental Agent', 'Technical Agent', 'Sentiment Agent']
            for agent_name in priority_order:
                agent_signal = next((s for s in signals if s.agent_name == agent_name), None)
                if agent_signal and agent_signal.direction != 'HOLD':
                    return agent_signal
            return signals[0]  # Default to first signal
        
        return signals[0]
    
    def analyze(self, 
                symbol: str,
                forex_data: Optional[pd.DataFrame] = None,
                economic_data: Optional[pd.DataFrame] = None,
                news_data: Optional[pd.DataFrame] = None) -> Dict:
        """
        Run ensemble analysis combining all agents
        
        Args:
            symbol: Currency pair (e.g., 'EURUSD')
            forex_data: OHLC price data for technical analysis
            economic_data: Economic indicators for fundamental analysis
            news_data: News articles for sentiment analysis
            
        Returns:
            Dictionary with ensemble decision and metadata
        """
        signals = []
        
        # Technical Analysis
        try:
            if forex_data is not None and not forex_data.empty:
                tech_signal = self.technical_agent.analyze(symbol, forex_data)
                signals.append(tech_signal)
        except Exception as e:
            print(f"Technical agent error: {e}")
        
        # Fundamental Analysis
        try:
            fund_signal = self.fundamental_agent.analyze(symbol, economic_data)
            signals.append(fund_signal)
        except Exception as e:
            print(f"Fundamental agent error: {e}")
        
        # Sentiment Analysis
        try:
            sent_signal = self.sentiment_agent.analyze(symbol, news_data)
            signals.append(sent_signal)
        except Exception as e:
            print(f"Sentiment agent error: {e}")
        
        # Combine signals based on voting method
        if self.voting_method == 'weighted':
            ensemble_result = self.weighted_voting(signals)
        elif self.voting_method == 'majority':
            ensemble_result = self.majority_voting(signals)
        else:
            ensemble_result = self.weighted_voting(signals)
        
        # Add metadata
        ensemble_result['timestamp'] = datetime.now().isoformat()
        ensemble_result['symbol'] = symbol
        ensemble_result['voting_method'] = self.voting_method
        ensemble_result['num_agents'] = len(signals)
        
        # Record in history
        self.ensemble_signals_history.append(ensemble_result)
        
        return ensemble_result
    
    def get_ensemble_performance(self) -> Dict:
        """
        Calculate ensemble performance metrics
        
        Returns:
            Dictionary of performance metrics
        """
        if not self.ensemble_signals_history:
            return {
                'total_signals': 0,
                'avg_confidence': 0.0,
                'agreement_rate': 0.0
            }
        
        total = len(self.ensemble_signals_history)
        avg_conf = np.mean([s['confidence'] for s in self.ensemble_signals_history])
        
        # Calculate agreement rate (all agents with same direction)
        agreement_count = 0
        for result in self.ensemble_signals_history:
            if 'individual_signals' in result:
                directions = [s['direction'] for s in result['individual_signals']]
                if len(set(directions)) == 1:
                    agreement_count += 1
        
        agreement_rate = agreement_count / total if total > 0 else 0.0
        
        return {
            'total_signals': total,
            'avg_confidence': avg_conf,
            'agreement_rate': agreement_rate,
            'technical_performance': self.technical_agent.get_performance(),
            'fundamental_performance': self.fundamental_agent.get_performance(),
            'sentiment_performance': self.sentiment_agent.get_performance()
        }
    
    def __repr__(self) -> str:
        return (f"EnsembleAgent(agents={len(self.agents)}, "
                f"method={self.voting_method}, "
                f"threshold={self.min_confidence_threshold})")
