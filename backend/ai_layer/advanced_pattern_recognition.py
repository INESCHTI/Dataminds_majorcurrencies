"""
Advanced Pattern Recognition using TensorFlow/CNN
Replaces basic PIL with deep learning for chart pattern detection
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, models
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    logging.warning("TensorFlow not available - using fallback pattern detection")

logger = logging.getLogger(__name__)


@dataclass
class AdvancedPattern:
    pattern_type: str
    confidence: float
    start_time: datetime
    end_time: datetime
    direction: str
    price_level: float
    cnn_confidence: float
    technical_confidence: float


class CNNPatternRecognizer:
    """
    CNN-based chart pattern recognition
    Uses ResNet-style architecture for image classification
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.pattern_classes = [
            'head_shoulders', 'inverse_head_shoulders', 'double_top',
            'double_bottom', 'ascending_triangle', 'descending_triangle',
            'symmetric_triangle', 'rising_wedge', 'falling_wedge',
            'bull_flag', 'bear_flag', 'cup_handle'
        ]
        
        if TF_AVAILABLE:
            if model_path and tf.io.gfile.exists(model_path):
                self.model = tf.keras.models.load_model(model_path)
            else:
                self.model = self._build_model()
                logger.info("Built new CNN pattern recognition model")
        else:
            logger.warning("TensorFlow not available - CNN features disabled")
    
    def _build_model(self) -> "keras.Model":
        """Build ResNet-style CNN for pattern recognition"""
        
        def residual_block(x, filters, kernel_size=3):
            """Residual block with skip connection"""
            shortcut = x
            
            x = layers.Conv2D(filters, kernel_size, padding='same')(x)
            x = layers.BatchNormalization()(x)
            x = layers.ReLU()(x)
            
            x = layers.Conv2D(filters, kernel_size, padding='same')(x)
            x = layers.BatchNormalization()(x)
            
            # Skip connection
            if shortcut.shape[-1] != filters:
                shortcut = layers.Conv2D(filters, 1, padding='same')(shortcut)
            
            x = layers.Add()([shortcut, x])
            x = layers.ReLU()(x)
            return x
        
        # Input: 224x224 RGB chart images
        inputs = keras.Input(shape=(224, 224, 3))
        
        # Initial convolution
        x = layers.Conv2D(64, 7, strides=2, padding='same')(inputs)
        x = layers.BatchNormalization()(x)
        x = layers.ReLU()(x)
        x = layers.MaxPooling2D(3, strides=2, padding='same')(x)
        
        # Residual blocks
        x = residual_block(x, 64)
        x = residual_block(x, 64)
        x = residual_block(x, 128, strides=2)
        x = residual_block(x, 128)
        x = residual_block(x, 256, strides=2)
        x = residual_block(x, 256)
        
        # Global average pooling
        x = layers.GlobalAveragePooling2D()(x)
        x = layers.Dropout(0.5)(x)
        
        # Output: Multi-label classification for patterns
        outputs = layers.Dense(len(self.pattern_classes), activation='sigmoid')(x)
        
        model = keras.Model(inputs, outputs)
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy', tf.keras.metrics.Precision(), tf.keras.metrics.Recall()]
        )
        
        return model
    
    def chart_to_image(self, df: pd.DataFrame, width: int = 224, height: int = 224) -> np.ndarray:
        """
        Convert OHLCV data to normalized image array for CNN input
        """
        try:
            import cv2
            
            # Create blank canvas
            img = np.zeros((height, width, 3), dtype=np.float32)
            
            # Normalize price data to image coordinates
            prices = df['close'].values
            if len(prices) < 20:
                return img
            
            price_min = prices.min()
            price_max = prices.max()
            price_range = price_max - price_min
            
            if price_range == 0:
                return img
            
            # Map prices to image coordinates
            n_points = min(len(prices), width)
            x_coords = np.linspace(0, width - 1, n_points, dtype=np.int32)
            
            for i in range(n_points):
                price_idx = int(i * len(prices) / n_points)
                price = prices[price_idx]
                y = int((price_max - price) / price_range * (height - 20)) + 10
                y = np.clip(y, 0, height - 1)
                
                # Draw price line (green for up, red for down)
                if i > 0:
                    prev_price = prices[int((i - 1) * len(prices) / n_points)]
                    color = [0, 1, 0] if price >= prev_price else [1, 0, 0]
                    img[y, x_coords[i]] = color
            
            # Add moving averages as blue channel
            if 'sma_20' in df.columns:
                sma = df['sma_20'].values
                for i in range(n_points):
                    price_idx = int(i * len(sma) / n_points)
                    price = sma[price_idx]
                    y = int((price_max - price) / price_range * (height - 20)) + 10
                    y = np.clip(y, 0, height - 1)
                    img[y, x_coords[i], 2] = 1.0
            
            return img
            
        except ImportError:
            # Fallback without OpenCV
            return self._chart_to_image_basic(df, width, height)
    
    def _chart_to_image_basic(self, df: pd.DataFrame, width: int, height: int) -> np.ndarray:
        """Fallback image generation without OpenCV"""
        img = np.zeros((height, width, 3), dtype=np.float32)
        prices = df['close'].values
        
        if len(prices) < 20:
            return img
        
        price_min, price_max = prices.min(), prices.max()
        price_range = price_max - price_min
        
        if price_range == 0:
            return img
        
        n_points = min(len(prices), width)
        for i in range(n_points):
            price_idx = int(i * len(prices) / n_points)
            price = prices[price_idx]
            y = int((price_max - price) / price_range * (height - 20)) + 10
            if 0 <= y < height and i < width:
                img[y, i, 0] = 1.0  # Red channel
        
        return img
    
    def predict_patterns(self, df: pd.DataFrame) -> List[AdvancedPattern]:
        """Predict patterns using CNN + traditional analysis"""
        patterns = []
        
        if not TF_AVAILABLE or self.model is None:
            logger.warning("CNN not available - returning empty patterns")
            return patterns
        
        try:
            # Convert to image
            img = self.chart_to_image(df)
            img_batch = np.expand_dims(img, axis=0)  # Add batch dimension
            
            # CNN prediction
            predictions = self.model.predict(img_batch, verbose=0)[0]
            
            # Create pattern objects for high-confidence detections
            for i, (pattern_name, confidence) in enumerate(zip(self.pattern_classes, predictions)):
                if confidence > 0.6:  # Threshold
                    direction = self._get_pattern_direction(pattern_name)
                    
                    pattern = AdvancedPattern(
                        pattern_type=pattern_name,
                        confidence=float(confidence),
                        start_time=df.index[0] if hasattr(df.index[0], 'to_pydatetime') else df.iloc[0]['timestamp'],
                        end_time=df.index[-1] if hasattr(df.index[-1], 'to_pydatetime') else df.iloc[-1]['timestamp'],
                        direction=direction,
                        price_level=float(df['close'].iloc[-1]),
                        cnn_confidence=float(confidence),
                        technical_confidence=0.0  # Will be filled by traditional analysis
                    )
                    patterns.append(pattern)
            
            # Sort by confidence
            patterns.sort(key=lambda x: x.confidence, reverse=True)
            
        except Exception as e:
            logger.error(f"Error in CNN pattern prediction: {e}")
        
        return patterns
    
    def _get_pattern_direction(self, pattern_name: str) -> str:
        """Get expected direction for pattern type"""
        bullish_patterns = [
            'inverse_head_shoulders', 'double_bottom', 'ascending_triangle',
            'falling_wedge', 'bull_flag', 'cup_handle'
        ]
        bearish_patterns = [
            'head_shoulders', 'double_top', 'descending_triangle',
            'rising_wedge', 'bear_flag'
        ]
        
        if pattern_name in bullish_patterns:
            return 'BULLISH'
        elif pattern_name in bearish_patterns:
            return 'BEARISH'
        return 'NEUTRAL'


