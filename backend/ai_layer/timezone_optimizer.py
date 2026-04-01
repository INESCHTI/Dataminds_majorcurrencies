"""
Multi-Timezone Optimization with Session-Based Strategies
Optimizes trading strategies based on trading sessions and timezone characteristics
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

@dataclass
class TradingSession:
    name: str
    timezone: str
    start_hour: int  # UTC hour
    end_hour: int    # UTC hour
    major_currencies: List[str]
    characteristics: Dict[str, Any]
    volatility_multiplier: float
    volume_multiplier: float

@dataclass
class SessionPerformance:
    session_name: str
    currency_pair: str
    total_trades: int
    winning_trades: int
    avg_return: float
    sharpe_ratio: float
    max_drawdown: float
    volatility: float
    optimal_weight: float
    last_updated: datetime

class MultiTimezoneOptimizer:
    """Advanced multi-timezone trading session optimizer"""
    
    def __init__(self):
        # Define trading sessions
        self.sessions = {
            'asian': TradingSession(
                name='Asian Session',
                timezone='Asia/Tokyo',
                start_hour=23,  # 23:00 UTC (08:00 JST)
                end_hour=8,    # 08:00 UTC (17:00 JST)
                major_currencies=['JPY', 'AUD', 'NZD'],
                characteristics={
                    'liquidity': 'medium',
                    'volatility': 'low',
                    'major_pairs': ['USDJPY', 'EURJPY', 'GBPJPY', 'AUDJPY', 'NZDJPY'],
                    'cross_pairs': ['AUDJPY', 'NZDJPY', 'EURJPY', 'GBPJPY']
                },
                volatility_multiplier=0.8,
                volume_multiplier=0.7
            ),
            'london': TradingSession(
                name='London Session',
                timezone='Europe/London',
                start_hour=8,   # 08:00 UTC
                end_hour=16,   # 16:00 UTC
                major_currencies=['GBP', 'EUR'],
                characteristics={
                    'liquidity': 'high',
                    'volatility': 'high',
                    'major_pairs': ['EURUSD', 'GBPUSD', 'EURGBP', 'USDCHF'],
                    'cross_pairs': ['EURGBP', 'EURCHF', 'GBPCHF']
                },
                volatility_multiplier=1.2,
                volume_multiplier=1.5
            ),
            'new_york': TradingSession(
                name='New York Session',
                timezone='America/New_York',
                start_hour=13,  # 13:00 UTC (08:00 EST)
                end_hour=22,   # 22:00 UTC (17:00 EST)
                major_currencies=['USD', 'CAD'],
                characteristics={
                    'liquidity': 'very_high',
                    'volatility': 'very_high',
                    'major_pairs': ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD', 'USDCHF'],
                    'cross_pairs': ['EURGBP', 'EURCHF', 'GBPCHF', 'EURCAD', 'GBPCAD']
                },
                volatility_multiplier=1.4,
                volume_multiplier=1.8
            ),
            'sydney': TradingSession(
                name='Sydney Session',
                timezone='Australia/Sydney',
                start_hour=21,  # 21:00 UTC (07:00 AEST)
                end_hour=6,    # 06:00 UTC (16:00 AEST)
                major_currencies=['AUD', 'NZD'],
                characteristics={
                    'liquidity': 'low',
                    'volatility': 'low',
                    'major_pairs': ['AUDUSD', 'NZDUSD', 'AUDNZD'],
                    'cross_pairs': ['AUDNZD']
                },
                volatility_multiplier=0.6,
                volume_multiplier=0.5
            )
        }
        
        # Session overlaps (high volatility periods)
        self.session_overlaps = {
            'london_new_york': {
                'start_hour': 13,
                'end_hour': 16,
                'volatility_multiplier': 1.8,
                'volume_multiplier': 2.0,
                'description': 'London/New York overlap - Highest liquidity'
            },
            'asian_london': {
                'start_hour': 8,
                'end_hour': 9,
                'volatility_multiplier': 1.3,
                'volume_multiplier': 1.2,
                'description': 'Asian/London overlap - Moderate liquidity'
            },
            'sydney_asian': {
                'start_hour': 23,
                'end_hour': 1,
                'volatility_multiplier': 1.1,
                'volume_multiplier': 1.0,
                'description': 'Sydney/Asian overlap - Low liquidity'
            }
        }
        
        # Currency pair characteristics by session
        self.currency_session_performance: Dict[str, Dict[str, SessionPerformance]] = {}
        
        # Optimization parameters
        self.min_session_weight = 0.1
        self.max_session_weight = 0.6
        self.rebalance_threshold = 0.05  # 5% change threshold
        self.performance_window = 30  # 30 days performance window
        
        # Initialize performance tracking
        self._initialize_performance_tracking()
    
    def _initialize_performance_tracking(self):
        """Initialize performance tracking for all currency pairs and sessions"""
        major_pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'NZDUSD', 'USDCAD']
        
        for pair in major_pairs:
            self.currency_session_performance[pair] = {}
            for session_name in self.sessions.keys():
                self.currency_session_performance[pair][session_name] = SessionPerformance(
                    session_name=session_name,
                    currency_pair=pair,
                    total_trades=0,
                    winning_trades=0,
                    avg_return=0.0,
                    sharpe_ratio=0.0,
                    max_drawdown=0.0,
                    volatility=0.0,
                    optimal_weight=0.25,  # Equal weight initially
                    last_updated=datetime.now()
                )
    
    def get_current_session(self, timestamp: Optional[datetime] = None) -> List[str]:
        """Get current active trading sessions"""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        current_hour = timestamp.hour
        active_sessions = []
        
        # Check each session
        for session_name, session in self.sessions.items():
            if session.start_hour <= session.end_hour:
                # Normal session (e.g., 8-16)
                if session.start_hour <= current_hour <= session.end_hour:
                    active_sessions.append(session_name)
            else:
                # Overnight session (e.g., 23-8)
                if current_hour >= session.start_hour or current_hour <= session.end_hour:
                    active_sessions.append(session_name)
        
        return active_sessions
    
    def get_session_overlap(self, timestamp: Optional[datetime] = None) -> Optional[str]:
        """Get current session overlap"""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        current_hour = timestamp.hour
        
        for overlap_name, overlap in self.session_overlaps.items():
            if overlap['start_hour'] <= current_hour <= overlap['end_hour']:
                return overlap_name
        
        return None
    
    def get_session_characteristics(self, session_name: str, currency_pair: str) -> Dict[str, Any]:
        """Get session characteristics for a specific currency pair"""
        if session_name not in self.sessions:
            return {}
        
        session = self.sessions[session_name]
        base_currency = currency_pair[:3]
        quote_currency = currency_pair[3:]
        
        characteristics = session.characteristics.copy()
        
        # Add currency-specific characteristics
        if base_currency in session.major_currencies or quote_currency in session.major_currencies:
            characteristics['currency_relevance'] = 'high'
            characteristics['expected_spread'] = 'low'
        else:
            characteristics['currency_relevance'] = 'medium'
            characteristics['expected_spread'] = 'medium'
        
        # Add volatility and volume multipliers
        characteristics['volatility_multiplier'] = session.volatility_multiplier
        characteristics['volume_multiplier'] = session.volume_multiplier
        
        # Check for session overlap
        current_hour = datetime.now(timezone.utc).hour
        for overlap_name, overlap in self.session_overlaps.items():
            if overlap['start_hour'] <= current_hour <= overlap['end_hour']:
                characteristics['overlap'] = overlap_name
                characteristics['volatility_multiplier'] *= overlap['volatility_multiplier']
                characteristics['volume_multiplier'] *= overlap['volume_multiplier']
                break
        
        return characteristics
    
    def update_session_performance(self, currency_pair: str, session_name: str, 
                                 return_pct: float, sharpe_ratio: float, max_drawdown: float, volatility: float):
        """Update performance metrics for a currency pair in a specific session"""
        if currency_pair not in self.currency_session_performance:
            self.currency_session_performance[currency_pair] = {}
        
        if session_name not in self.currency_session_performance[currency_pair]:
            self.currency_session_performance[currency_pair][session_name] = SessionPerformance(
                session_name=session_name,
                currency_pair=currency_pair,
                total_trades=0,
                winning_trades=0,
                avg_return=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                volatility=0.0,
                optimal_weight=0.25,
                last_updated=datetime.now()
            )
        
        performance = self.currency_session_performance[currency_pair][session_name]
        
        # Update performance metrics
        performance.total_trades += 1
        if return_pct > 0:
            performance.winning_trades += 1
        
        # Update averages (exponential moving average)
        alpha = 0.1  # Smoothing factor
        performance.avg_return = performance.avg_return * (1 - alpha) + return_pct * alpha
        performance.sharpe_ratio = performance.sharpe_ratio * (1 - alpha) + sharpe_ratio * alpha
        performance.max_drawdown = performance.max_drawdown * (1 - alpha) + max_drawdown * alpha
        performance.volatility = performance.volatility * (1 - alpha) + volatility * alpha
        
        performance.last_updated = datetime.now()
    
    def optimize_session_weights(self, currency_pair: str) -> Dict[str, float]:
        """Optimize session weights for a currency pair based on performance"""
        if currency_pair not in self.currency_session_performance:
            return {session: 0.25 for session in self.sessions.keys()}
        
        performances = self.currency_session_performance[currency_pair]
        
        # Calculate performance scores
        scores = {}
        for session_name, performance in performances.items():
            if performance.total_trades >= 5:  # Need minimum trades
                # Composite score based on multiple metrics
                win_rate = performance.winning_trades / performance.total_trades
                sharpe_score = max(0, performance.sharpe_ratio / 2)  # Normalize to 0-1
                drawdown_penalty = max(0, 1 - performance.max_drawdown * 10)  # Penalize high drawdown
                
                # Session-specific adjustments
                session = self.sessions[session_name]
                session_multiplier = 1.0
                
                # Boost weights for sessions where currency is major
                base_currency = currency_pair[:3]
                quote_currency = currency_pair[3:]
                if base_currency in session.major_currencies or quote_currency in session.major_currencies:
                    session_multiplier *= 1.2
                
                # Calculate final score
                score = (win_rate * 0.4 + sharpe_score * 0.3 + drawdown_penalty * 0.3) * session_multiplier
                scores[session_name] = max(0.1, score)  # Minimum score
            else:
                scores[session_name] = 0.1  # Default score for insufficient data
        
        # Normalize scores to weights
        total_score = sum(scores.values())
        if total_score > 0:
            weights = {session: score / total_score for session, score in scores.items()}
        else:
            weights = {session: 0.25 for session in self.sessions.keys()}
        
        # Apply weight constraints
        for session in weights:
            weights[session] = max(self.min_session_weight, min(self.max_session_weight, weights[session]))
        
        # Renormalize after constraints
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {session: weight / total_weight for session, weight in weights.items()}
        
        return weights
    
    def get_session_recommendations(self, currency_pair: str, current_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get trading recommendations based on current session"""
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        active_sessions = self.get_current_session(current_time)
        overlap = self.get_session_overlap(current_time)
        
        # Get optimized weights
        session_weights = self.optimize_session_weights(currency_pair)
        
        # Build recommendations
        recommendations = {
            'current_time': current_time.isoformat(),
            'active_sessions': active_sessions,
            'session_overlap': overlap,
            'session_weights': session_weights,
            'recommendations': []
        }
        
        # Generate specific recommendations
        for session_name in active_sessions:
            weight = session_weights.get(session_name, 0.25)
            characteristics = self.get_session_characteristics(session_name, currency_pair)
            
            recommendation = {
                'session': session_name,
                'weight': weight,
                'characteristics': characteristics,
                'action': self._get_session_action(weight, characteristics),
                'risk_level': self._assess_risk_level(characteristics),
                'optimal_strategies': self._get_optimal_strategies(session_name, currency_pair)
            }
            recommendations['recommendations'].append(recommendation)
        
        # Add overlap recommendation if applicable
        if overlap:
            overlap_info = self.session_overlaps[overlap]
            recommendations['overlap_recommendation'] = {
                'overlap_name': overlap,
                'description': overlap_info['description'],
                'volatility_multiplier': overlap_info['volatility_multiplier'],
                'volume_multiplier': overlap_info['volume_multiplier'],
                'action': 'increased_position_sizing' if overlap_info['volatility_multiplier'] > 1.5 else 'normal_trading',
                'risk_adjustment': overlap_info['volatility_multiplier'] > 1.3
            }
        
        return recommendations
    
    def _get_session_action(self, weight: float, characteristics: Dict[str, Any]) -> str:
        """Get recommended action for session"""
        if weight > 0.35:
            return 'increase_position_size'
        elif weight < 0.15:
            return 'reduce_position_size_or_avoid'
        elif characteristics.get('volatility_multiplier', 1.0) > 1.5:
            return 'trade_with_caution'
        else:
            return 'normal_trading'
    
    def _assess_risk_level(self, characteristics: Dict[str, Any]) -> str:
        """Assess risk level based on session characteristics"""
        volatility_mult = characteristics.get('volatility_multiplier', 1.0)
        volume_mult = characteristics.get('volume_multiplier', 1.0)
        
        if volatility_mult > 1.5 and volume_mult > 1.5:
            return 'high'
        elif volatility_mult > 1.2 or volume_mult > 1.3:
            return 'medium'
        else:
            return 'low'
    
    def _get_optimal_strategies(self, session_name: str, currency_pair: str) -> List[str]:
        """Get optimal trading strategies for session and currency pair"""
        strategies = []
        session = self.sessions[session_name]
        base_currency = currency_pair[:3]
        quote_currency = currency_pair[3:]
        
        # Session-specific strategies
        if session_name == 'asian':
            if 'JPY' in currency_pair:
                strategies.extend(['range_trading', 'carry_trade'])
            else:
                strategies.extend(['breakout_trading', 'trend_following'])
        
        elif session_name == 'london':
            if 'GBP' in currency_pair or 'EUR' in currency_pair:
                strategies.extend(['momentum_trading', 'news_trading'])
            else:
                strategies.extend(['technical_analysis', 'support_resistance'])
        
        elif session_name == 'new_york':
            if 'USD' in currency_pair:
                strategies.extend(['economic_data_trading', 'high_volatility_trading'])
            else:
                strategies.extend(['position_management', 'profit_taking'])
        
        elif session_name == 'sydney':
            strategies.extend(['patient_trading', 'long_term_positions'])
        
        # Currency-specific strategies
        if base_currency in session.major_currencies:
            strategies.append('major_currency_focus')
        
        return list(set(strategies))  # Remove duplicates
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get comprehensive session statistics"""
        stats = {
            'session_overview': {},
            'currency_performance': {},
            'optimization_summary': {}
        }
        
        # Session overview
        for session_name, session in self.sessions.items():
            stats['session_overview'][session_name] = {
                'name': session.name,
                'timezone': session.timezone,
                'hours': f"{session.start_hour}:00 - {session.end_hour}:00 UTC",
                'major_currencies': session.major_currencies,
                'volatility_multiplier': session.volatility_multiplier,
                'volume_multiplier': session.volume_multiplier
            }
        
        # Currency performance by session
        for currency_pair, performances in self.currency_session_performance.items():
            stats['currency_performance'][currency_pair] = {}
            
            for session_name, performance in performances.items():
                if performance.total_trades > 0:
                    stats['currency_performance'][currency_pair][session_name] = {
                        'total_trades': performance.total_trades,
                        'win_rate': performance.winning_trades / performance.total_trades,
                        'avg_return': performance.avg_return,
                        'sharpe_ratio': performance.sharpe_ratio,
                        'max_drawdown': performance.max_drawdown,
                        'optimal_weight': performance.optimal_weight,
                        'last_updated': performance.last_updated.isoformat()
                    }
        
        # Optimization summary
        total_trades = sum(
            perf.total_trades 
            for performances in self.currency_session_performance.values() 
            for perf in performances.values()
        )
        
        stats['optimization_summary'] = {
            'total_currency_pairs': len(self.currency_session_performance),
            'total_trades_analyzed': total_trades,
            'active_sessions': self.get_current_session(),
            'current_overlap': self.get_session_overlap(),
            'last_optimization': datetime.now().isoformat()
        }
        
        return stats
    
    def create_session_schedule(self, currency_pair: str, days: int = 7) -> pd.DataFrame:
        """Create trading schedule for currency pair"""
        schedule_data = []
        
        for day in range(days):
            date = datetime.now(timezone.utc) + timedelta(days=day)
            
            # Check each hour of the day
            for hour in range(24):
                timestamp = date.replace(hour=hour, minute=0, second=0, microsecond=0)
                active_sessions = self.get_current_session(timestamp)
                overlap = self.get_session_overlap(timestamp)
                
                if active_sessions:
                    # Get session characteristics
                    characteristics = {}
                    for session in active_sessions:
                        characteristics[session] = self.get_session_characteristics(session, currency_pair)
                    
                    # Get recommendations
                    recommendations = self.get_session_recommendations(currency_pair, timestamp)
                    
                    schedule_data.append({
                        'timestamp': timestamp,
                        'hour': hour,
                        'active_sessions': ', '.join(active_sessions),
                        'session_overlap': overlap or 'None',
                        'volatility_multiplier': max([c.get('volatility_multiplier', 1.0) for c in characteristics.values()], default=1.0),
                        'volume_multiplier': max([c.get('volume_multiplier', 1.0) for c in characteristics.values()], default=1.0),
                        'recommended_action': recommendations['recommendations'][0]['action'] if recommendations['recommendations'] else 'normal_trading',
                        'risk_level': recommendations['recommendations'][0]['risk_level'] if recommendations['recommendations'] else 'low'
                    })
        
        return pd.DataFrame(schedule_data)
    
    def reset_performance_tracking(self):
        """Reset all performance tracking"""
        self._initialize_performance_tracking()
        logger.info("Multi-timezone performance tracking reset")

# Factory function
def create_timezone_optimizer() -> MultiTimezoneOptimizer:
    """Create multi-timezone optimizer"""
    return MultiTimezoneOptimizer()
