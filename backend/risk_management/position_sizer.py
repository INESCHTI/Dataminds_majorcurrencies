"""
Position Sizing and Risk Management Module
Implements various position sizing strategies and risk controls
"""
import math
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class PositionSizingMethod(Enum):
    FIXED = "fixed"
    PERCENTAGE = "percentage"
    VOLATILITY = "volatility"
    KELLY = "kelly"
    RISK_PARITY = "risk_parity"

@dataclass
class RiskParameters:
    max_portfolio_risk: float = 0.02  # 2% max portfolio risk
    max_position_risk: float = 0.01   # 1% max position risk
    max_positions: int = 10           # Max concurrent positions
    stop_loss_atr_multiplier: float = 2.0  # Stop loss at 2x ATR
    take_profit_atr_multiplier: float = 3.0  # Take profit at 3x ATR
    min_trade_size: float = 1000     # Minimum trade size in currency
    max_leverage: float = 50.0       # Maximum leverage allowed

@dataclass
class Position:
    symbol: str
    direction: str  # "BUY" or "SELL"
    size: float
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_amount: float
    potential_profit: float
    risk_reward_ratio: float
    timestamp: datetime

class PositionSizer:
    """Advanced position sizing with multiple methods and risk controls"""
    
    def __init__(self, risk_params: RiskParameters):
        self.risk_params = risk_params
        self.current_positions: Dict[str, Position] = {}
        self.account_balance: float = 100000.0  # Default account balance
        self.total_risk: float = 0.0
        
    def update_account_balance(self, balance: float):
        """Update account balance for calculations"""
        self.account_balance = balance
        logger.info(f"Account balance updated to: ${balance:,.2f}")
    
    def calculate_position_size(
        self, 
        symbol: str, 
        direction: str, 
        entry_price: float, 
        stop_loss: float,
        method: PositionSizingMethod = PositionSizingMethod.PERCENTAGE,
        confidence: float = 0.5,
        volatility: float = 0.01,
        win_rate: float = 0.5,
        avg_win_loss_ratio: float = 1.0
    ) -> Tuple[float, Dict]:
        """Calculate optimal position size using specified method"""
        
        # Validate inputs
        if direction not in ["BUY", "SELL"]:
            raise ValueError("Direction must be 'BUY' or 'SELL'")
        
        if stop_loss is None:
            raise ValueError("Stop loss must be provided")
        
        # Calculate risk per trade
        risk_per_trade = self.account_balance * self.risk_params.max_position_risk
        
        # Calculate position size based on method
        if method == PositionSizingMethod.FIXED:
            position_size, details = self._fixed_size()
        elif method == PositionSizingMethod.PERCENTAGE:
            position_size, details = self._percentage_size(risk_per_trade, entry_price, stop_loss)
        elif method == PositionSizingMethod.VOLATILITY:
            position_size, details = self._volatility_size(risk_per_trade, entry_price, stop_loss, volatility)
        elif method == PositionSizingMethod.KELLY:
            position_size, details = self._kelly_size(win_rate, avg_win_loss_ratio, entry_price, stop_loss)
        elif method == PositionSizingMethod.RISK_PARITY:
            position_size, details = self._risk_parity_size(risk_per_trade, entry_price, stop_loss, volatility)
        else:
            raise ValueError(f"Unknown position sizing method: {method}")
        
        # Apply risk controls
        position_size = self._apply_risk_controls(position_size, symbol, direction, entry_price, stop_loss, confidence)
        
        # Calculate risk metrics
        risk_amount = abs(entry_price - stop_loss) * position_size
        take_profit = self._calculate_take_profit(entry_price, stop_loss, direction)
        potential_profit = abs(take_profit - entry_price) * position_size
        risk_reward_ratio = potential_profit / risk_amount if risk_amount > 0 else 0
        
        # Create position object
        position = Position(
            symbol=symbol,
            direction=direction,
            size=position_size,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_amount=risk_amount,
            potential_profit=potential_profit,
            risk_reward_ratio=risk_reward_ratio,
            timestamp=datetime.now()
        )
        
        details.update({
            'position_size': position_size,
            'risk_amount': risk_amount,
            'potential_profit': potential_profit,
            'risk_reward_ratio': risk_reward_ratio,
            'take_profit': take_profit,
            'portfolio_risk': (self.total_risk + risk_amount) / self.account_balance
        })
        
        return position_size, details
    
    def _fixed_size(self) -> Tuple[float, Dict]:
        """Fixed position size method"""
        size = 10000.0  # Fixed $10,000 position
        return size, {'method': 'fixed', 'base_size': size}
    
    def _percentage_size(self, risk_amount: float, entry_price: float, stop_loss: float) -> Tuple[float, Dict]:
        """Percentage risk method"""
        risk_per_unit = abs(entry_price - stop_loss)
        if risk_per_unit == 0:
            return 0, {'error': 'Zero risk per unit'}
        
        size = risk_amount / risk_per_unit
        return size, {
            'method': 'percentage',
            'risk_per_trade': risk_amount,
            'risk_per_unit': risk_per_unit,
            'calculated_size': size
        }
    
    def _volatility_size(self, risk_amount: float, entry_price: float, stop_loss: float, volatility: float) -> Tuple[float, Dict]:
        """Volatility-adjusted position sizing"""
        risk_per_unit = abs(entry_price - stop_loss)
        if risk_per_unit == 0:
            return 0, {'error': 'Zero risk per unit'}
        
        # Adjust position size based on volatility (inverse relationship)
        volatility_adjustment = min(2.0, max(0.5, 1.0 / (volatility * 100)))
        base_size = risk_amount / risk_per_unit
        adjusted_size = base_size * volatility_adjustment
        
        return adjusted_size, {
            'method': 'volatility',
            'risk_per_trade': risk_amount,
            'volatility': volatility,
            'volatility_adjustment': volatility_adjustment,
            'base_size': base_size,
            'adjusted_size': adjusted_size
        }
    
    def _kelly_size(self, win_rate: float, avg_win_loss_ratio: float, entry_price: float, stop_loss: float) -> Tuple[float, Dict]:
        """Kelly Criterion position sizing"""
        if win_rate <= 0 or win_rate >= 1:
            return 0, {'error': 'Invalid win rate for Kelly formula'}
        
        # Kelly formula: f* = (bp - q) / b
        # where b = avg win/loss ratio, p = win rate, q = loss rate
        b = avg_win_loss_ratio
        p = win_rate
        q = 1 - p
        
        kelly_fraction = (b * p - q) / b
        kelly_fraction = max(0, min(0.25, kelly_fraction))  # Cap at 25% of bankroll
        
        risk_per_unit = abs(entry_price - stop_loss)
        if risk_per_unit == 0:
            return 0, {'error': 'Zero risk per unit'}
        
        kelly_size = (self.account_balance * kelly_fraction) / risk_per_unit
        
        return kelly_size, {
            'method': 'kelly',
            'win_rate': win_rate,
            'avg_win_loss_ratio': avg_win_loss_ratio,
            'kelly_fraction': kelly_fraction,
            'calculated_size': kelly_size
        }
    
    def _risk_parity_size(self, risk_amount: float, entry_price: float, stop_loss: float, volatility: float) -> Tuple[float, Dict]:
        """Risk parity position sizing"""
        risk_per_unit = abs(entry_price - stop_loss)
        if risk_per_unit == 0:
            return 0, {'error': 'Zero risk per unit'}
        
        # Target equal risk contribution across all positions
        num_positions = len(self.current_positions) + 1
        target_risk_per_position = self.risk_params.max_portfolio_risk / max(1, num_positions)
        
        # Adjust for volatility
        volatility_adjustment = 1.0 / (1.0 + volatility * 10)  # Reduce size for high volatility
        adjusted_risk = target_risk_per_position * volatility_adjustment
        
        size = (self.account_balance * adjusted_risk) / risk_per_unit
        
        return size, {
            'method': 'risk_parity',
            'target_risk_per_position': target_risk_per_position,
            'volatility_adjustment': volatility_adjustment,
            'adjusted_risk': adjusted_risk,
            'calculated_size': size
        }
    
    def _apply_risk_controls(
        self, 
        size: float, 
        symbol: str, 
        direction: str, 
        entry_price: float, 
        stop_loss: float, 
        confidence: float
    ) -> float:
        """Apply comprehensive risk controls"""
        
        # Minimum trade size
        size = max(self.risk_params.min_trade_size, size)
        
        # Maximum leverage check
        required_margin = size * entry_price / self.risk_params.max_leverage
        if required_margin > self.account_balance * 0.95:  # Don't use more than 95% of account
            size = (self.account_balance * 0.95 * self.risk_params.max_leverage) / entry_price
        
        # Maximum position count
        if len(self.current_positions) >= self.risk_params.max_positions:
            # Reduce size to fit within position limit
            size = size * 0.5
        
        # Portfolio risk check
        new_position_risk = abs(entry_price - stop_loss) * size
        if (self.total_risk + new_position_risk) > (self.account_balance * self.risk_params.max_portfolio_risk):
            # Reduce size to stay within portfolio risk limit
            max_risk = (self.account_balance * self.risk_params.max_portfolio_risk) - self.total_risk
            size = max(0, max_risk / abs(entry_price - stop_loss))
        
        # Confidence adjustment
        if confidence < 0.7:
            size *= confidence  # Reduce size for low confidence
        
        # Correlation check (simplified)
        if self._has_correlated_position(symbol):
            size *= 0.5  # Reduce size for correlated positions
        
        return size
    
    def _has_correlated_position(self, symbol: str) -> bool:
        """Check if there's a correlated position already open"""
        correlations = {
            'EURUSD': ['GBPUSD', 'EURGBP', 'EURCHF'],
            'GBPUSD': ['EURUSD', 'EURGBP', 'GBPCHF'],
            'USDJPY': ['EURJPY', 'GBPJPY', 'CHFJPY'],
            'USDCHF': ['EURCHF', 'GBPCHF', 'EURUSD'],
        }
        
        correlated_symbols = correlations.get(symbol, [])
        return any(pos_symbol in correlated_symbols for pos_symbol in self.current_positions.keys())
    
    def _calculate_take_profit(self, entry_price: float, stop_loss: float, direction: str) -> float:
        """Calculate take profit based on risk/reward ratio"""
        risk = abs(entry_price - stop_loss)
        reward = risk * self.risk_params.take_profit_atr_multiplier
        
        if direction == "BUY":
            return entry_price + reward
        else:
            return entry_price - reward
    
    def add_position(self, position: Position):
        """Add a new position to track"""
        self.current_positions[position.symbol] = position
        self.total_risk += position.risk_amount
        logger.info(f"Position added: {position.symbol} {position.direction} size={position.size} risk=${position.risk_amount:.2f}")
    
    def close_position(self, symbol: str, exit_price: float) -> Dict:
        """Close a position and calculate P&L"""
        if symbol not in self.current_positions:
            return {'error': 'Position not found'}
        
        position = self.current_positions[symbol]
        
        # Calculate P&L
        if position.direction == "BUY":
            pnl = (exit_price - position.entry_price) * position.size
        else:
            pnl = (position.entry_price - exit_price) * position.size
        
        # Update account balance
        self.account_balance += pnl
        
        # Remove position and update risk
        del self.current_positions[symbol]
        self.total_risk -= position.risk_amount
        
        result = {
            'symbol': symbol,
            'entry_price': position.entry_price,
            'exit_price': exit_price,
            'size': position.size,
            'direction': position.direction,
            'pnl': pnl,
            'risk_amount': position.risk_amount,
            'risk_reward_ratio': position.risk_reward_ratio,
            'duration': (datetime.now() - position.timestamp).total_seconds() / 3600  # hours
        }
        
        logger.info(f"Position closed: {symbol} P&L=${pnl:.2f}")
        return result
    
    def get_portfolio_summary(self) -> Dict:
        """Get current portfolio summary"""
        open_positions = len(self.current_positions)
        total_risk_percentage = (self.total_risk / self.account_balance) * 100 if self.account_balance > 0 else 0
        
        return {
            'account_balance': self.account_balance,
            'open_positions': open_positions,
            'total_risk': self.total_risk,
            'total_risk_percentage': total_risk_percentage,
            'max_positions': self.risk_params.max_positions,
            'risk_utilization': total_risk_percentage / (self.risk_params.max_portfolio_risk * 100),
            'positions': {
                symbol: {
                    'direction': pos.direction,
                    'size': pos.size,
                    'entry_price': pos.entry_price,
                    'stop_loss': pos.stop_loss,
                    'take_profit': pos.take_profit,
                    'pnl': (pos.entry_price - pos.stop_loss) * pos.size if pos.direction == "SELL" else (pos.stop_loss - pos.entry_price) * pos.size,
                    'risk_amount': pos.risk_amount,
                    'duration_hours': (datetime.now() - pos.timestamp).total_seconds() / 3600
                }
                for symbol, pos in self.current_positions.items()
            }
        }
    
    def validate_risk_limits(self) -> Dict:
        """Validate if current positions are within risk limits"""
        violations = []
        
        # Check portfolio risk
        portfolio_risk_pct = (self.total_risk / self.account_balance) * 100
        if portfolio_risk_pct > (self.risk_params.max_portfolio_risk * 100):
            violations.append(f"Portfolio risk {portfolio_risk_pct:.2f}% exceeds limit {self.risk_params.max_portfolio_risk * 100}%")
        
        # Check position count
        if len(self.current_positions) > self.risk_params.max_positions:
            violations.append(f"Position count {len(self.current_positions)} exceeds limit {self.risk_params.max_positions}")
        
        # Check individual position risks
        for symbol, position in self.current_positions.items():
            position_risk_pct = (position.risk_amount / self.account_balance) * 100
            if position_risk_pct > (self.risk_params.max_position_risk * 100):
                violations.append(f"Position {symbol} risk {position_risk_pct:.2f}% exceeds limit {self.risk_params.max_position_risk * 100}%")
        
        return {
            'violations': violations,
            'is_compliant': len(violations) == 0,
            'portfolio_risk_pct': portfolio_risk_pct,
            'position_count': len(self.current_positions),
            'total_risk': self.total_risk
        }

# Factory function
def create_position_sizer(
    max_portfolio_risk: float = 0.02,
    max_position_risk: float = 0.01,
    account_balance: float = 100000.0
) -> PositionSizer:
    """Create position sizer with default risk parameters"""
    risk_params = RiskParameters(
        max_portfolio_risk=max_portfolio_risk,
        max_position_risk=max_position_risk
    )
    
    sizer = PositionSizer(risk_params)
    sizer.update_account_balance(account_balance)
    
    return sizer
