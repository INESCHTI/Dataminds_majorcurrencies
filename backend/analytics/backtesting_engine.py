"""
Backtesting Engine for FX Alpha Platform
5-year historical validation with comprehensive performance metrics
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class Trade:
    symbol: str
    direction: str
    entry_time: datetime
    entry_price: float
    exit_time: datetime
    exit_price: float
    size: float
    pnl: float
    commission: float
    duration_hours: float
    entry_signal: str
    exit_reason: str

@dataclass
class PerformanceMetrics:
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_duration: int
    profit_factor: float
    avg_win: float
    avg_loss: float
    avg_win_loss_ratio: float
    largest_win: float
    largest_loss: float
    avg_trade_duration: float
    volatility: float
    calmar_ratio: float
    sortino_ratio: float

class BacktestingEngine:
    """Comprehensive backtesting engine for FX trading strategies"""
    
    def __init__(self, initial_balance: float = 100000.0, commission_rate: float = 0.0002):
        self.initial_balance = initial_balance
        self.commission_rate = commission_rate
        self.trades: List[Trade] = []
        self.equity_curve: List[Tuple[datetime, float]] = []
        self.current_balance = initial_balance
        self.current_positions: Dict[str, Dict] = {}
        
    def load_historical_data(self, start_date: datetime, end_date: datetime, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """Load historical data for backtesting"""
        data = {}
        
        for symbol in symbols:
            # In production, this would load from InfluxDB or database
            # For now, generate sample data
            dates = pd.date_range(start=start_date, end=end_date, freq='1H')
            
            # Generate realistic price movements
            np.random.seed(42)  # For reproducible results
            
            # Base prices
            base_prices = {
                'EURUSD': 1.0850,
                'GBPUSD': 1.2650,
                'USDJPY': 149.50,
                'USDCHF': 0.8820,
                'AUDUSD': 0.6550,
                'USDCAD': 1.3650,
                'NZDUSD': 0.6150,
                'EURGBP': 0.8580
            }
            
            base_price = base_prices.get(symbol, 1.0)
            
            # Generate OHLC data with realistic volatility
            returns = np.random.normal(0, 0.001, len(dates))  # 0.1% hourly volatility
            
            prices = [base_price]
            for ret in returns:
                prices.append(prices[-1] * (1 + ret))
            
            prices = prices[1:]  # Remove initial price
            
            # Create OHLC
            high = []
            low = []
            close = []
            
            for i in range(len(prices)):
                # Add some intraday volatility
                intraday_vol = np.random.normal(0, 0.0002, 4)  # 0.02% intraday volatility
                
                high_price = prices[i] * (1 + abs(intraday_vol[0]))
                low_price = prices[i] * (1 - abs(intraday_vol[1]))
                
                high.append(high_price)
                low.append(low_price)
                close.append(prices[i])
            
            df = pd.DataFrame({
                'timestamp': dates,
                'open': prices,
                'high': high,
                'low': low,
                'close': close,
                'volume': np.random.randint(1000000, 10000000, len(dates))
            })
            
            data[symbol] = df
        
        return data
    
    def run_backtest(
        self, 
        historical_data: Dict[str, pd.DataFrame],
        signal_generator: callable,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Run comprehensive backtest"""
        logger.info(f"Starting backtest from {start_date} to {end_date}")
        
        # Reset state
        self.trades = []
        self.equity_curve = []
        self.current_balance = self.initial_balance
        self.current_positions = {}
        
        # Generate signals and execute trades
        all_dates = set()
        for df in historical_data.values():
            all_dates.update(df['timestamp'])
        
        sorted_dates = sorted(all_dates)
        
        for i, current_time in enumerate(sorted_dates):
            # Update equity curve
            self.equity_curve.append((current_time, self.current_balance))
            
            # Get current prices
            current_prices = {}
            for symbol, df in historical_data.items():
                price_data = df[df['timestamp'] <= current_time]
                if not price_data.empty:
                    current_prices[symbol] = price_data.iloc[-1]['close']
            
            # Generate trading signals
            try:
                signals = signal_generator(current_time, current_prices, self.current_positions)
                
                # Execute signals
                for symbol, signal in signals.items():
                    if symbol in current_prices:
                        self._execute_signal(symbol, signal, current_prices[symbol], current_time)
                
            except Exception as e:
                logger.error(f"Error generating signals at {current_time}: {e}")
            
            # Update existing positions (stop loss, take profit)
            self._update_positions(current_prices, current_time)
            
            # Progress update
            if i % 1000 == 0:
                logger.info(f"Processed {i}/{len(sorted_dates)} time points")
        
        # Close all remaining positions
        for symbol in list(self.current_positions.keys()):
            if symbol in current_prices:
                self._close_position(symbol, current_prices[symbol], current_time, "backtest_end")
        
        # Calculate performance metrics
        metrics = self._calculate_performance_metrics()
        
        result = {
            'metrics': asdict(metrics),
            'trades': [asdict(trade) for trade in self.trades],
            'equity_curve': [(t.isoformat(), v) for t, v in self.equity_curve],
            'final_balance': self.current_balance,
            'total_return': ((self.current_balance - self.initial_balance) / self.initial_balance) * 100
        }
        
        logger.info(f"Backtest completed. Final balance: ${self.current_balance:,.2f}, Total return: {result['total_return']:.2f}%")
        
        return result
    
    def _execute_signal(self, symbol: str, signal: Dict, current_price: float, timestamp: datetime):
        """Execute trading signal"""
        direction = signal.get('direction')
        confidence = signal.get('confidence', 0.5)
        
        if not direction or direction not in ['BUY', 'SELL']:
            return
        
        # Check if we already have a position in this symbol
        if symbol in self.current_positions:
            # Close existing position if signal is opposite
            existing_pos = self.current_positions[symbol]
            if existing_pos['direction'] != direction:
                self._close_position(symbol, current_price, timestamp, "signal_reversal")
            return
        
        # Calculate position size based on confidence
        risk_per_trade = self.current_balance * 0.02  # 2% risk per trade
        position_size = (risk_per_trade * confidence) / current_price
        
        # Calculate stop loss and take profit
        stop_distance = current_price * 0.02  # 2% stop loss
        if direction == 'BUY':
            stop_loss = current_price - stop_distance
            take_profit = current_price + (stop_distance * 1.5)
        else:
            stop_loss = current_price + stop_distance
            take_profit = current_price - (stop_distance * 1.5)
        
        # Calculate commission
        commission = position_size * current_price * self.commission_rate
        
        # Open position
        self.current_positions[symbol] = {
            'direction': direction,
            'size': position_size,
            'entry_price': current_price,
            'entry_time': timestamp,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'commission': commission,
            'signal': signal
        }
        
        logger.debug(f"Opened {direction} position in {symbol} at {current_price}, size: {position_size}")
    
    def _update_positions(self, current_prices: Dict[str, float], timestamp: datetime):
        """Update existing positions, check stop loss and take profit"""
        for symbol in list(self.current_positions.keys()):
            if symbol in current_prices:
                position = self.current_positions[symbol]
                current_price = current_prices[symbol]
                
                # Check stop loss
                if position['direction'] == 'BUY':
                    if current_price <= position['stop_loss']:
                        self._close_position(symbol, current_price, timestamp, "stop_loss")
                    elif current_price >= position['take_profit']:
                        self._close_position(symbol, current_price, timestamp, "take_profit")
                else:  # SELL
                    if current_price >= position['stop_loss']:
                        self._close_position(symbol, current_price, timestamp, "stop_loss")
                    elif current_price <= position['take_profit']:
                        self._close_position(symbol, current_price, timestamp, "take_profit")
    
    def _close_position(self, symbol: str, exit_price: float, timestamp: datetime, reason: str):
        """Close a position and record the trade"""
        if symbol not in self.current_positions:
            return
        
        position = self.current_positions[symbol]
        
        # Calculate P&L
        if position['direction'] == 'BUY':
            pnl = (exit_price - position['entry_price']) * position['size'] - position['commission']
        else:
            pnl = (position['entry_price'] - exit_price) * position['size'] - position['commission']
        
        # Create trade record
        trade = Trade(
            symbol=symbol,
            direction=position['direction'],
            entry_time=position['entry_time'],
            entry_price=position['entry_price'],
            exit_time=timestamp,
            exit_price=exit_price,
            size=position['size'],
            pnl=pnl,
            commission=position['commission'],
            duration_hours=(timestamp - position['entry_time']).total_seconds() / 3600,
            entry_signal=position['signal'].get('direction', 'UNKNOWN'),
            exit_reason=reason
        )
        
        self.trades.append(trade)
        self.current_balance += pnl
        
        del self.current_positions[symbol]
        
        logger.debug(f"Closed {symbol} position: P&L=${pnl:.2f}, Reason: {reason}")
    
    def _calculate_performance_metrics(self) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics"""
        if not self.trades:
            return PerformanceMetrics(
                total_trades=0, winning_trades=0, losing_trades=0, win_rate=0,
                total_pnl=0, total_return=0, sharpe_ratio=0, max_drawdown=0,
                max_drawdown_duration=0, profit_factor=0, avg_win=0, avg_loss=0,
                avg_win_loss_ratio=0, largest_win=0, largest_loss=0,
                avg_trade_duration=0, volatility=0, calmar_ratio=0, sortino_ratio=0
            )
        
        # Basic metrics
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t.pnl > 0])
        losing_trades = total_trades - winning_trades
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        # P&L metrics
        total_pnl = sum(t.pnl for t in self.trades)
        total_return = ((self.current_balance - self.initial_balance) / self.initial_balance) * 100
        
        wins = [t.pnl for t in self.trades if t.pnl > 0]
        losses = [t.pnl for t in self.trades if t.pnl < 0]
        
        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        largest_win = max(wins) if wins else 0
        largest_loss = min(losses) if losses else 0
        
        profit_factor = sum(wins) / abs(sum(losses)) if losses else float('inf')
        avg_win_loss_ratio = avg_win / abs(avg_loss) if avg_loss != 0 else float('inf')
        
        # Time metrics
        avg_trade_duration = np.mean([t.duration_hours for t in self.trades])
        
        # Risk metrics
        equity_values = [balance for _, balance in self.equity_curve]
        returns = np.diff(equity_values) / equity_values[:-1] if len(equity_values) > 1 else []
        
        volatility = np.std(returns) * np.sqrt(252 * 24) if len(returns) > 1 else 0  # Annualized
        
        # Sharpe ratio
        sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252 * 24) if len(returns) > 1 and np.std(returns) > 0 else 0
        
        # Sortino ratio
        downside_returns = [r for r in returns if r < 0]
        sortino_ratio = np.mean(returns) / np.std(downside_returns) * np.sqrt(252 * 24) if len(downside_returns) > 0 and np.std(downside_returns) > 0 else 0
        
        # Drawdown
        peak = np.maximum.accumulate(equity_values)
        drawdown = (peak - equity_values) / peak * 100
        max_drawdown = np.max(drawdown)
        
        # Max drawdown duration
        drawdown_periods = []
        in_drawdown = False
        drawdown_start = None
        
        for i, dd in enumerate(drawdown):
            if dd > 0 and not in_drawdown:
                in_drawdown = True
                drawdown_start = i
            elif dd == 0 and in_drawdown:
                in_drawdown = False
                drawdown_periods.append(i - drawdown_start)
        
        max_drawdown_duration = max(drawdown_periods) if drawdown_periods else 0
        
        # Calmar ratio
        calmar_ratio = total_return / max_drawdown if max_drawdown > 0 else 0
        
        return PerformanceMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_pnl=total_pnl,
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_duration=max_drawdown_duration,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            avg_win_loss_ratio=avg_win_loss_ratio,
            largest_win=largest_win,
            largest_loss=largest_loss,
            avg_trade_duration=avg_trade_duration,
            volatility=volatility,
            calmar_ratio=calmar_ratio,
            sortino_ratio=sortino_ratio
        )
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive backtest report"""
        metrics = results['metrics']
        
        report = f"""
# FX Alpha Platform - Backtest Report

## Performance Summary
- **Total Return**: {metrics['total_return']:.2f}%
- **Total P&L**: ${metrics['total_pnl']:,.2f}
- **Sharpe Ratio**: {metrics['sharpe_ratio']:.2f}
- **Max Drawdown**: {metrics['max_drawdown']:.2f}%
- **Win Rate**: {metrics['win_rate']:.1f}%

## Trading Statistics
- **Total Trades**: {metrics['total_trades']}
- **Winning Trades**: {metrics['winning_trades']}
- **Losing Trades**: {metrics['losing_trades']}
- **Profit Factor**: {metrics['profit_factor']:.2f}
- **Average Win**: ${metrics['avg_win']:.2f}
- **Average Loss**: ${metrics['avg_loss']:.2f}
- **Largest Win**: ${metrics['largest_win']:.2f}
- **Largest Loss**: ${metrics['largest_loss']:.2f}

## Risk Metrics
- **Volatility**: {metrics['volatility']:.2f}
- **Sortino Ratio**: {metrics['sortino_ratio']:.2f}
- **Calmar Ratio**: {metrics['calmar_ratio']:.2f}
- **Max Drawdown Duration**: {metrics['max_drawdown_duration']} periods
- **Average Trade Duration**: {metrics['avg_trade_duration']:.1f} hours

## Assessment
"""
        
        # Performance assessment
        if metrics['sharpe_ratio'] > 1.5:
            report += "✅ **Excellent**: Sharpe ratio > 1.5\n"
        elif metrics['sharpe_ratio'] > 1.0:
            report += "⚠️ **Good**: Sharpe ratio > 1.0\n"
        else:
            report += "❌ **Poor**: Sharpe ratio < 1.0\n"
        
        if metrics['max_drawdown'] < 15:
            report += "✅ **Excellent**: Max drawdown < 15%\n"
        elif metrics['max_drawdown'] < 25:
            report += "⚠️ **Acceptable**: Max drawdown < 25%\n"
        else:
            report += "❌ **Poor**: Max drawdown > 25%\n"
        
        if metrics['win_rate'] > 55:
            report += "✅ **Excellent**: Win rate > 55%\n"
        elif metrics['win_rate'] > 45:
            report += "⚠️ **Acceptable**: Win rate > 45%\n"
        else:
            report += "❌ **Poor**: Win rate < 45%\n"
        
        if metrics['profit_factor'] > 1.3:
            report += "✅ **Excellent**: Profit factor > 1.3\n"
        elif metrics['profit_factor'] > 1.1:
            report += "⚠️ **Acceptable**: Profit factor > 1.1\n"
        else:
            report += "❌ **Poor**: Profit factor < 1.1\n"
        
        return report

# Utility function for creating signal generators
def create_multi_agent_signal_generator(coordinator_agent):
    """Create a signal generator function for backtesting"""
    def signal_generator(timestamp, prices, positions):
        signals = {}
        
        for symbol in prices.keys():
            try:
                # Generate signal using the multi-agent coordinator
                signal_result = coordinator_agent.generate_signal(symbol)
                
                if signal_result and signal_result.get('success'):
                    signal = signal_result['signal']
                    direction = signal.get('direction', 'NEUTRAL')
                    confidence = signal.get('confidence', 0.5)
                    
                    if direction != 'NEUTRAL' and confidence > 0.6:
                        signals[symbol] = {
                            'direction': direction,
                            'confidence': confidence,
                            'timestamp': timestamp.isoformat()
                        }
            except Exception as e:
                logger.error(f"Error generating signal for {symbol}: {e}")
        
        return signals
    
    return signal_generator
