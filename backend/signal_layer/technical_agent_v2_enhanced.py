"""
Enhanced Technical Agent V2 - Multi-Timeframe Analysis
Implements your vision for multi-scale technical analysis
"""
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from core.database import DatabaseManager


class TechnicalAgentV2Enhanced:
    """
    Enhanced Technical Analysis Agent with Multi-Timeframe Support
    
    Timeframes:
    - Short-term (1H-4H): Momentum, patterns
    - Medium-term (D1-W1): Support/resistance, moving averages  
    - Long-term (M1-M3): Structural trends, cycles
    """
    
    def __init__(self):
        self.timeframes = {
            'short': {'hours': 4, 'weight': 0.3},    # 1H-4H
            'medium': {'hours': 24, 'weight': 0.4},  # D1
            'long': {'hours': 168, 'weight': 0.3}    # W1
        }
    
    def generate_signal(
        self,
        symbol: str,
        base: str,
        quote: str,
        lookback_hours: int = 168  # 1 week default
    ) -> Dict:
        """
        Generate multi-timeframe technical signal
        
        Returns:
            {
                'signal': -1/0/1,
                'confidence': 0-1,
                'features_used': dict,
                'deterministic_reason': str
            }
        """
        timeframe_signals = {}
        
        # Analyze each timeframe
        for tf_name, tf_config in self.timeframes.items():
            tf_signal = self._analyze_timeframe(symbol, tf_config['hours'])
            timeframe_signals[tf_name] = tf_signal
        
        # Combine timeframe signals with weights
        combined_signal = self._combine_timeframe_signals(timeframe_signals)
        
        # Calculate overall confidence
        confidence = self._calculate_multi_tf_confidence(timeframe_signals)
        
        # Generate detailed reasoning
        reasoning = self._generate_multi_tf_reasoning(timeframe_signals, symbol)
        
        return {
            'signal': combined_signal,
            'confidence': confidence,
            'features_used': {
                'timeframe_signals': timeframe_signals,
                'timeframe_weights': {k: v['weight'] for k, v in self.timeframes.items()},
                'symbol': symbol,
                'analysis_timeframes': list(self.timeframes.keys())
            },
            'deterministic_reason': reasoning
        }
    
    def _analyze_timeframe(self, symbol: str, hours: int) -> Dict:
        """Analyze specific timeframe"""
        try:
            # Get OHLCV data
            ohlcv_data = self._get_ohlcv_data(symbol, hours)
            
            if ohlcv_data.empty or len(ohlcv_data) < 10:
                return {
                    'signal': 0,
                    'confidence': 0.0,
                    'indicators': {},
                    'trend': 'unknown',
                    'momentum': 'neutral'
                }
            
            # Calculate indicators
            indicators = self._calculate_indicators(ohlcv_data, hours)
            
            # Determine trend and momentum
            trend = self._determine_trend(indicators, ohlcv_data)
            momentum = self._determine_momentum(indicators)
            
            # Generate timeframe signal
            signal = self._generate_timeframe_signal(trend, momentum, indicators)
            
            return {
                'signal': signal,
                'confidence': self._calculate_timeframe_confidence(indicators),
                'indicators': indicators,
                'trend': trend,
                'momentum': momentum
            }
            
        except Exception as e:
            print(f"Error analyzing timeframe {hours}H for {symbol}: {e}")
            return {
                'signal': 0,
                'confidence': 0.0,
                'indicators': {},
                'trend': 'error',
                'momentum': 'error'
            }
    
    def _get_ohlcv_data(self, symbol: str, hours: int) -> pd.DataFrame:
        """Get OHLCV data from InfluxDB"""
        try:
            with DatabaseManager.get_influx_client() as client:
                query_api = client.query_api()
                
                # Use the main forex_data bucket for all timeframes
                bucket = "forex_data"
                
                start_time = datetime.now() - timedelta(hours=hours * 2)  # Get more data for indicators
                
                query = f'''
                from(bucket: "{bucket}")
                  |> range(start: {start_time.isoformat()}Z)
                  |> filter(fn: (r) => r["_measurement"] == "ohlcv")
                  |> filter(fn: (r) => r["symbol"] == "{symbol}")
                  |> filter(fn: (r) => r["_field"] == "open" or r["_field"] == "high" or r["_field"] == "low" or r["_field"] == "close")
                  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                  |> sort(columns: ["_time"])
                  |> limit(n: {hours * 2})
                '''
                
                result = query_api.query(query=query)
                
                if not result:
                    return pd.DataFrame()
                
                # Convert to DataFrame
                data = []
                for table in result:
                    for record in table.records:
                        data.append({
                            'timestamp': record.get_time(),
                            'open': record.values.get('open'),
                            'high': record.values.get('high'),
                            'low': record.values.get('low'),
                            'close': record.values.get('close')
                        })
                
                df = pd.DataFrame(data)
                if not df.empty:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df = df.dropna()
                
                return df
                
        except Exception as e:
            print(f"Error getting OHLCV data: {e}")
            return pd.DataFrame()
    
    def _calculate_indicators(self, df: pd.DataFrame, timeframe_hours: int) -> Dict:
        """Calculate technical indicators for timeframe"""
        if df.empty or len(df) < 10:
            return {}
        
        indicators = {}
        
        # Moving averages
        if timeframe_hours <= 4:  # Short-term
            indicators['sma_10'] = df['close'].rolling(10).mean().iloc[-1]
            indicators['sma_20'] = df['close'].rolling(20).mean().iloc[-1]
            indicators['ema_12'] = df['close'].ewm(span=12).mean().iloc[-1]
            indicators['ema_26'] = df['close'].ewm(span=26).mean().iloc[-1]
        elif timeframe_hours <= 24:  # Medium-term
            indicators['sma_20'] = df['close'].rolling(20).mean().iloc[-1]
            indicators['sma_50'] = df['close'].rolling(50).mean().iloc[-1]
            indicators['ema_20'] = df['close'].ewm(span=20).mean().iloc[-1]
        else:  # Long-term
            indicators['sma_50'] = df['close'].rolling(50).mean().iloc[-1]
            indicators['sma_200'] = df['close'].rolling(200).mean().iloc[-1]
        
        # MACD
        if len(df) >= 26:
            ema_12 = df['close'].ewm(span=12).mean().iloc[-1]
            ema_26 = df['close'].ewm(span=26).mean().iloc[-1]
            indicators['macd'] = ema_12 - ema_26
            
            # MACD signal line
            macd_series = df['close'].ewm(span=12).mean() - df['close'].ewm(span=26).mean()
            indicators['macd_signal'] = macd_series.ewm(span=9).mean().iloc[-1]
            indicators['macd_histogram'] = indicators['macd'] - indicators['macd_signal']
        
        # RSI
        if len(df) >= 14:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            indicators['rsi'] = 100 - (100 / (1 + rs.iloc[-1]))
        
        # Bollinger Bands
        if len(df) >= 20:
            sma_20 = df['close'].rolling(20).mean().iloc[-1]
            std_20 = df['close'].rolling(20).std().iloc[-1]
            indicators['bb_upper'] = sma_20 + (std_20 * 2)
            indicators['bb_lower'] = sma_20 - (std_20 * 2)
            indicators['bb_middle'] = sma_20
        
        # Current price relative to indicators
        current_price = df['close'].iloc[-1]
        indicators['price'] = current_price
        
        # Clean up NaN values
        return {k: v for k, v in indicators.items() if pd.notna(v)}
    
    def _determine_trend(self, indicators: Dict, df: pd.DataFrame) -> str:
        """Determine trend based on indicators"""
        if not indicators or 'price' not in indicators:
            return 'unknown'
        
        price = indicators['price']
        trend_signals = []
        
        # Moving average trend
        if 'sma_20' in indicators:
            if price > indicators['sma_20']:
                trend_signals.append('bullish')
            else:
                trend_signals.append('bearish')
        
        if 'sma_50' in indicators:
            if price > indicators['sma_50']:
                trend_signals.append('bullish')
            else:
                trend_signals.append('bearish')
        
        # MACD trend
        if 'macd' in indicators and 'macd_signal' in indicators:
            if indicators['macd'] > indicators['macd_signal']:
                trend_signals.append('bullish')
            else:
                trend_signals.append('bearish')
        
        # Determine overall trend
        if not trend_signals:
            return 'neutral'
        
        bullish_count = trend_signals.count('bullish')
        bearish_count = trend_signals.count('bearish')
        
        if bullish_count > bearish_count:
            return 'bullish'
        elif bearish_count > bullish_count:
            return 'bearish'
        else:
            return 'neutral'
    
    def _determine_momentum(self, indicators: Dict) -> str:
        """Determine momentum based on indicators"""
        if not indicators:
            return 'neutral'
        
        momentum_signals = []
        
        # RSI momentum
        if 'rsi' in indicators:
            rsi = indicators['rsi']
            if rsi > 70:
                momentum_signals.append('overbought')
            elif rsi < 30:
                momentum_signals.append('oversold')
            else:
                momentum_signals.append('neutral')
        
        # Bollinger Bands momentum
        if all(k in indicators for k in ['price', 'bb_upper', 'bb_lower']):
            price = indicators['price']
            if price > indicators['bb_upper']:
                momentum_signals.append('strong_bullish')
            elif price < indicators['bb_lower']:
                momentum_signals.append('strong_bearish')
            else:
                momentum_signals.append('neutral')
        
        # Determine overall momentum
        if not momentum_signals:
            return 'neutral'
        
        # Priority to strong signals
        if 'strong_bullish' in momentum_signals:
            return 'bullish'
        elif 'strong_bearish' in momentum_signals:
            return 'bearish'
        elif 'overbought' in momentum_signals:
            return 'bearish'  # Potential reversal
        elif 'oversold' in momentum_signals:
            return 'bullish'   # Potential reversal
        else:
            return 'neutral'
    
    def _generate_timeframe_signal(self, trend: str, momentum: str, indicators: Dict) -> int:
        """Generate signal for specific timeframe"""
        # Combine trend and momentum
        if trend == 'bullish' and momentum in ['bullish', 'strong_bullish']:
            return 1  # BUY
        elif trend == 'bearish' and momentum in ['bearish', 'strong_bearish']:
            return -1  # SELL
        elif trend == 'bullish' and momentum == 'oversold':
            return 1  # BUY (dip buying)
        elif trend == 'bearish' and momentum == 'overbought':
            return -1  # SELL (selling rally)
        else:
            return 0  # NEUTRAL
    
    def _calculate_timeframe_confidence(self, indicators: Dict) -> float:
        """Calculate confidence for timeframe analysis"""
        if not indicators:
            return 0.0
        
        # Base confidence from indicator availability
        confidence = len(indicators) / 8.0  # Normalize by expected indicators
        
        # Boost confidence if indicators align
        trend_alignment = 0.0
        if 'macd' in indicators and 'macd_signal' in indicators:
            macd_diff = abs(indicators['macd'] - indicators['macd_signal'])
            trend_alignment += min(macd_diff * 10, 0.3)  # Max 0.3 boost
        
        if 'rsi' in indicators:
            rsi = indicators['rsi']
            if 40 <= rsi <= 60:  # Neutral zone (lower confidence)
                trend_alignment -= 0.1
            elif rsi > 70 or rsi < 30:  # Extreme zones (higher confidence)
                trend_alignment += 0.2
        
        return min(max(confidence + trend_alignment, 0.0), 1.0)
    
    def _combine_timeframe_signals(self, timeframe_signals: Dict) -> int:
        """Combine signals from all timeframes"""
        if not timeframe_signals:
            return 0
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for tf_name, tf_config in self.timeframes.items():
            if tf_name in timeframe_signals:
                signal_data = timeframe_signals[tf_name]
                weight = tf_config['weight']
                signal = signal_data['signal']
                confidence = signal_data['confidence']
                
                weighted_score += signal * confidence * weight
                total_weight += confidence * weight
        
        if total_weight == 0:
            return 0
        
        final_score = weighted_score / total_weight
        
        # Convert to signal
        if final_score > 0.3:
            return 1   # BUY
        elif final_score < -0.3:
            return -1  # SELL
        else:
            return 0   # NEUTRAL
    
    def _calculate_multi_tf_confidence(self, timeframe_signals: Dict) -> float:
        """Calculate overall confidence from all timeframes"""
        if not timeframe_signals:
            return 0.0
        
        confidences = []
        for tf_name, signal_data in timeframe_signals.items():
            confidences.append(signal_data['confidence'])
        
        # Average confidence weighted by timeframe importance
        weighted_confidence = 0.0
        total_weight = 0.0
        
        for tf_name, tf_config in self.timeframes.items():
            if tf_name in timeframe_signals:
                confidence = timeframe_signals[tf_name]['confidence']
                weight = tf_config['weight']
                weighted_confidence += confidence * weight
                total_weight += weight
        
        return weighted_confidence / total_weight if total_weight > 0 else 0.0
    
    def _generate_multi_tf_reasoning(self, timeframe_signals: Dict, symbol: str) -> str:
        """Generate detailed reasoning for multi-timeframe analysis"""
        if not timeframe_signals:
            return f"No technical data available for {symbol}"
        
        reasoning_parts = []
        
        for tf_name, signal_data in timeframe_signals.items():
            tf_display = {
                'short': 'Short-term (1H-4H)',
                'medium': 'Medium-term (D1)', 
                'long': 'Long-term (W1)'
            }.get(tf_name, tf_name)
            
            signal_map = {1: 'BUY', -1: 'SELL', 0: 'NEUTRAL'}
            signal = signal_map[signal_data['signal']]
            confidence = signal_data['confidence']
            trend = signal_data.get('trend', 'unknown')
            
            reasoning_parts.append(
                f"{tf_display}: {signal} ({confidence:.0%} confidence, {trend} trend)"
            )
        
        return f"Multi-timeframe analysis for {symbol}: " + "; ".join(reasoning_parts)
