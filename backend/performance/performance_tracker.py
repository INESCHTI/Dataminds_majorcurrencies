"""
Performance Tracker for Real-time Metrics
Tracks Sharpe ratio, drawdown, win rate, and other key metrics
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class PerformanceSnapshot:
    timestamp: datetime
    account_balance: float
    total_pnl: float
    daily_return: float
    equity_curve: List[float]
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    volatility: float
    sortino_ratio: float
    calmar_ratio: float

class PerformanceTracker:
    """Real-time performance tracking and analysis"""
    
    def __init__(self, initial_balance: float = 100000.0, lookback_days: int = 30):
        self.initial_balance = initial_balance
        self.lookback_days = lookback_days
        
        # Performance data
        self.daily_returns: List[Tuple[datetime, float]] = []
        self.equity_curve: List[Tuple[datetime, float]] = []
        self.trades: List[Dict] = []
        self.snapshots: List[PerformanceSnapshot] = []
        
        # Current state
        self.current_balance = initial_balance
        self.current_positions: Dict[str, Dict] = {}
        self.total_pnl = 0.0
        
        # Performance metrics cache
        self._cached_metrics: Optional[Dict] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = timedelta(minutes=5)
    
    def update_balance(self, new_balance: float, timestamp: Optional[datetime] = None):
        """Update account balance"""
        if timestamp is None:
            timestamp = datetime.now()
        
        # Calculate daily return
        daily_return = 0.0
        if self.equity_curve:
            last_balance = self.equity_curve[-1][1]
            daily_return = ((new_balance - last_balance) / last_balance) * 100
        
        # Update state
        self.current_balance = new_balance
        self.total_pnl = new_balance - self.initial_balance
        
        # Store data
        self.equity_curve.append((timestamp, new_balance))
        self.daily_returns.append((timestamp, daily_return))
        
        # Invalidate cache
        self._cached_metrics = None
        self._cache_timestamp = None
        
        logger.debug(f"Balance updated: ${new_balance:,.2f}, Daily return: {daily_return:.2f}%")
    
    def add_trade(self, trade_data: Dict):
        """Add a completed trade to performance tracking"""
        trade = {
            'timestamp': trade_data.get('timestamp', datetime.now()),
            'symbol': trade_data['symbol'],
            'direction': trade_data['direction'],
            'entry_price': trade_data['entry_price'],
            'exit_price': trade_data['exit_price'],
            'size': trade_data['size'],
            'pnl': trade_data['pnl'],
            'commission': trade_data.get('commission', 0),
            'duration_hours': trade_data.get('duration_hours', 0),
            'entry_signal': trade_data.get('entry_signal', 'UNKNOWN'),
            'exit_reason': trade_data.get('exit_reason', 'UNKNOWN')
        }
        
        self.trades.append(trade)
        
        # Update balance
        self.update_balance(self.current_balance + trade['pnl'], trade['timestamp'])
        
        # Invalidate cache
        self._cached_metrics = None
        self._cache_timestamp = None
        
        logger.debug(f"Trade added: {trade['symbol']} {trade['direction']} P&L=${trade['pnl']:.2f}")
    
    def update_position(self, symbol: str, position_data: Dict):
        """Update current position data"""
        self.current_positions[symbol] = {
            **position_data,
            'last_updated': datetime.now()
        }
    
    def close_position(self, symbol: str, exit_price: float, timestamp: Optional[datetime] = None):
        """Close a position and record the trade"""
        if symbol not in self.current_positions:
            logger.warning(f"Position {symbol} not found for closing")
            return
        
        position = self.current_positions[symbol]
        
        # Calculate P&L
        if position['direction'] == 'BUY':
            pnl = (exit_price - position['entry_price']) * position['size']
        else:
            pnl = (position['entry_price'] - exit_price) * position['size']
        
        # Create trade record
        trade_data = {
            'symbol': symbol,
            'direction': position['direction'],
            'entry_price': position['entry_price'],
            'exit_price': exit_price,
            'size': position['size'],
            'pnl': pnl,
            'duration_hours': (timestamp or datetime.now() - position['entry_time']).total_seconds() / 3600,
            'entry_signal': position.get('signal', 'UNKNOWN'),
            'exit_reason': 'manual_close'
        }
        
        self.add_trade(trade_data)
        del self.current_positions[symbol]
    
    def get_current_metrics(self) -> Dict:
        """Get current performance metrics"""
        now = datetime.now()
        
        # Check cache
        if (self._cached_metrics and self._cache_timestamp and 
            now - self._cache_timestamp < self._cache_ttl):
            return self._cached_metrics
        
        # Calculate metrics
        metrics = self._calculate_metrics()
        
        # Create snapshot
        snapshot = PerformanceSnapshot(
            timestamp=now,
            account_balance=self.current_balance,
            total_pnl=self.total_pnl,
            daily_return=self._get_latest_daily_return(),
            equity_curve=[balance for _, balance in self.equity_curve],
            sharpe_ratio=metrics['sharpe_ratio'],
            max_drawdown=metrics['max_drawdown'],
            win_rate=metrics['win_rate'],
            profit_factor=metrics['profit_factor'],
            total_trades=metrics['total_trades'],
            winning_trades=metrics['winning_trades'],
            losing_trades=metrics['losing_trades'],
            avg_win=metrics['avg_win'],
            avg_loss=metrics['avg_loss'],
            volatility=metrics['volatility'],
            sortino_ratio=metrics['sortino_ratio'],
            calmar_ratio=metrics['calmar_ratio']
        )
        
        self.snapshots.append(snapshot)
        self._cached_metrics = metrics
        self._cache_timestamp = now
        
        return metrics
    
    def _calculate_metrics(self) -> Dict:
        """Calculate all performance metrics"""
        if not self.equity_curve:
            return self._empty_metrics()
        
        # Basic metrics
        total_return = ((self.current_balance - self.initial_balance) / self.initial_balance) * 100
        total_pnl = self.current_balance - self.initial_balance
        
        # Trade metrics
        trade_metrics = self._calculate_trade_metrics()
        
        # Risk metrics
        risk_metrics = self._calculate_risk_metrics()
        
        # Combine all metrics
        metrics = {
            **trade_metrics,
            **risk_metrics,
            'total_return': total_return,
            'total_pnl': total_pnl,
            'current_balance': self.current_balance,
            'open_positions': len(self.current_positions),
            'equity_curve_length': len(self.equity_curve),
            'trades_last_30_days': self._count_trades_last_days(30),
            'trades_last_7_days': self._count_trades_last_days(7)
        }
        
        return metrics
    
    def _calculate_trade_metrics(self) -> Dict:
        """Calculate trade-related metrics"""
        if not self.trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'avg_win_loss_ratio': 0,
                'largest_win': 0,
                'largest_loss': 0,
                'avg_trade_duration': 0
            }
        
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t['pnl'] > 0])
        losing_trades = total_trades - winning_trades
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        wins = [t['pnl'] for t in self.trades if t['pnl'] > 0]
        losses = [t['pnl'] for t in self.trades if t['pnl'] < 0]
        
        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        largest_win = max(wins) if wins else 0
        largest_loss = min(losses) if losses else 0
        
        profit_factor = sum(wins) / abs(sum(losses)) if losses else float('inf')
        avg_win_loss_ratio = avg_win / abs(avg_loss) if avg_loss != 0 else float('inf')
        
        avg_trade_duration = np.mean([t['duration_hours'] for t in self.trades])
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'avg_win_loss_ratio': avg_win_loss_ratio,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'avg_trade_duration': avg_trade_duration
        }
    
    def _calculate_risk_metrics(self) -> Dict:
        """Calculate risk-related metrics"""
        if len(self.equity_curve) < 2:
            return {
                'sharpe_ratio': 0,
                'sortino_ratio': 0,
                'calmar_ratio': 0,
                'max_drawdown': 0,
                'volatility': 0,
                'downside_deviation': 0
            }
        
        # Extract returns
        equity_values = [balance for _, balance in self.equity_curve]
        returns = np.diff(equity_values) / equity_values[:-1]
        
        # Volatility (annualized)
        trading_days_per_year = 252
        hours_per_day = 24
        volatility = np.std(returns) * np.sqrt(trading_days_per_year * hours_per_day)
        
        # Sharpe ratio
        risk_free_rate = 0.02  # 2% annual risk-free rate
        excess_returns = returns - (risk_free_rate / (trading_days_per_year * hours_per_day))
        sharpe_ratio = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(trading_days_per_year * hours_per_day) if np.std(excess_returns) > 0 else 0
        
        # Sortino ratio
        downside_returns = [r for r in returns if r < 0]
        downside_deviation = np.std(downside_returns) if downside_returns else 0
        sortino_ratio = np.mean(excess_returns) / downside_deviation * np.sqrt(trading_days_per_year * hours_per_day) if downside_deviation > 0 else 0
        
        # Calmar ratio
        max_dd = self._calculate_max_drawdown()
        total_return = (self.current_balance - self.initial_balance) / self.initial_balance
        calmar_ratio = total_return / max_dd if max_dd > 0 else 0
        
        return {
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'max_drawdown': max_dd * 100,  # Convert to percentage
            'volatility': volatility * 100,  # Convert to percentage
            'downside_deviation': downside_deviation
        }
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown"""
        if not self.equity_curve:
            return 0.0
        
        equity_values = [balance for _, balance in self.equity_curve]
        peak = np.maximum.accumulate(equity_values)
        drawdown = (peak - equity_values) / peak
        return np.max(drawdown)
    
    def _get_latest_daily_return(self) -> float:
        """Get the most recent daily return"""
        if not self.daily_returns:
            return 0.0
        return self.daily_returns[-1][1]
    
    def _count_trades_last_days(self, days: int) -> int:
        """Count trades in the last N days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        return len([t for t in self.trades if t['timestamp'] >= cutoff_date])
    
    def _empty_metrics(self) -> Dict:
        """Return empty metrics when no data available"""
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'profit_factor': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'avg_win_loss_ratio': 0,
            'largest_win': 0,
            'largest_loss': 0,
            'avg_trade_duration': 0,
            'sharpe_ratio': 0,
            'sortino_ratio': 0,
            'calmar_ratio': 0,
            'max_drawdown': 0,
            'volatility': 0,
            'downside_deviation': 0,
            'total_return': 0,
            'total_pnl': 0,
            'current_balance': self.current_balance,
            'open_positions': len(self.current_positions),
            'equity_curve_length': 0,
            'trades_last_30_days': 0,
            'trades_last_7_days': 0
        }
    
    def get_equity_curve_data(self, days: int = 30) -> List[Dict]:
        """Get equity curve data for the last N days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered_curve = [(t, b) for t, b in self.equity_curve if t >= cutoff_date]
        
        return [
            {
                'timestamp': t.isoformat(),
                'balance': b,
                'return': ((b - self.initial_balance) / self.initial_balance) * 100
            }
            for t, b in filtered_curve
        ]
    
    def get_trade_history(self, limit: int = 100) -> List[Dict]:
        """Get recent trade history"""
        recent_trades = sorted(self.trades, key=lambda x: x['timestamp'], reverse=True)[:limit]
        
        return [
            {
                **trade,
                'timestamp': trade['timestamp'].isoformat(),
                'return_pct': (trade['pnl'] / (trade['entry_price'] * trade['size'])) * 100 if trade['size'] > 0 else 0
            }
            for trade in recent_trades
        ]
    
    def get_performance_summary(self) -> Dict:
        """Get a comprehensive performance summary"""
        metrics = self.get_current_metrics()
        
        # Performance rating
        rating = self._calculate_performance_rating(metrics)
        
        # Key insights
        insights = self._generate_insights(metrics)
        
        return {
            'metrics': metrics,
            'rating': rating,
            'insights': insights,
            'summary': self._generate_summary(metrics),
            'recommendations': self._generate_recommendations(metrics)
        }
    
    def _calculate_performance_rating(self, metrics: Dict) -> str:
        """Calculate overall performance rating"""
        score = 0
        
        # Sharpe ratio (40 points)
        if metrics['sharpe_ratio'] > 2.0:
            score += 40
        elif metrics['sharpe_ratio'] > 1.5:
            score += 30
        elif metrics['sharpe_ratio'] > 1.0:
            score += 20
        elif metrics['sharpe_ratio'] > 0.5:
            score += 10
        
        # Max drawdown (20 points)
        if metrics['max_drawdown'] < 10:
            score += 20
        elif metrics['max_drawdown'] < 15:
            score += 15
        elif metrics['max_drawdown'] < 20:
            score += 10
        elif metrics['max_drawdown'] < 25:
            score += 5
        
        # Win rate (20 points)
        if metrics['win_rate'] > 60:
            score += 20
        elif metrics['win_rate'] > 55:
            score += 15
        elif metrics['win_rate'] > 50:
            score += 10
        elif metrics['win_rate'] > 45:
            score += 5
        
        # Profit factor (20 points)
        if metrics['profit_factor'] > 1.5:
            score += 20
        elif metrics['profit_factor'] > 1.3:
            score += 15
        elif metrics['profit_factor'] > 1.1:
            score += 10
        elif metrics['profit_factor'] > 1.0:
            score += 5
        
        # Rating based on score
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Fair"
        else:
            return "Poor"
    
    def _generate_insights(self, metrics: Dict) -> List[str]:
        """Generate performance insights"""
        insights = []
        
        if metrics['sharpe_ratio'] > 1.5:
            insights.append("Excellent risk-adjusted returns")
        elif metrics['sharpe_ratio'] < 0.5:
            insights.append("Low risk-adjusted returns")
        
        if metrics['max_drawdown'] > 20:
            insights.append("High drawdown detected")
        
        if metrics['win_rate'] > 60:
            insights.append("High win rate")
        elif metrics['win_rate'] < 40:
            insights.append("Low win rate")
        
        if metrics['profit_factor'] > 1.5:
            insights.append("Strong profit factor")
        elif metrics['profit_factor'] < 1.0:
            insights.append("Profit factor below 1.0")
        
        if metrics['volatility'] > 15:
            insights.append("High volatility")
        
        return insights
    
    def _generate_summary(self, metrics: Dict) -> str:
        """Generate performance summary text"""
        total_return = metrics['total_return']
        sharpe = metrics['sharpe_ratio']
        max_dd = metrics['max_drawdown']
        win_rate = metrics['win_rate']
        
        return f"""
Performance Summary:
- Total Return: {total_return:.2f}%
- Sharpe Ratio: {sharpe:.2f}
- Max Drawdown: {max_dd:.2f}%
- Win Rate: {win_rate:.1f}%
- Total Trades: {metrics['total_trades']}
"""
    
    def _generate_recommendations(self, metrics: Dict) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []
        
        if metrics['sharpe_ratio'] < 1.0:
            recommendations.append("Consider reducing position sizes to improve risk-adjusted returns")
        
        if metrics['max_drawdown'] > 20:
            recommendations.append("Implement tighter stop-losses to reduce drawdown")
        
        if metrics['win_rate'] < 45:
            recommendations.append("Review entry criteria to improve win rate")
        
        if metrics['profit_factor'] < 1.1:
            recommendations.append("Optimize take-profit levels to improve profit factor")
        
        if metrics['avg_trade_duration'] > 24:
            recommendations.append("Consider shorter holding periods for better capital efficiency")
        
        return recommendations

# Global instance for application-wide use
performance_tracker: Optional[PerformanceTracker] = None

def get_performance_tracker(initial_balance: float = 100000.0) -> PerformanceTracker:
    """Get or create global performance tracker instance"""
    global performance_tracker
    if performance_tracker is None:
        performance_tracker = PerformanceTracker(initial_balance)
    return performance_tracker
