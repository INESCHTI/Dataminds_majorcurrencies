"""
Chart Pattern Recognition using Computer Vision
Identifies technical patterns in price charts using image processing and ML
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
from PIL import Image, ImageDraw, ImageFont
import io
import base64

logger = logging.getLogger(__name__)

@dataclass
class ChartPattern:
    pattern_type: str
    confidence: float
    start_time: datetime
    end_time: datetime
    price_level: float
    direction: str  # "BULLISH", "BEARISH", "NEUTRAL"
    description: str
    key_points: List[Tuple[datetime, float]]
    pattern_data: Dict

@dataclass
class PatternRecognitionResult:
    symbol: str
    timeframe: str
    timestamp: datetime
    patterns: List[ChartPattern]
    overall_sentiment: str
    confidence: float
    chart_image: Optional[str]  # Base64 encoded image
    analysis_summary: str

class ChartPatternRecognizer:
    """Advanced chart pattern recognition using computer vision"""
    
    def __init__(self):
        self.pattern_detectors = {
            'head_shoulders': self._detect_head_shoulders,
            'double_top_bottom': self._detect_double_top_bottom,
            'triangle': self._detect_triangle,
            'flag_pennant': self._detect_flag_pennant,
            'wedge': self._detect_wedge,
            'support_resistance': self._detect_support_resistance,
            'trend_lines': self._detect_trend_lines,
            'candlestick_patterns': self._detect_candlestick_patterns
        }
        
        # Pattern templates
        self.pattern_templates = {
            'head_shoulders': {
                'description': 'Head and Shoulders - Reversal pattern',
                'bullish': False,
                'min_points': 5
            },
            'inverse_head_shoulders': {
                'description': 'Inverse Head and Shoulders - Bullish reversal',
                'bullish': True,
                'min_points': 5
            },
            'double_top': {
                'description': 'Double Top - Bearish reversal',
                'bullish': False,
                'min_points': 4
            },
            'double_bottom': {
                'description': 'Double Bottom - Bullish reversal',
                'bullish': True,
                'min_points': 4
            },
            'ascending_triangle': {
                'description': 'Ascending Triangle - Bullish continuation',
                'bullish': True,
                'min_points': 4
            },
            'descending_triangle': {
                'description': 'Descending Triangle - Bearish continuation',
                'bullish': False,
                'min_points': 4
            },
            'symmetric_triangle': {
                'description': 'Symmetric Triangle - Continuation pattern',
                'bullish': None,
                'min_points': 4
            }
        }
    
    def analyze_chart(self, symbol: str, data: pd.DataFrame, timeframe: str = '1H') -> PatternRecognitionResult:
        """Analyze chart for patterns"""
        try:
            # Prepare data
            if len(data) < 50:
                return self._create_empty_result(symbol, timeframe, "Insufficient data")
            
            # Create chart image
            chart_image = self._create_chart_image(data)
            
            # Detect patterns
            patterns = []
            for pattern_name, detector in self.pattern_detectors.items():
                try:
                    detected_patterns = detector(data, timeframe)
                    patterns.extend(detected_patterns)
                except Exception as e:
                    logger.error(f"Error detecting {pattern_name}: {e}")
            
            # Filter patterns by confidence
            high_confidence_patterns = [p for p in patterns if p.confidence > 0.6]
            
            # Calculate overall sentiment
            overall_sentiment = self._calculate_overall_sentiment(high_confidence_patterns)
            overall_confidence = np.mean([p.confidence for p in high_confidence_patterns]) if high_confidence_patterns else 0.0
            
            # Generate analysis summary
            summary = self._generate_analysis_summary(high_confidence_patterns)
            
            return PatternRecognitionResult(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=datetime.now(),
                patterns=high_confidence_patterns,
                overall_sentiment=overall_sentiment,
                confidence=overall_confidence,
                chart_image=chart_image,
                analysis_summary=summary
            )
            
        except Exception as e:
            logger.error(f"Error analyzing chart for {symbol}: {e}")
            return self._create_empty_result(symbol, timeframe, f"Analysis error: {str(e)}")
    
    def _create_chart_image(self, data: pd.DataFrame, width: int = 800, height: int = 400) -> str:
        """Create chart image from price data"""
        try:
            # Normalize data
            prices = data['close'].values
            high_prices = data['high'].values
            low_prices = data['low'].values
            
            # Create image
            img = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(img)
            
            # Calculate scaling
            price_min = np.min(low_prices)
            price_max = np.max(high_prices)
            price_range = price_max - price_min
            
            margin = 40
            chart_width = width - 2 * margin
            chart_height = height - 2 * margin
            
            # Draw grid
            grid_color = '#e0e0e0'
            for i in range(5):
                y = margin + (chart_height * i / 4)
                draw.line([(margin, y), (width - margin, y)], fill=grid_color)
            
            # Draw price line
            points = []
            for i, price in enumerate(prices[-100:]):  # Last 100 points
                x = margin + (chart_width * i / min(99, len(prices) - 1))
                y = margin + chart_height - ((price - price_min) / price_range * chart_height)
                points.append((x, y))
            
            if len(points) > 1:
                draw.line(points, fill='blue', width=2)
            
            # Draw candlesticks (last 20)
            for i in range(max(0, len(data) - 20), len(data)):
                x = margin + (chart_width * (i - max(0, len(data) - 20)) / 19)
                
                open_price = data.iloc[i]['open']
                close_price = data.iloc[i]['close']
                high_price = data.iloc[i]['high']
                low_price = data.iloc[i]['low']
                
                y_open = margin + chart_height - ((open_price - price_min) / price_range * chart_height)
                y_close = margin + chart_height - ((close_price - price_min) / price_range * chart_height)
                y_high = margin + chart_height - ((high_price - price_min) / price_range * chart_height)
                y_low = margin + chart_height - ((low_price - price_min) / price_range * chart_height)
                
                color = 'green' if close_price >= open_price else 'red'
                
                # Draw high-low line
                draw.line([(x, y_high), (x, y_low)], fill=color, width=1)
                
                # Draw open-close box
                box_height = abs(y_close - y_open)
                box_top = min(y_open, y_close)
                draw.rectangle([(x - 2, box_top), (x + 2, box_top + box_height)], fill=color)
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return img_base64
            
        except Exception as e:
            logger.error(f"Error creating chart image: {e}")
            return ""
    
    def _detect_head_shoulders(self, data: pd.DataFrame, timeframe: str) -> List[ChartPattern]:
        """Detect head and shoulders patterns"""
        patterns = []
        
        try:
            # Find peaks and troughs
            peaks = self._find_peaks(data['high'])
            troughs = self._find_peaks(-data['low'])  # Invert to find troughs
            
            # Look for head and shoulders pattern (3 peaks, middle highest)
            if len(peaks) >= 3:
                for i in range(len(peaks) - 2):
                    peak1_idx = peaks[i]
                    peak2_idx = peaks[i + 1]
                    peak3_idx = peaks[i + 2]
                    
                    peak1 = data.iloc[peak1_idx]['high']
                    peak2 = data.iloc[peak2_idx]['high']
                    peak3 = data.iloc[peak3_idx]['high']
                    
                    # Check if middle peak is highest
                    if peak2 > peak1 and peak2 > peak3:
                        # Check if peaks are roughly similar height (within 10%)
                        if abs(peak1 - peak3) / peak2 < 0.1:
                            # Calculate confidence based on pattern clarity
                            confidence = self._calculate_pattern_confidence(data, [peak1_idx, peak2_idx, peak3_idx])
                            
                            if confidence > 0.6:
                                pattern = ChartPattern(
                                    pattern_type='head_shoulders',
                                    confidence=confidence,
                                    start_time=data.iloc[peak1_idx]['timestamp'],
                                    end_time=data.iloc[peak3_idx]['timestamp'],
                                    price_level=peak2,
                                    direction='BEARISH',
                                    description='Head and Shoulders - Bearish reversal pattern',
                                    key_points=[
                                        (data.iloc[peak1_idx]['timestamp'], peak1),
                                        (data.iloc[peak2_idx]['timestamp'], peak2),
                                        (data.iloc[peak3_idx]['timestamp'], peak3)
                                    ],
                                    pattern_data={
                                        'left_shoulder': peak1,
                                        'head': peak2,
                                        'right_shoulder': peak3,
                                        'neckline': (peak1 + peak3) / 2
                                    }
                                )
                                patterns.append(pattern)
            
        except Exception as e:
            logger.error(f"Error in head and shoulders detection: {e}")
        
        return patterns
    
    def _detect_double_top_bottom(self, data: pd.DataFrame, timeframe: str) -> List[ChartPattern]:
        """Detect double top and double bottom patterns"""
        patterns = []
        
        try:
            peaks = self._find_peaks(data['high'])
            troughs = self._find_peaks(-data['low'])
            
            # Double top detection
            if len(peaks) >= 2:
                for i in range(len(peaks) - 1):
                    peak1_idx = peaks[i]
                    peak2_idx = peaks[i + 1]
                    
                    peak1 = data.iloc[peak1_idx]['high']
                    peak2 = data.iloc[peak2_idx]['high']
                    
                    # Check if peaks are similar height
                    if abs(peak1 - peak2) / max(peak1, peak2) < 0.02:  # Within 2%
                        # Check for valley between peaks
                        valley_data = data.iloc[peak1_idx:peak2_idx + 1]
                        valley_min = valley_data['low'].min()
                        
                        # Check depth
                        depth = (min(peak1, peak2) - valley_min) / min(peak1, peak2)
                        
                        if 0.02 < depth < 0.1:  # 2% to 10% depth
                            confidence = self._calculate_pattern_confidence(data, [peak1_idx, peak2_idx])
                            
                            if confidence > 0.6:
                                pattern = ChartPattern(
                                    pattern_type='double_top',
                                    confidence=confidence,
                                    start_time=data.iloc[peak1_idx]['timestamp'],
                                    end_time=data.iloc[peak2_idx]['timestamp'],
                                    price_level=min(peak1, peak2),
                                    direction='BEARISH',
                                    description='Double Top - Bearish reversal pattern',
                                    key_points=[
                                        (data.iloc[peak1_idx]['timestamp'], peak1),
                                        (data.iloc[peak2_idx]['timestamp'], peak2)
                                    ],
                                    pattern_data={
                                        'top1': peak1,
                                        'top2': peak2,
                                        'valley': valley_min,
                                        'breakout_level': valley_min
                                    }
                                )
                                patterns.append(pattern)
            
            # Double bottom detection (similar logic)
            if len(troughs) >= 2:
                for i in range(len(troughs) - 1):
                    trough1_idx = troughs[i]
                    trough2_idx = troughs[i + 1]
                    
                    trough1 = data.iloc[trough1_idx]['low']
                    trough2 = data.iloc[trough2_idx]['low']
                    
                    if abs(trough1 - trough2) / max(trough1, trough2) < 0.02:
                        peak_data = data.iloc[trough1_idx:trough2_idx + 1]
                        peak_max = peak_data['high'].max()
                        
                        height = (peak_max - max(trough1, trough2)) / max(trough1, trough2)
                        
                        if 0.02 < height < 0.1:
                            confidence = self._calculate_pattern_confidence(data, [trough1_idx, trough2_idx])
                            
                            if confidence > 0.6:
                                pattern = ChartPattern(
                                    pattern_type='double_bottom',
                                    confidence=confidence,
                                    start_time=data.iloc[trough1_idx]['timestamp'],
                                    end_time=data.iloc[trough2_idx]['timestamp'],
                                    price_level=max(trough1, trough2),
                                    direction='BULLISH',
                                    description='Double Bottom - Bullish reversal pattern',
                                    key_points=[
                                        (data.iloc[trough1_idx]['timestamp'], trough1),
                                        (data.iloc[trough2_idx]['timestamp'], trough2)
                                    ],
                                    pattern_data={
                                        'bottom1': trough1,
                                        'bottom2': trough2,
                                        'peak': peak_max,
                                        'breakout_level': peak_max
                                    }
                                )
                                patterns.append(pattern)
            
        except Exception as e:
            logger.error(f"Error in double top/bottom detection: {e}")
        
        return patterns
    
    def _detect_triangle(self, data: pd.DataFrame, timeframe: str) -> List[ChartPattern]:
        """Detect triangle patterns"""
        patterns = []
        
        try:
            # Look for converging trend lines
            if len(data) < 20:
                return patterns
            
            # Find support and resistance trend lines
            support_line = self._find_trend_line(data, 'support')
            resistance_line = self._find_trend_line(data, 'resistance')
            
            if support_line and resistance_line:
                # Check if lines are converging
                support_slope = support_line['slope']
                resistance_slope = resistance_line['slope']
                
                # Triangle pattern: support slope > 0, resistance slope < 0
                if support_slope > 0 and resistance_slope < 0:
                    # Calculate convergence point
                    convergence_x = (resistance_line['intercept'] - support_line['intercept']) / (support_slope - resistance_slope)
                    
                    if 0 < convergence_x < len(data):
                        convergence_price = support_line['slope'] * convergence_x + support_line['intercept']
                        
                        confidence = min(0.8, (abs(support_slope) + abs(resistance_slope)) * 1000)
                        
                        if confidence > 0.6:
                            pattern_type = 'symmetric_triangle'
                            direction = 'NEUTRAL'
                            
                            # Determine triangle type
                            if abs(support_slope) > abs(resistance_slope) * 1.5:
                                pattern_type = 'ascending_triangle'
                                direction = 'BULLISH'
                            elif abs(resistance_slope) > abs(support_slope) * 1.5:
                                pattern_type = 'descending_triangle'
                                direction = 'BEARISH'
                            
                            pattern = ChartPattern(
                                pattern_type=pattern_type,
                                confidence=confidence,
                                start_time=data.iloc[0]['timestamp'],
                                end_time=data.iloc[-1]['timestamp'],
                                price_level=convergence_price,
                                direction=direction,
                                description=f'{pattern_type.replace("_", " ").title()} - Continuation pattern',
                                key_points=[
                                    (data.iloc[0]['timestamp'], support_line['intercept']),
                                    (data.iloc[-1]['timestamp'], support_line['slope'] * len(data) + support_line['intercept'])
                                ],
                                pattern_data={
                                    'support_line': support_line,
                                    'resistance_line': resistance_line,
                                    'convergence_point': (convergence_x, convergence_price)
                                }
                            )
                            patterns.append(pattern)
            
        except Exception as e:
            logger.error(f"Error in triangle detection: {e}")
        
        return patterns
    
    def _detect_flag_pennant(self, data: pd.DataFrame, timeframe: str) -> List[ChartPattern]:
        """Detect flag and pennant patterns"""
        patterns = []
        
        try:
            # Look for strong price movement followed by consolidation
            if len(data) < 30:
                return patterns
            
            # Find strong trend
            price_change = (data.iloc[-1]['close'] - data.iloc[0]['close']) / data.iloc[0]['close']
            
            if abs(price_change) > 0.02:  # At least 2% move
                # Look for consolidation in last third of data
                consolidation_start = int(len(data) * 0.7)
                consolidation_data = data.iloc[consolidation_start:]
                
                # Check for consolidation (low volatility)
                consolidation_volatility = consolidation_data['close'].std() / consolidation_data['close'].mean()
                
                if consolidation_volatility < 0.01:  # Low volatility
                    confidence = min(0.9, abs(price_change) * 20)
                    
                    if confidence > 0.6:
                        pattern_type = 'flag' if consolidation_volatility < 0.005 else 'pennant'
                        direction = 'BULLISH' if price_change > 0 else 'BEARISH'
                        
                        pattern = ChartPattern(
                            pattern_type=pattern_type,
                            confidence=confidence,
                            start_time=data.iloc[consolidation_start]['timestamp'],
                            end_time=data.iloc[-1]['timestamp'],
                            price_level=consolidation_data['close'].mean(),
                            direction=direction,
                            description=f'{pattern_type.title()} - Continuation pattern',
                            key_points=[
                                (data.iloc[consolidation_start]['timestamp'], consolidation_data.iloc[0]['close']),
                                (data.iloc[-1]['timestamp'], consolidation_data.iloc[-1]['close'])
                            ],
                            pattern_data={
                                'trend_strength': abs(price_change),
                                'consolidation_volatility': consolidation_volatility,
                                'breakout_expected': direction
                            }
                        )
                        patterns.append(pattern)
            
        except Exception as e:
            logger.error(f"Error in flag/pennant detection: {e}")
        
        return patterns
    
    def _detect_wedge(self, data: pd.DataFrame, timeframe: str) -> List[ChartPattern]:
        """Detect wedge patterns"""
        patterns = []
        
        try:
            # Similar to triangle but both lines slope in same direction
            support_line = self._find_trend_line(data, 'support')
            resistance_line = self._find_trend_line(data, 'resistance')
            
            if support_line and resistance_line:
                support_slope = support_line['slope']
                resistance_slope = resistance_line['slope']
                
                # Rising wedge: both slopes positive, resistance steeper
                if support_slope > 0 and resistance_slope > 0 and resistance_slope > support_slope * 1.5:
                    confidence = min(0.8, (resistance_slope - support_slope) * 1000)
                    
                    if confidence > 0.6:
                        pattern = ChartPattern(
                            pattern_type='rising_wedge',
                            confidence=confidence,
                            start_time=data.iloc[0]['timestamp'],
                            end_time=data.iloc[-1]['timestamp'],
                            price_level=data.iloc[-1]['close'],
                            direction='BEARISH',
                            description='Rising Wedge - Bearish reversal pattern',
                            key_points=[
                                (data.iloc[0]['timestamp'], support_line['intercept']),
                                (data.iloc[-1]['timestamp'], support_line['slope'] * len(data) + support_line['intercept'])
                            ],
                            pattern_data={
                                'support_line': support_line,
                                'resistance_line': resistance_line,
                                'convergence_expected': True
                            }
                        )
                        patterns.append(pattern)
                
                # Falling wedge: both slopes negative, support steeper
                elif support_slope < 0 and resistance_slope < 0 and abs(support_slope) > abs(resistance_slope) * 1.5:
                    confidence = min(0.8, (abs(support_slope) - abs(resistance_slope)) * 1000)
                    
                    if confidence > 0.6:
                        pattern = ChartPattern(
                            pattern_type='falling_wedge',
                            confidence=confidence,
                            start_time=data.iloc[0]['timestamp'],
                            end_time=data.iloc[-1]['timestamp'],
                            price_level=data.iloc[-1]['close'],
                            direction='BULLISH',
                            description='Falling Wedge - Bullish reversal pattern',
                            key_points=[
                                (data.iloc[0]['timestamp'], support_line['intercept']),
                                (data.iloc[-1]['timestamp'], support_line['slope'] * len(data) + support_line['intercept'])
                            ],
                            pattern_data={
                                'support_line': support_line,
                                'resistance_line': resistance_line,
                                'convergence_expected': True
                            }
                        )
                        patterns.append(pattern)
            
        except Exception as e:
            logger.error(f"Error in wedge detection: {e}")
        
        return patterns
    
    def _detect_support_resistance(self, data: pd.DataFrame, timeframe: str) -> List[ChartPattern]:
        """Detect support and resistance levels"""
        patterns = []
        
        try:
            # Find price levels with multiple touches
            price_levels = {}
            
            for i in range(len(data)):
                price = data.iloc[i]['close']
                # Round to nearest 0.0001 for FX pairs
                rounded_price = round(price * 10000) / 10000
                
                if rounded_price not in price_levels:
                    price_levels[rounded_price] = []
                price_levels[rounded_price].append(i)
            
            # Find levels with multiple touches
            for price, touches in price_levels.items():
                if len(touches) >= 3:  # At least 3 touches
                    # Check if touches are spread out
                    if touches[-1] - touches[0] > len(data) * 0.3:  # Spread across 30% of data
                        confidence = min(0.9, len(touches) / 10)
                        
                        # Determine if support or resistance
                        recent_prices = data.iloc[max(0, len(data) - 10):]['close']
                        
                        if price < recent_prices.mean():
                            level_type = 'support'
                            direction = 'BULLISH'
                        else:
                            level_type = 'resistance'
                            direction = 'BEARISH'
                        
                        pattern = ChartPattern(
                            pattern_type=f'{level_type}_level',
                            confidence=confidence,
                            start_time=data.iloc[touches[0]]['timestamp'],
                            end_time=data.iloc[touches[-1]]['timestamp'],
                            price_level=price,
                            direction=direction,
                            description=f'{level_type.title()} Level - {len(touches)} touches',
                            key_points=[(data.iloc[t]['timestamp'], price) for t in touches],
                            pattern_data={
                                'level_type': level_type,
                                'touches': len(touches),
                                'strength': confidence
                            }
                        )
                        patterns.append(pattern)
            
        except Exception as e:
            logger.error(f"Error in support/resistance detection: {e}")
        
        return patterns
    
    def _detect_trend_lines(self, data: pd.DataFrame, timeframe: str) -> List[ChartPattern]:
        """Detect trend lines"""
        patterns = []
        
        try:
            # Support trend line
            support_line = self._find_trend_line(data, 'support')
            if support_line:
                confidence = min(0.8, abs(support_line['slope']) * 500)
                
                if confidence > 0.5:
                    direction = 'BULLISH' if support_line['slope'] > 0 else 'BEARISH'
                    
                    pattern = ChartPattern(
                        pattern_type='support_trend_line',
                        confidence=confidence,
                        start_time=data.iloc[0]['timestamp'],
                        end_time=data.iloc[-1]['timestamp'],
                        price_level=support_line['slope'] * len(data) + support_line['intercept'],
                        direction=direction,
                        description=f'Support Trend Line - {direction.lower()} trend',
                        key_points=[
                            (data.iloc[0]['timestamp'], support_line['intercept']),
                            (data.iloc[-1]['timestamp'], support_line['slope'] * len(data) + support_line['intercept'])
                        ],
                        pattern_data={
                            'line_type': 'support',
                            'slope': support_line['slope'],
                            'intercept': support_line['intercept']
                        }
                    )
                    patterns.append(pattern)
            
            # Resistance trend line
            resistance_line = self._find_trend_line(data, 'resistance')
            if resistance_line:
                confidence = min(0.8, abs(resistance_line['slope']) * 500)
                
                if confidence > 0.5:
                    direction = 'BULLISH' if resistance_line['slope'] > 0 else 'BEARISH'
                    
                    pattern = ChartPattern(
                        pattern_type='resistance_trend_line',
                        confidence=confidence,
                        start_time=data.iloc[0]['timestamp'],
                        end_time=data.iloc[-1]['timestamp'],
                        price_level=resistance_line['slope'] * len(data) + resistance_line['intercept'],
                        direction=direction,
                        description=f'Resistance Trend Line - {direction.lower()} trend',
                        key_points=[
                            (data.iloc[0]['timestamp'], resistance_line['intercept']),
                            (data.iloc[-1]['timestamp'], resistance_line['slope'] * len(data) + resistance_line['intercept'])
                        ],
                        pattern_data={
                            'line_type': 'resistance',
                            'slope': resistance_line['slope'],
                            'intercept': resistance_line['intercept']
                        }
                    )
                    patterns.append(pattern)
            
        except Exception as e:
            logger.error(f"Error in trend line detection: {e}")
        
        return patterns
    
    def _detect_candlestick_patterns(self, data: pd.DataFrame, timeframe: str) -> List[ChartPattern]:
        """Detect candlestick patterns"""
        patterns = []
        
        try:
            if len(data) < 3:
                return patterns
            
            # Check recent candles for patterns
            for i in range(len(data) - 2, len(data)):
                candle = data.iloc[i]
                prev_candle = data.iloc[i - 1]
                prev2_candle = data.iloc[i - 2] if i >= 2 else None
                
                # Doji pattern
                body_size = abs(candle['close'] - candle['open'])
                range_size = candle['high'] - candle['low']
                
                if body_size < range_size * 0.1:  # Doji
                    pattern = ChartPattern(
                        pattern_type='doji',
                        confidence=0.7,
                        start_time=candle['timestamp'],
                        end_time=candle['timestamp'],
                        price_level=candle['close'],
                        direction='NEUTRAL',
                        description='Doji - Indecision pattern',
                        key_points=[(candle['timestamp'], candle['close'])],
                        pattern_data={'body_size': body_size, 'range_size': range_size}
                    )
                    patterns.append(pattern)
                
                # Hammer pattern
                if prev2_candle:
                    lower_shadow = candle['close'] - candle['low'] if candle['close'] > candle['open'] else candle['open'] - candle['low']
                    upper_shadow = candle['high'] - candle['close'] if candle['close'] > candle['open'] else candle['high'] - candle['open']
                    
                    if lower_shadow > range_size * 0.6 and upper_shadow < range_size * 0.1:
                        # Check if in downtrend
                        if prev2_candle['close'] > prev_candle['close'] > candle['open']:
                            pattern = ChartPattern(
                                pattern_type='hammer',
                                confidence=0.75,
                                start_time=candle['timestamp'],
                                end_time=candle['timestamp'],
                                price_level=candle['close'],
                                direction='BULLISH',
                                description='Hammer - Bullish reversal pattern',
                                key_points=[(candle['timestamp'], candle['close'])],
                                pattern_data={'lower_shadow': lower_shadow, 'upper_shadow': upper_shadow}
                            )
                            patterns.append(pattern)
            
        except Exception as e:
            logger.error(f"Error in candlestick pattern detection: {e}")
        
        return patterns
    
    def _find_peaks(self, data: np.ndarray) -> List[int]:
        """Find peaks in data"""
        peaks = []
        
        for i in range(1, len(data) - 1):
            if data[i] > data[i - 1] and data[i] > data[i + 1]:
                peaks.append(i)
        
        return peaks
    
    def _find_trend_line(self, data: pd.DataFrame, line_type: str) -> Optional[Dict]:
        """Find trend line (support or resistance)"""
        try:
            if line_type == 'support':
                prices = data['low']
            else:  # resistance
                prices = data['high']
            
            # Use linear regression to find trend line
            x = np.arange(len(prices))
            y = prices.values
            
            # Calculate coefficients
            coeffs = np.polyfit(x, y, 1)
            slope, intercept = coeffs
            
            # Calculate R-squared
            y_pred = slope * x + intercept
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            
            # Return trend line if it's reasonably good fit
            if r_squared > 0.3:
                return {
                    'slope': slope,
                    'intercept': intercept,
                    'r_squared': r_squared
                }
            
        except Exception as e:
            logger.error(f"Error finding trend line: {e}")
        
        return None
    
    def _calculate_pattern_confidence(self, data: pd.DataFrame, point_indices: List[int]) -> float:
        """Calculate confidence score for pattern"""
        try:
            # Base confidence on pattern clarity and data quality
            base_confidence = 0.6
            
            # Adjust based on volume (if available)
            if 'volume' in data.columns:
                volumes = data.iloc[point_indices]['volume']
                volume_consistency = 1 - (volumes.std() / volumes.mean()) if volumes.mean() > 0 else 0
                base_confidence += volume_consistency * 0.2
            
            # Adjust based on price action smoothness
            price_changes = data['close'].pct_change().abs()
            smoothness = 1 - price_changes.std() if len(price_changes) > 1 else 0
            base_confidence += smoothness * 0.2
            
            return min(0.95, max(0.0, base_confidence))
            
        except Exception as e:
            logger.error(f"Error calculating pattern confidence: {e}")
            return 0.6
    
    def _calculate_overall_sentiment(self, patterns: List[ChartPattern]) -> str:
        """Calculate overall sentiment from patterns"""
        if not patterns:
            return 'NEUTRAL'
        
        bullish_score = sum(p.confidence for p in patterns if p.direction == 'BULLISH')
        bearish_score = sum(p.confidence for p in patterns if p.direction == 'BEARISH')
        
        if bullish_score > bearish_score * 1.2:
            return 'BULLISH'
        elif bearish_score > bullish_score * 1.2:
            return 'BEARISH'
        else:
            return 'NEUTRAL'
    
    def _generate_analysis_summary(self, patterns: List[ChartPattern]) -> str:
        """Generate analysis summary"""
        if not patterns:
            return "No significant patterns detected."
        
        pattern_types = [p.pattern_type for p in patterns]
        directions = [p.direction for p in patterns]
        avg_confidence = np.mean([p.confidence for p in patterns])
        
        summary = f"Detected {len(patterns)} patterns with {avg_confidence:.1%} average confidence. "
        summary += f"Patterns: {', '.join(set(pattern_types))}. "
        summary += f"Overall bias: {self._calculate_overall_sentiment(patterns)}."
        
        return summary
    
    def _create_empty_result(self, symbol: str, timeframe: str, error_message: str) -> PatternRecognitionResult:
        """Create empty result when analysis fails"""
        return PatternRecognitionResult(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=datetime.now(),
            patterns=[],
            overall_sentiment='NEUTRAL',
            confidence=0.0,
            chart_image="",
            analysis_summary=error_message
        )

# Factory function
def create_pattern_recognizer() -> ChartPatternRecognizer:
    """Create chart pattern recognizer"""
    return ChartPatternRecognizer()
