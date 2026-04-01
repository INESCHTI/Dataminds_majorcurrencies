"""
Reinforcement Learning for Agent Weight Optimization
Uses RL to dynamically optimize multi-agent signal weights based on performance
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging
from collections import deque
import random
import json

logger = logging.getLogger(__name__)

@dataclass
class AgentPerformance:
    agent_name: str
    performance_history: List[float]
    current_weight: float
    last_update: datetime
    success_rate: float
    avg_confidence: float
    volatility: float

@dataclass
class RLReward:
    timestamp: datetime
    agent_weights: Dict[str, float]
    portfolio_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    reward: float

class ReinforcementLearningOptimizer:
    """RL-based agent weight optimizer using Q-learning"""
    
    def __init__(self, learning_rate: float = 0.1, discount_factor: float = 0.95, 
                 exploration_rate: float = 0.1, memory_size: int = 1000):
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = exploration_rate
        self.memory_size = memory_size
        
        # Agent tracking
        self.agents: Dict[str, AgentPerformance] = {}
        self.initial_weights = {
            'technical': 0.30,
            'macro': 0.25,
            'sentiment': 0.20,
            'geopolitical': 0.25
        }
        
        # Q-learning state
        self.q_table: Dict[str, np.ndarray] = {}
        self.state_history: deque = deque(maxlen=memory_size)
        self.reward_history: List[RLReward] = []
        
        # Performance tracking
        self.portfolio_returns: List[float] = []
        self.optimization_rounds = 0
        self.last_optimization = datetime.now()
        
        # RL parameters
        self.weight_adjustment_step = 0.05  # 5% adjustment per step
        self.min_weight = 0.05  # Minimum 5% weight per agent
        self.max_weight = 0.50  # Maximum 50% weight per agent
        
        # Initialize Q-table
        self._initialize_q_table()
    
    def _initialize_q_table(self):
        """Initialize Q-learning table"""
        # State discretization: performance ranges
        performance_bins = [-1.0, -0.5, -0.2, 0.0, 0.2, 0.5, 1.0]
        state_size = len(performance_bins) - 1
        
        # Actions: weight adjustments for each agent
        actions = ['increase', 'decrease', 'maintain']
        action_size = len(actions)
        
        # Initialize Q-table for each agent
        for agent in self.initial_weights.keys():
            self.q_table[agent] = np.random.uniform(-0.1, 0.1, (state_size, action_size))
    
    def update_agent_performance(self, agent_name: str, performance: float, confidence: float):
        """Update individual agent performance"""
        if agent_name not in self.agents:
            self.agents[agent_name] = AgentPerformance(
                agent_name=agent_name,
                performance_history=[],
                current_weight=self.initial_weights.get(agent_name, 0.25),
                last_update=datetime.now(),
                success_rate=0.0,
                avg_confidence=0.0,
                volatility=0.0
            )
        
        agent = self.agents[agent_name]
        agent.performance_history.append(performance)
        agent.last_update = datetime.now()
        
        # Keep only last 50 performances
        if len(agent.performance_history) > 50:
            agent.performance_history = agent.performance_history[-50:]
        
        # Update statistics
        if len(agent.performance_history) > 5:
            agent.success_rate = len([p for p in agent.performance_history if p > 0]) / len(agent.performance_history)
            agent.avg_confidence = (agent.avg_confidence * 0.8 + confidence * 0.2)  # EMA
            agent.volatility = np.std(agent.performance_history) if len(agent.performance_history) > 1 else 0.0
    
    def get_current_weights(self) -> Dict[str, float]:
        """Get current agent weights"""
        return {agent: perf.current_weight for agent, perf in self.agents.items()}
    
    def optimize_weights(self, portfolio_return: float, sharpe_ratio: float, max_drawdown: float, win_rate: float) -> Dict[str, float]:
        """Optimize agent weights using RL"""
        try:
            # Calculate reward
            reward = self._calculate_reward(portfolio_return, sharpe_ratio, max_drawdown, win_rate)
            
            # Store reward
            reward_record = RLReward(
                timestamp=datetime.now(),
                agent_weights=self.get_current_weights(),
                portfolio_return=portfolio_return,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                win_rate=win_rate,
                reward=reward
            )
            self.reward_history.append(reward_record)
            
            # Get current state
            current_state = self._get_state()
            
            # Choose action (exploration vs exploitation)
            if random.random() < self.exploration_rate:
                action = self._choose_random_action()
            else:
                action = self._choose_best_action(current_state)
            
            # Execute action (adjust weights)
            new_weights = self._execute_action(action)
            
            # Update Q-table
            if len(self.reward_history) > 1:
                self._update_q_table(current_state, action, reward)
            
            # Normalize weights
            new_weights = self._normalize_weights(new_weights)
            
            # Update agent weights
            for agent, weight in new_weights.items():
                if agent in self.agents:
                    self.agents[agent].current_weight = weight
            
            # Update tracking
            self.optimization_rounds += 1
            self.last_optimization = datetime.now()
            self.portfolio_returns.append(portfolio_return)
            
            logger.info(f"RL Optimization Round {self.optimization_rounds}: Reward={reward:.4f}, New weights={new_weights}")
            
            return new_weights
            
        except Exception as e:
            logger.error(f"Error in RL optimization: {e}")
            return self.get_current_weights()
    
    def _calculate_reward(self, portfolio_return: float, sharpe_ratio: float, max_drawdown: float, win_rate: float) -> float:
        """Calculate reward for RL agent"""
        # Base reward from portfolio return
        reward = portfolio_return * 10  # Scale returns
        
        # Bonus for high Sharpe ratio
        if sharpe_ratio > 1.0:
            reward += (sharpe_ratio - 1.0) * 5
        
        # Penalty for high drawdown
        if max_drawdown > 0.1:  # 10% drawdown
            reward -= max_drawdown * 20
        
        # Bonus for high win rate
        if win_rate > 0.6:  # 60% win rate
            reward += (win_rate - 0.6) * 10
        
        # Penalty for extreme weight changes (stability bonus)
        if len(self.reward_history) > 1:
            prev_weights = self.reward_history[-1].agent_weights
            current_weights = self.get_current_weights()
            weight_change = sum(abs(current_weights.get(agent, 0) - prev_weights.get(agent, 0)) for agent in current_weights)
            reward -= weight_change * 2  # Penalty for large changes
        
        return reward
    
    def _get_state(self) -> str:
        """Get current state representation"""
        if not self.agents:
            return "neutral"
        
        # Calculate overall performance metrics
        avg_performance = np.mean([np.mean(perf.performance_history[-5:]) if len(perf.performance_history) >= 5 else 0 for perf in self.agents.values()])
        
        # Discretize performance into state
        if avg_performance > 0.5:
            return "excellent"
        elif avg_performance > 0.2:
            return "good"
        elif avg_performance > 0.0:
            return "moderate"
        elif avg_performance > -0.2:
            return "poor"
        else:
            return "terrible"
    
    def _choose_random_action(self) -> Dict[str, str]:
        """Choose random action for exploration"""
        actions = ['increase', 'decrease', 'maintain']
        return {agent: random.choice(actions) for agent in self.agents.keys()}
    
    def _choose_best_action(self, state: str) -> Dict[str, str]:
        """Choose best action based on Q-table"""
        actions = ['increase', 'decrease', 'maintain']
        best_actions = {}
        
        state_index = self._state_to_index(state)
        
        for agent in self.agents.keys():
            if agent in self.q_table:
                q_values = self.q_table[agent][state_index]
                best_action_index = np.argmax(q_values)
                best_actions[agent] = actions[best_action_index]
            else:
                best_actions[agent] = 'maintain'
        
        return best_actions
    
    def _state_to_index(self, state: str) -> int:
        """Convert state string to index"""
        state_mapping = {
            'terrible': 0,
            'poor': 1,
            'moderate': 2,
            'good': 3,
            'excellent': 4
        }
        return state_mapping.get(state, 2)
    
    def _execute_action(self, actions: Dict[str, str]) -> Dict[str, float]:
        """Execute actions to adjust weights"""
        new_weights = {}
        
        for agent, action in actions.items():
            if agent not in self.agents:
                continue
            
            current_weight = self.agents[agent].current_weight
            
            if action == 'increase':
                new_weight = current_weight + self.weight_adjustment_step
            elif action == 'decrease':
                new_weight = current_weight - self.weight_adjustment_step
            else:  # maintain
                new_weight = current_weight
            
            # Apply bounds
            new_weight = max(self.min_weight, min(self.max_weight, new_weight))
            new_weights[agent] = new_weight
        
        return new_weights
    
    def _normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """Normalize weights to sum to 1.0"""
        total_weight = sum(weights.values())
        
        if total_weight == 0:
            return self.initial_weights
        
        normalized = {agent: weight / total_weight for agent, weight in weights.items()}
        
        # Ensure minimum weights
        for agent in normalized:
            if normalized[agent] < self.min_weight:
                # Redistribute excess weight
                excess = self.min_weight - normalized[agent]
                normalized[agent] = self.min_weight
                
                # Distribute excess to other agents
                other_agents = [a for a in normalized if a != agent]
                if other_agents:
                    for other_agent in other_agents:
                        normalized[other_agent] -= excess / len(other_agents)
        
        # Final normalization
        total_weight = sum(normalized.values())
        if total_weight > 0:
            normalized = {agent: weight / total_weight for agent, weight in normalized.items()}
        
        return normalized
    
    def _update_q_table(self, state: str, action: Dict[str, str], reward: float):
        """Update Q-table using Q-learning"""
        state_index = self._state_to_index(state)
        actions = ['increase', 'decrease', 'maintain']
        
        for agent, chosen_action in action.items():
            if agent not in self.q_table:
                continue
            
            action_index = actions.index(chosen_action)
            
            # Current Q-value
            current_q = self.q_table[agent][state_index, action_index]
            
            # Estimate future reward (simplified)
            future_reward = reward * self.discount_factor
            
            # Q-learning update
            new_q = current_q + self.learning_rate * (future_reward - current_q)
            self.q_table[agent][state_index, action_index] = new_q
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics"""
        if not self.reward_history:
            return {
                'optimization_rounds': 0,
                'avg_reward': 0.0,
                'best_reward': 0.0,
                'current_weights': self.initial_weights,
                'performance_trend': 'stable'
            }
        
        rewards = [r.reward for r in self.reward_history]
        recent_rewards = rewards[-10:] if len(rewards) >= 10 else rewards
        
        # Calculate performance trend
        if len(recent_rewards) >= 5:
            early_avg = np.mean(recent_rewards[:len(recent_rewards)//2])
            late_avg = np.mean(recent_rewards[len(recent_rewards)//2:])
            
            if late_avg > early_avg * 1.1:
                trend = 'improving'
            elif late_avg < early_avg * 0.9:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
        
        return {
            'optimization_rounds': self.optimization_rounds,
            'avg_reward': np.mean(rewards),
            'best_reward': max(rewards),
            'current_weights': self.get_current_weights(),
            'performance_trend': trend,
            'recent_avg_reward': np.mean(recent_rewards),
            'agent_performances': {
                agent: {
                    'success_rate': perf.success_rate,
                    'avg_confidence': perf.avg_confidence,
                    'volatility': perf.volatility,
                    'current_weight': perf.current_weight
                }
                for agent, perf in self.agents.items()
            }
        }
    
    def reset_optimization(self):
        """Reset optimization state"""
        self.agents.clear()
        self.reward_history.clear()
        self.portfolio_returns.clear()
        self.optimization_rounds = 0
        self.last_optimization = datetime.now()
        self._initialize_q_table()
        
        logger.info("RL optimization reset")

class AdvancedWeightOptimizer:
    """Advanced weight optimizer with multiple strategies"""
    
    def __init__(self):
        self.rl_optimizer = ReinforcementLearningOptimizer()
        self.optimization_strategies = {
            'rl': self.rl_optimizer.optimize_weights,
            'performance_based': self._performance_based_optimization,
            'volatility_adjusted': self._volatility_adjusted_optimization,
            'momentum_based': self._momentum_based_optimization
        }
        self.current_strategy = 'rl'
        self.strategy_performance: Dict[str, List[float]] = {strategy: [] for strategy in self.optimization_strategies}
    
    def optimize_weights(self, strategy: str = 'rl', **kwargs) -> Dict[str, float]:
        """Optimize weights using specified strategy"""
        if strategy not in self.optimization_strategies:
            strategy = 'rl'
        
        self.current_strategy = strategy
        
        try:
            weights = self.optimization_strategies[strategy](**kwargs)
            
            # Track strategy performance
            portfolio_return = kwargs.get('portfolio_return', 0.0)
            self.strategy_performance[strategy].append(portfolio_return)
            
            # Auto-switch strategy if current one underperforms
            self._evaluate_strategy_performance()
            
            return weights
            
        except Exception as e:
            logger.error(f"Error in {strategy} optimization: {e}")
            return self.rl_optimizer.get_current_weights()
    
    def _performance_based_optimization(self, **kwargs) -> Dict[str, float]:
        """Optimize based on recent performance"""
        if not self.rl_optimizer.agents:
            return self.rl_optimizer.get_current_weights()
        
        # Calculate performance scores
        scores = {}
        for agent, perf in self.rl_optimizer.agents.items():
            if len(perf.performance_history) >= 5:
                recent_perf = np.mean(perf.performance_history[-5:])
                confidence_bonus = perf.avg_confidence * 0.1
                volatility_penalty = perf.volatility * 0.05
                
                score = recent_perf + confidence_bonus - volatility_penalty
                scores[agent] = max(0.1, score)  # Ensure positive scores
            else:
                scores[agent] = 0.1
        
        # Convert scores to weights
        total_score = sum(scores.values())
        if total_score > 0:
            weights = {agent: score / total_score for agent, score in scores.items()}
        else:
            weights = self.rl_optimizer.initial_weights
        
        return weights
    
    def _volatility_adjusted_optimization(self, **kwargs) -> Dict[str, float]:
        """Optimize with volatility adjustment"""
        if not self.rl_optimizer.agents:
            return self.rl_optimizer.get_current_weights()
        
        # Calculate volatility-adjusted performance
        adjusted_scores = {}
        for agent, perf in self.rl_optimizer.agents.items():
            if len(perf.performance_history) >= 10:
                recent_perf = np.mean(perf.performance_history[-10:])
                volatility = perf.volatility
                
                # Adjust performance by volatility (lower volatility = higher score)
                if volatility > 0:
                    adjusted_score = recent_perf / (1 + volatility)
                else:
                    adjusted_score = recent_perf
                
                adjusted_scores[agent] = max(0.1, adjusted_score)
            else:
                adjusted_scores[agent] = 0.1
        
        # Convert to weights
        total_score = sum(adjusted_scores.values())
        if total_score > 0:
            weights = {agent: score / total_score for agent, score in adjusted_scores.items()}
        else:
            weights = self.rl_optimizer.initial_weights
        
        return weights
    
    def _momentum_based_optimization(self, **kwargs) -> Dict[str, float]:
        """Optimize based on performance momentum"""
        if not self.rl_optimizer.agents:
            return self.rl_optimizer.get_current_weights()
        
        momentum_scores = {}
        for agent, perf in self.rl_optimizer.agents.items():
            if len(perf.performance_history) >= 10:
                recent_performances = perf.performance_history[-10:]
                
                # Calculate momentum (recent trend)
                if len(recent_performances) >= 5:
                    early_avg = np.mean(recent_performances[:5])
                    late_avg = np.mean(recent_performances[5:])
                    momentum = (late_avg - early_avg) / abs(early_avg) if early_avg != 0 else 0
                    
                    # Combine momentum with recent performance
                    recent_avg = np.mean(recent_performances)
                    momentum_score = recent_avg + momentum * 0.5
                    
                    momentum_scores[agent] = max(0.1, momentum_score)
                else:
                    momentum_scores[agent] = 0.1
            else:
                momentum_scores[agent] = 0.1
        
        # Convert to weights
        total_score = sum(momentum_scores.values())
        if total_score > 0:
            weights = {agent: score / total_score for agent, score in momentum_scores.items()}
        else:
            weights = self.rl_optimizer.initial_weights
        
        return weights
    
    def _evaluate_strategy_performance(self):
        """Evaluate and potentially switch optimization strategy"""
        if len(self.strategy_performance[self.current_strategy]) < 10:
            return
        
        # Compare current strategy performance with others
        current_performance = np.mean(self.strategy_performance[self.current_strategy][-10:])
        
        for strategy, performances in self.strategy_performance.items():
            if strategy != self.current_strategy and len(performances) >= 10:
                strategy_performance = np.mean(performances[-10:])
                
                # Switch if other strategy performs significantly better
                if strategy_performance > current_performance * 1.2:  # 20% better
                    logger.info(f"Switching optimization strategy from {self.current_strategy} to {strategy}")
                    self.current_strategy = strategy
                    break
    
    def get_optimizer_stats(self) -> Dict[str, Any]:
        """Get comprehensive optimizer statistics"""
        rl_stats = self.rl_optimizer.get_optimization_stats()
        
        return {
            'current_strategy': self.current_strategy,
            'strategy_performance': {
                strategy: {
                    'avg_performance': np.mean(perfs) if perfs else 0.0,
                    'recent_performance': np.mean(perfs[-5:]) if len(perfs) >= 5 else 0.0,
                    'sample_size': len(perfs)
                }
                for strategy, perfs in self.strategy_performance.items()
            },
            'rl_stats': rl_stats,
            'available_strategies': list(self.optimization_strategies.keys())
        }

# Factory functions
def create_rl_optimizer() -> ReinforcementLearningOptimizer:
    """Create RL weight optimizer"""
    return ReinforcementLearningOptimizer()

def create_advanced_optimizer() -> AdvancedWeightOptimizer:
    """Create advanced weight optimizer"""
    return AdvancedWeightOptimizer()
