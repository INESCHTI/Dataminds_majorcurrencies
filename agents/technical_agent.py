"""
Technical Agent (DSO1.2)
Analyzes price patterns using technical indicators
"""

import pandas as pd
import numpy as np
from typing import List, Dict
from datetime import datetime
from .base_agent import BaseAgent, Signal


class TechnicalAgent(BaseAgent):
    """
    Technical Analysis Agent
    Uses TA-Lib indicators: RSI, MACD, Bollinger Bands, Moving Averages
    """
    
    def __init__(self, 
                 name: str = "Technical Agent",
                 weight: float = 1.0,
                 rsi_period: int = 14,
                 rsi_oversold: float = 30,
                 rsi_overbought: float = 70,
                 macd_fast: int = 12,
                 macd_slow: int = 26,
                 macd_signal: int = 9,
                 bb_period: int = 20,
                 bb_std: float = 2.0,
                 ma_short: int = 20,
                 ma_long: int = 50):
        """
        Initialize Technical Agent
        
        Args:
            name: Agent name
            weight: Agent weight in ensemble
            rsi_period: RSI calculation period
            rsi_oversold: RSI oversold threshold
            rsi_overbought: RSI overbought threshold
            macd_fast: MACD fast period
            macd_slow: MACD slow period
            macd_signal: MACD signal period
            bb_period: Bollinger Bands period
            bb_std: Bollinger Bands standard deviation
            ma_short: Short moving average period
            ma_long: Long moving average period
        """
        super().__init__(name, weight)
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.ma_short = ma_short
        self.ma_long = ma_long
    
    def get_required_data(self) -> List[str]:
        """Required OHLC data"""
        return ['open', 'high', 'low', 'close', 'volume']
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, prices: pd.Series) -> Dict[str, pd.Series]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        ema_fast = prices.ewm(span=self.macd_fast, adjust=False).mean()
        ema_slow = prices.ewm(span=self.macd_slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.macd_signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def calculate_bollinger_bands(self, prices: pd.Series) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=self.bb_period).mean()
        std = prices.rolling(window=self.bb_period).std()
        upper_band = sma + (std * self.bb_std)
        lower_band = sma - (std * self.bb_std)
        
        return {
            'upper': upper_band,
            'middle': sma,
            'lower': lower_band
        }
    
    def calculate_moving_averages(self, prices: pd.Series) -> Dict[str, pd.Series]:
        """Calculate Simple Moving Averages"""
        return {
            'sma_short': prices.rolling(window=self.ma_short).mean(),
            'sma_long': prices.rolling(window=self.ma_long).mean()
        }
    
    def analyze(self, symbol: str, data: pd.DataFrame, **kwargs) -> Signal:
        """
        Analyze technical indicators and generate signal
        
        Args:
            symbol: Currency pair
            data: OHLC DataFrame with columns [open, high, low, close, volume]
            
        Returns:
            Signal with BUY/SELL/HOLD recommendation
        """
        self.validate_data(data)
        
        if len(data) < max(self.ma_long, self.bb_period, self.rsi_period):
            return Signal(
                timestamp=datetime.now(),
                symbol=symbol,
                direction='HOLD',
                confidence=0.0,
                agent_name=self.name,
                reasoning="Insufficient data for technical analysis",
                indicators={}
            )
        
        # Calculate all indicators
        close_prices = data['close']
        
        rsi = self.calculate_rsi(close_prices, self.rsi_period)
        macd_data = self.calculate_macd(close_prices)
        bb_data = self.calculate_bollinger_bands(close_prices)
        ma_data = self.calculate_moving_averages(close_prices)
        
        # Get latest values
        current_price = close_prices.iloc[-1]
        current_rsi = rsi.iloc[-1]
        current_macd = macd_data['macd'].iloc[-1]
        current_signal = macd_data['signal'].iloc[-1]
        current_histogram = macd_data['histogram'].iloc[-1]
        bb_upper = bb_data['upper'].iloc[-1]
        bb_lower = bb_data['lower'].iloc[-1]
        bb_middle = bb_data['middle'].iloc[-1]
        sma_short = ma_data['sma_short'].iloc[-1]
        sma_long = ma_data['sma_long'].iloc[-1]
        
        # Detect crossovers
        macd_crossover = current_macd > current_signal and macd_data['macd'].iloc[-2] <= macd_data['signal'].iloc[-2]
        macd_crossunder = current_macd < current_signal and macd_data['macd'].iloc[-2] >= macd_data['signal'].iloc[-2]
        ma_crossover = sma_short > sma_long and ma_data['sma_short'].iloc[-2] <= ma_data['sma_long'].iloc[-2]
        ma_crossunder = sma_short < sma_long and ma_data['sma_short'].iloc[-2] >= ma_data['sma_long'].iloc[-2]
        
        # Signal generation logic
        buy_signals = 0
        sell_signals = 0
        reasoning_parts = []
        
        # RSI Analysis
        if current_rsi < self.rsi_oversold:
            buy_signals += 1
            reasoning_parts.append(f"RSI oversold ({current_rsi:.1f})")
        elif current_rsi > self.rsi_overbought:
            sell_signals += 1
            reasoning_parts.append(f"RSI overbought ({current_rsi:.1f})")
        
        # MACD Analysis
        if macd_crossover:
            buy_signals += 1
            reasoning_parts.append("MACD bullish crossover")
        elif macd_crossunder:
            sell_signals += 1
            reasoning_parts.append("MACD bearish crossunder")
        elif current_histogram > 0:
            buy_signals += 0.5
            reasoning_parts.append("MACD histogram positive")
        else:
            sell_signals += 0.5
            reasoning_parts.append("MACD histogram negative")
        
        # Bollinger Bands Analysis
        if current_price < bb_lower:
            buy_signals += 1
            reasoning_parts.append("Price below lower Bollinger Band")
        elif current_price > bb_upper:
            sell_signals += 1
            reasoning_parts.append("Price above upper Bollinger Band")
        
        # Moving Average Analysis
        if ma_crossover:
            buy_signals += 1
            reasoning_parts.append("MA golden cross")
        elif ma_crossunder:
            sell_signals += 1
            reasoning_parts.append("MA death cross")
        elif sma_short > sma_long:
            buy_signals += 0.5
            reasoning_parts.append("Short-term uptrend")
        else:
            sell_signals += 0.5
            reasoning_parts.append("Short-term downtrend")
        
        # Determine final signal
        total_signals = buy_signals + sell_signals
        if total_signals == 0:
            direction = 'HOLD'
            confidence = 0.0
            reasoning = "No clear technical signal"
        elif buy_signals > sell_signals:
            direction = 'BUY'
            confidence = min(buy_signals / 5.0, 1.0)  # Normalize to 0-1
            reasoning = "Technical indicators bullish: " + ", ".join(reasoning_parts)
        elif sell_signals > buy_signals:
            direction = 'SELL'
            confidence = min(sell_signals / 5.0, 1.0)
            reasoning = "Technical indicators bearish: " + ", ".join(reasoning_parts)
        else:
            direction = 'HOLD'
            confidence = 0.5
            reasoning = "Technical indicators neutral: " + ", ".join(reasoning_parts)
        
        # Create signal
        signal = Signal(
            timestamp=datetime.now(),
            symbol=symbol,
            direction=direction,
            confidence=confidence,
            agent_name=self.name,
            reasoning=reasoning,
            indicators={
                'rsi': float(current_rsi),
                'macd': float(current_macd),
                'macd_signal': float(current_signal),
                'macd_histogram': float(current_histogram),
                'bb_upper': float(bb_upper),
                'bb_middle': float(bb_middle),
                'bb_lower': float(bb_lower),
                'sma_short': float(sma_short),
                'sma_long': float(sma_long),
                'price': float(current_price)
            }
        )
        
        self.record_signal(signal)
        return signal