class HybridPatternRecognizer:
    """
    Combines CNN deep learning with traditional technical analysis
    for robust pattern recognition
    """
    
    def __init__(self):
        self.cnn_recognizer = CNNPatternRecognizer()
        self.technical_recognizer = None  # Will import from chart_pattern_recognition.py
        self.pattern_weights = {
            'cnn': 0.6,
            'technical': 0.4
        }
    
    def analyze(self, df: pd.DataFrame, symbol: str = "UNKNOWN") -> Dict:
        """
        Hybrid pattern analysis combining CNN and traditional methods
        """
        from ai_layer.chart_pattern_recognition import ChartPatternRecognizer
        
        # Get CNN patterns
        cnn_patterns = self.cnn_recognizer.predict_patterns(df)
        
        # Get traditional patterns
        traditional = ChartPatternRecognizer()
        traditional_result = traditional.analyze_chart(symbol, df)
        
        # Merge and weight predictions
        merged_patterns = self._merge_patterns(
            cnn_patterns, 
            traditional_result.patterns if hasattr(traditional_result, 'patterns') else []
        )
        
        return {
            'symbol': symbol,
            'patterns': merged_patterns,
            'cnn_count': len(cnn_patterns),
            'traditional_count': len(traditional_result.patterns if hasattr(traditional_result, 'patterns') else []),
            'hybrid_confidence': np.mean([p['confidence'] for p in merged_patterns]) if merged_patterns else 0.0
        }
    
    def _merge_patterns(self, cnn_patterns: List[AdvancedPattern], 
                       technical_patterns: List) -> List[Dict]:
        """Merge CNN and technical patterns with weighted confidence"""
        merged = []
        
        # Add CNN patterns
        for p in cnn_patterns:
            merged.append({
                'type': p.pattern_type,
                'confidence': p.confidence * self.pattern_weights['cnn'],
                'direction': p.direction,
                'source': 'cnn',
                'price_level': p.price_level
            })
        
        # Add technical patterns
        for p in technical_patterns:
            if hasattr(p, 'pattern_type'):
                merged.append({
                    'type': p.pattern_type,
                    'confidence': p.confidence * self.pattern_weights['technical'],
                    'direction': p.direction if hasattr(p, 'direction') else 'NEUTRAL',
                    'source': 'technical',
                    'price_level': p.price_level if hasattr(p, 'price_level') else 0.0
                })
        
        # Sort by confidence
        merged.sort(key=lambda x: x['confidence'], reverse=True)
        return merged


# Factory functions
def create_cnn_recognizer(model_path: Optional[str] = None) -> CNNPatternRecognizer:
    """Create CNN pattern recognizer"""
    return CNNPatternRecognizer(model_path)


def create_hybrid_recognizer() -> HybridPatternRecognizer:
    """Create hybrid pattern recognizer"""
    return HybridPatternRecognizer()
