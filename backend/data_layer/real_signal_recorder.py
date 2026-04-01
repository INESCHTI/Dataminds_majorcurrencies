"""
Real Signal Recorder for FX Alpha Platform
Records actual signal generation and trade execution
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class RealSignalRecorder:
    """
    Records real signal generation and trade execution
    """
    
    def __init__(self):
        self.active_trades = {}  # {trade_id: trade_info}
        self.trade_counter = 0
        
        # Risk management parameters
        self.risk_per_trade = 0.02  # 2% risk per trade
        self.rr_ratio = 1.5  # 1.5:1 reward-to-risk ratio
    
    def generate_signal_from_market_data(self, ohlcv_df: pd.DataFrame, 
                                        agent_name: str, pair: str) -> Dict:
        """
        Generate a real signal based on market data and agent logic
        """
        try:
            if ohlcv_df.empty:
                return self._create_neutral_signal(agent_name, pair, "No market data")
            
            latest_data = ohlcv_df.iloc[-1]
            recent_data = ohlcv_df.tail(5)  # Last 5 days
            
            # Agent-specific signal generation logic
            if agent_name == 'TechnicalV2':
                signal = self._technical_signal(recent_data, latest_data)
            elif agent_name == 'MacroV2':
                signal = self._macro_signal(recent_data, latest_data, pair)
            elif agent_name == 'SentimentV2':
                signal = self._sentiment_signal(recent_data, latest_data)
            elif agent_name == 'GeopoliticalV2':
                signal = self._geopolitical_signal(recent_data, latest_data, pair)
            else:
                signal = self._create_neutral_signal(agent_name, pair, "Unknown agent")
            
            # Add metadata
            signal.update({
                'timestamp': datetime.now(),
                'pair': pair,
                'agent_name': agent_name,
                'entry_price': latest_data['close']
            })
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating signal for {agent_name}: {e}")
            return self._create_neutral_signal(agent_name, pair, f"Error: {str(e)}")
    
    def _technical_signal(self, recent_data: pd.DataFrame, latest_data: Dict) -> Dict:
        """Generate technical analysis signal"""
        close_prices = recent_data['close'].values
        
        if len(close_prices) < 5:
            return self._create_neutral_signal("TechnicalV2", "", "Insufficient data")
        
        # Simple technical indicators
        # RSI calculation (simplified)
        price_changes = np.diff(close_prices)
        gains = np.where(price_changes > 0, price_changes, 0)
        losses = np.where(price_changes < 0, -price_changes, 0)
        
        if len(gains) > 0 and len(losses) > 0:
            avg_gain = np.mean(gains)
            avg_loss = np.mean(losses)
            
            if avg_loss > 0:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            else:
                rsi = 100 if avg_gain > 0 else 50
        else:
            rsi = 50
        
        # Moving average
        ma_short = np.mean(close_prices[-3:])
        ma_long = np.mean(close_prices[-5:])
        
        # Signal logic
        current_price = latest_data['close']
        
        if rsi < 30 and current_price > ma_short:
            return {
                'signal': 'BUY',
                'confidence': 0.75,
                'reasoning': f"RSI oversold ({rsi:.1f}) + price above short MA ({ma_short:.5f})"
            }
        elif rsi > 70 and current_price < ma_short:
            return {
                'signal': 'SELL',
                'confidence': 0.75,
                'reasoning': f"RSI overbought ({rsi:.1f}) + price below short MA ({ma_short:.5f})"
            }
        elif ma_short > ma_long:
            return {
                'signal': 'BUY',
                'confidence': 0.60,
                'reasoning': f"Bullish trend: short MA ({ma_short:.5f}) > long MA ({ma_long:.5f})"
            }
        elif ma_short < ma_long:
            return {
                'signal': 'SELL',
                'confidence': 0.60,
                'reasoning': f"Bearish trend: short MA ({ma_short:.5f}) < long MA ({ma_long:.5f})"
            }
        else:
            return {
                'signal': 'NEUTRAL',
                'confidence': 0.40,
                'reasoning': f"No clear technical signal (RSI: {rsi:.1f}, MA: neutral)"
            }
    
    def _macro_signal(self, recent_data: pd.DataFrame, latest_data: Dict, pair: str) -> Dict:
        """Generate macroeconomic signal"""
        # Simplified macro analysis based on price trends
        price_trend = (latest_data['close'] - recent_data.iloc[0]['close']) / recent_data.iloc[0]['close']
        
        # Currency-specific macro factors
        if 'EUR' in pair:
            # EUR strength based on trend
            if price_trend > 0.01:
                return {
                    'signal': 'BUY',
                    'confidence': 0.70,
                    'reasoning': f"EUR strength: {price_trend:+.2%} trend suggests economic outperformance"
                }
            elif price_trend < -0.01:
                return {
                    'signal': 'SELL',
                    'confidence': 0.70,
                    'reasoning': f"EUR weakness: {price_trend:+.2%} trend suggests economic underperformance"
                }
        
        elif 'USD' in pair:
            # USD as safe haven
            volatility = (latest_data['high'] - latest_data['low']) / latest_data['close']
            if volatility > 0.02:  # High volatility
                return {
                    'signal': 'BUY',  # USD as safe haven
                    'confidence': 0.65,
                    'reasoning': f"High volatility ({volatility:.2%}) suggests USD safe-haven demand"
                }
        
        return {
            'signal': 'NEUTRAL',
            'confidence': 0.50,
            'reasoning': f"Macro analysis inconclusive (trend: {price_trend:+.2%})"
        }
    
    def _sentiment_signal(self, recent_data: pd.DataFrame, latest_data: Dict) -> Dict:
        """Generate sentiment-based signal"""
        # Use price action as sentiment proxy
        price_change = (latest_data['close'] - latest_data['open']) / latest_data['open']
        volume = latest_data.get('volume', 1000000)
        
        # High volume + strong move = strong sentiment
        volume_factor = min(volume / 10000000, 1.0)  # Normalize to 10M volume
        
        if abs(price_change) > 0.01 and volume_factor > 0.5:
            if price_change > 0:
                return {
                    'signal': 'BUY',
                    'confidence': 0.65 * volume_factor,
                    'reasoning': f"Bullish sentiment: {price_change:+.2%} with high volume"
                }
            else:
                return {
                    'signal': 'SELL',
                    'confidence': 0.65 * volume_factor,
                    'reasoning': f"Bearish sentiment: {price_change:+.2%} with high volume"
                }
        
        return {
            'signal': 'NEUTRAL',
            'confidence': 0.45,
            'reasoning': f"Weak sentiment: {price_change:+.2%} with low volume"
        }
    
    def _geopolitical_signal(self, recent_data: pd.DataFrame, latest_data: Dict, pair: str) -> Dict:
        """Generate geopolitical signal"""
        # Safe haven vs risk-on currencies
        safe_havens = ['USD', 'JPY', 'CHF']
        risk_currencies = ['EUR', 'GBP', 'AUD', 'CAD']
        
        base_currency = pair[:3]
        
        if base_currency in safe_havens:
            # Safe haven behavior during volatility
            volatility = (latest_data['high'] - latest_data['low']) / latest_data['close']
            if volatility > 0.015:  # High volatility
                return {
                    'signal': 'BUY',
                    'confidence': 0.60,
                    'reasoning': f"High volatility ({volatility:.1%}) favors safe haven {base_currency}"
                }
        
        elif base_currency in risk_currencies:
            # Risk-on during stable periods
            volatility = (latest_data['high'] - latest_data['low']) / latest_data['close']
            if volatility < 0.008:  # Low volatility
                return {
                    'signal': 'BUY',
                    'confidence': 0.55,
                    'reasoning': f"Low volatility ({volatility:.1%}) favors risk-on {base_currency}"
                }
            elif volatility > 0.02:
                return {
                    'signal': 'SELL',
                    'confidence': 0.55,
                    'reasoning': f"High volatility ({volatility:.1%}) hurts risk-on {base_currency}"
                }
        
        return {
            'signal': 'NEUTRAL',
            'confidence': 0.45,
            'reasoning': f"Geopolitical analysis neutral for {base_currency}"
        }
    
    def _create_neutral_signal(self, agent_name: str, pair: str, reason: str) -> Dict:
        """Create a neutral signal"""
        return {
            'signal': 'NEUTRAL',
            'confidence': 0.30,
            'reasoning': f"Neutral signal: {reason}",
            'pair': pair,
            'agent_name': agent_name,
            'timestamp': datetime.now()
        }
    
    def execute_trade(self, signal: Dict) -> Optional[str]:
        """
        Execute a trade based on signal
        Returns trade_id if trade opened
        """
        if signal['signal'] == 'NEUTRAL':
            return None
        
        self.trade_counter += 1
        trade_id = f"trade_{self.trade_counter}_{signal['pair']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        entry_price = signal['entry_price']
        signal_direction = signal['signal']
        confidence = signal['confidence']
        
        # Calculate stop loss and take profit
        atr = 0.01  # Simplified ATR (1%)
        
        if signal_direction == 'BUY':
            stop_loss = entry_price * (1 - atr)
            take_profit = entry_price * (1 + atr * self.rr_ratio)
        else:  # SELL
            stop_loss = entry_price * (1 + atr)
            take_profit = entry_price * (1 - atr * self.rr_ratio)
        
        # Store trade information
        self.active_trades[trade_id] = {
            'pair': signal['pair'],
            'agent_name': signal['agent_name'],
            'signal': signal_direction,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'confidence': confidence,
            'entry_time': datetime.now(),
            'reasoning': signal['reasoning']
        }
        
        logger.info(f"📈 Opened {signal_direction} trade {trade_id} at {entry_price:.5f}")
        return trade_id
    
    def close_trades_with_market_data(self, current_prices: Dict[str, float]) -> List[Dict]:
        """
        Close active trades based on current market prices
        """
        closed_trades = []
        
        for trade_id, trade in list(self.active_trades.items()):
            pair = trade['pair']
            if pair not in current_prices:
                continue
            
            current_price = current_prices[pair]
            signal_direction = trade['signal']
            stop_loss = trade['stop_loss']
            take_profit = trade['take_profit']
            
            should_close = False
            exit_reason = ""
            pnl = 0.0
            
            if signal_direction == 'BUY':
                if current_price >= take_profit:
                    should_close = True
                    exit_reason = "Take Profit Hit"
                    pnl = (take_profit - trade['entry_price']) / trade['entry_price']
                elif current_price <= stop_loss:
                    should_close = True
                    exit_reason = "Stop Loss Hit"
                    pnl = (current_price - trade['entry_price']) / trade['entry_price']
            else:  # SELL
                if current_price <= take_profit:
                    should_close = True
                    exit_reason = "Take Profit Hit"
                    pnl = (trade['entry_price'] - take_profit) / trade['entry_price']
                elif current_price >= stop_loss:
                    should_close = True
                    exit_reason = "Stop Loss Hit"
                    pnl = (trade['entry_price'] - current_price) / trade['entry_price']
            
            # Time-based exit (24 hours)
            trade_duration = datetime.now() - trade['entry_time']
            if trade_duration > timedelta(hours=24):
                should_close = True
                exit_reason = "Time Exit"
                if signal_direction == 'BUY':
                    pnl = (current_price - trade['entry_price']) / trade['entry_price']
                else:
                    pnl = (trade['entry_price'] - current_price) / trade['entry_price']
            
            if should_close:
                # Close the trade
                closed_trade = {
                    **trade,
                    'exit_price': current_price,
                    'exit_time': datetime.now(),
                    'pnl': pnl,
                    'exit_reason': exit_reason,
                    'was_correct': pnl > 0
                }
                
                closed_trades.append(closed_trade)
                del self.active_trades[trade_id]
                
                # Record to database
                self._record_trade_to_database(closed_trade)
                
                logger.info(f"📊 Closed {trade_id}: {exit_reason}, P&L: {pnl:+.2%}")
        
        return closed_trades
    
    def _record_trade_to_database(self, trade: Dict):
        """Record completed trade to database"""
        try:
            from core.database import DatabaseManager
            
            db = DatabaseManager()
            
            # Record to agent_performance_log
            sql = f"""
                INSERT INTO agent_performance_log 
                (agent_name, symbol, timestamp, pnl, confidence, was_correct, signal, reasoning)
                VALUES ('{trade['agent_name']}', '{trade['pair']}', '{trade['entry_time']}', {trade['pnl']}, {trade['confidence']}, {trade['was_correct']}, '{trade['signal']}', '{trade['reasoning']}')
            """
            
            with db.get_postgres_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql)
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error recording trade to database: {e}")
    
    def get_active_trades_count(self) -> int:
        """Get number of active trades"""
        return len(self.active_trades)


# Global instance
real_signal_recorder = RealSignalRecorder()


def generate_real_signals(ohlcv_df: pd.DataFrame, agent_name: str, pair: str) -> Dict:
    """Generate real signal from market data"""
    return real_signal_recorder.generate_signal_from_market_data(ohlcv_df, agent_name, pair)


def execute_trade(signal: Dict) -> Optional[str]:
    """Execute a trade based on signal"""
    return real_signal_recorder.execute_trade(signal)


def update_trades_with_market_data(current_prices: Dict[str, float]) -> List[Dict]:
    """Update and close trades with current market data"""
    return real_signal_recorder.close_trades_with_market_data(current_prices)
