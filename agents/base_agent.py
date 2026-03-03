"""
Base Agent Class
Abstract base class for all trading agents
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime
import pandas as pd


@dataclass
class Signal:
    """Trading signal with metadata"""
    timestamp: datetime
    symbol: str
    direction: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float  # 0.0 to 1.0
    agent_name: str
    reasoning: str
    indicators: Dict[str, float]
    
    def to_dict(self) -> Dict:
        """Convert signal to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'direction': self.direction,
            'confidence': self.confidence,
            'agent_name': self.agent_name,
            'reasoning': self.reasoning,
            'indicators': self.indicators
        }


class BaseAgent(ABC):
    """Abstract base class for all trading agents"""
    
    def __init__(self, name: str, weight: float = 1.0):
        """
        Initialize base agent
        
        Args:
            name: Agent name
            weight: Agent weight in ensemble (0.0 to 1.0)
        """
        self.name = name
        self.weight = weight
        self.signals_history: List[Signal] = []
        
    @abstractmethod
    def analyze(self, symbol: str, data: pd.DataFrame, **kwargs) -> Signal:
        """
        Analyze market data and generate trading signal
        
        Args:
            symbol: Currency pair symbol (e.g., 'EURUSD')
            data: Market data DataFrame
            **kwargs: Additional parameters
            
        Returns:
            Signal object with trading recommendation
        """
        pass
    
    @abstractmethod
    def get_required_data(self) -> List[str]:
        """
        Get list of required data fields
        
        Returns:
            List of required column names
        """
        pass
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate input data has required fields
        
        Args:
            data: Input DataFrame
            
        Returns:
            True if data is valid
        """
        required = self.get_required_data()
        missing = [col for col in required if col not in data.columns]
        
        if missing:
            raise ValueError(f"{self.name}: Missing required columns: {missing}")
        
        if data.empty:
            raise ValueError(f"{self.name}: Input data is empty")
            
        return True
    
    def record_signal(self, signal: Signal):
        """Record signal in history"""
        self.signals_history.append(signal)
        
    def get_performance(self) -> Dict[str, float]:
        """
        Calculate agent performance metrics
        
        Returns:
            Dictionary of performance metrics
        """
        if not self.signals_history:
            return {
                'total_signals': 0,
                'avg_confidence': 0.0,
                'buy_signals': 0,
                'sell_signals': 0,
                'hold_signals': 0
            }
        
        buy_count = sum(1 for s in self.signals_history if s.direction == 'BUY')
        sell_count = sum(1 for s in self.signals_history if s.direction == 'SELL')
        hold_count = sum(1 for s in self.signals_history if s.direction == 'HOLD')
        avg_confidence = sum(s.confidence for s in self.signals_history) / len(self.signals_history)
        
        return {
            'total_signals': len(self.signals_history),
            'avg_confidence': avg_confidence,
            'buy_signals': buy_count,
            'sell_signals': sell_count,
            'hold_signals': hold_count,
            'buy_ratio': buy_count / len(self.signals_history) if self.signals_history else 0,
            'sell_ratio': sell_count / len(self.signals_history) if self.signals_history else 0
        }
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', weight={self.weight})"
