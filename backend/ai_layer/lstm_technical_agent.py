"""
LSTM-Based Technical Agent
Deep learning agent for short-term price prediction and pattern recognition
Uses LSTM/GRU networks to capture temporal dynamics beyond traditional indicators
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
import os
import joblib

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, models, callbacks
    from tensorflow.keras.optimizers import Adam
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    logging.warning("TensorFlow not available for LSTM agent")

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class LSTMSignal:
    """Signal output from LSTM technical agent"""
    timestamp: datetime
    symbol: str
    direction: str  # 'BUY', 'SELL', 'NEUTRAL'
    confidence: float
    predicted_return: float
    probability_up: float
    probability_down: float
    model_uncertainty: float
    feature_importance: Dict[str, float]
    explanation: str


class LSTMTechnicalAgent:
    """
    Deep learning technical agent using LSTM/Transformer architectures
    
    Features:
    - LSTM for short-term price prediction (1-24 hours)
    - Multi-head attention for pattern recognition
    - Uncertainty quantification via dropout
    - Automatic feature engineering
    """
    
    def __init__(
        self,
        sequence_length: int = 60,  # 60 periods = 2.5 days of 1H data
        n_features: int = 20,
        lstm_units: List[int] = [128, 64],
        dropout_rate: float = 0.2,
        learning_rate: float = 0.001,
        model_path: Optional[str] = None
    ):
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.lstm_units = lstm_units
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        self.model = None
        self.scaler = None
        self.feature_names = []
        
        # Model persistence
        self.model_dir = model_path or os.path.join(
            os.path.dirname(__file__), 'models', 'lstm_technical'
        )
        os.makedirs(self.model_dir, exist_ok=True)
        
        if TF_AVAILABLE:
            self._build_model()
            self._load_existing_model()
    
    def _build_model(self):
        """Build LSTM model with attention mechanism"""
        if not TF_AVAILABLE:
            return
        
        inputs = layers.Input(shape=(self.sequence_length, self.n_features))
        
        # First LSTM layer
        x = layers.LSTM(
            self.lstm_units[0],
            return_sequences=True,
            dropout=self.dropout_rate,
            recurrent_dropout=self.dropout_rate
        )(inputs)
        
        # Multi-head attention for pattern recognition
        attention_output = layers.MultiHeadAttention(
            num_heads=4,
            key_dim=32
        )(x, x)
        
        # Second LSTM layer
        x = layers.LSTM(
            self.lstm_units[1],
            dropout=self.dropout_rate,
            recurrent_dropout=self.dropout_rate
        )(attention_output)
        
        # Dense layers
        x = layers.Dense(32, activation='relu')(x)
        x = layers.Dropout(self.dropout_rate)(x)
        
        # Output: probability distribution [down, neutral, up]
        outputs = layers.Dense(3, activation='softmax', name='direction')(x)
        
        # Additional output: predicted return magnitude
        return_output = layers.Dense(1, name='return')(x)
        
        self.model = models.Model(
            inputs=inputs,
            outputs=[outputs, return_output]
        )
        
        self.model.compile(
            optimizer=Adam(learning_rate=self.learning_rate),
            loss={
                'direction': 'categorical_crossentropy',
                'return': 'mse'
            },
            loss_weights={'direction': 0.7, 'return': 0.3},
            metrics={'direction': 'accuracy'}
        )
        
        logger.info(f"LSTM model built: {self.lstm_units} units, {self.sequence_length} sequence")
    
    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Automatic feature engineering from OHLCV data
        
        Creates 20+ technical features:
        - Price-based: returns, log returns, volatility
        - Trend: multiple EMAs, slope
        - Momentum: RSI, MACD, Stochastic
        - Volatility: ATR, Bollinger Bands
        - Volume: OBV, volume trends
        """
        df = df.copy()
        
        # Price features
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        df['price_range'] = (df['high'] - df['low']) / df['close']
        
        # Multiple timeframe EMAs
        for period in [5, 10, 20, 50]:
            df[f'ema_{period}'] = df['close'].ewm(span=period).mean()
            df[f'ema_{period}_ratio'] = df['close'] / df[f'ema_{period}']
        
        # RSI (multiple periods)
        for period in [7, 14, 21]:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            df[f'rsi_{period}'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = df['close'].ewm(span=12).mean()
        ema_26 = df['close'].ewm(span=26).mean()
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(20).mean()
        bb_std = df['close'].rolling(20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # Average True Range (ATR)
        df['tr1'] = df['high'] - df['low']
        df['tr2'] = abs(df['high'] - df['close'].shift(1))
        df['tr3'] = abs(df['low'] - df['close'].shift(1))
        df['true_range'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        df['atr_14'] = df['true_range'].rolling(14).mean()
        df['atr_ratio'] = df['atr_14'] / df['close']
        
        # Stochastic Oscillator
        low_min = df['low'].rolling(14).min()
        high_max = df['high'].rolling(14).max()
        df['stoch_k'] = 100 * (df['close'] - low_min) / (high_max - low_min)
        df['stoch_d'] = df['stoch_k'].rolling(3).mean()
        
        # On Balance Volume (OBV)
        df['obv'] = (np.sign(df['close'].diff()) * df['volume']).cumsum()
        df['obv_ema'] = df['obv'].ewm(span=20).mean()
        
        # Volatility features
        df['volatility_20'] = df['returns'].rolling(20).std()
        df['volatility_change'] = df['volatility_20'].pct_change(5)
        
        # Trend strength (simple slope)
        df['trend_20'] = df['close'].rolling(20).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) == 20 else 0
        )
        
        # Select final features
        feature_cols = [
            'returns', 'log_returns', 'price_range',
            'ema_5_ratio', 'ema_10_ratio', 'ema_20_ratio', 'ema_50_ratio',
            'rsi_7', 'rsi_14', 'rsi_21',
            'macd', 'macd_signal', 'macd_hist',
            'bb_position', 'atr_ratio',
            'stoch_k', 'stoch_d',
            'obv_ema', 'volatility_20', 'trend_20'
        ]
        
        self.feature_names = feature_cols
        return df[feature_cols]
    
    def _prepare_sequences(
        self,
        df: pd.DataFrame,
        target_horizon: int = 6  # Predict 6 periods ahead (6 hours for 1H data)
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sequences for LSTM training
        
        X: (samples, sequence_length, n_features)
        y: (samples, 3) - one-hot encoded direction + return magnitude
        """
        features_df = self._engineer_features(df)
        features_df = features_df.dropna()
        
        if len(features_df) < self.sequence_length + target_horizon:
            return None, None
        
        # Normalize features
        if self.scaler is None:
            from sklearn.preprocessing import StandardScaler
            self.scaler = StandardScaler()
            scaled_features = self.scaler.fit_transform(features_df)
        else:
            scaled_features = self.scaler.transform(features_df)
        
        # Create sequences
        X, y_direction, y_return = [], [], []
        
        for i in range(len(scaled_features) - self.sequence_length - target_horizon):
            X.append(scaled_features[i:i + self.sequence_length])
            
            # Future return
            future_return = (
                df['close'].iloc[i + self.sequence_length + target_horizon] /
                df['close'].iloc[i + self.sequence_length] - 1
            )
            
            # Direction classification
            if future_return > 0.001:  # > 0.1% return = UP
                direction = [0, 0, 1]
            elif future_return < -0.001:  # < -0.1% return = DOWN
                direction = [1, 0, 0]
            else:
                direction = [0, 1, 0]  # NEUTRAL
            
            y_direction.append(direction)
            y_return.append(future_return)
        
        return (
            np.array(X),
            {'direction': np.array(y_direction), 'return': np.array(y_return)}
        )
    
    def train(self, df: pd.DataFrame, epochs: int = 50, batch_size: int = 32) -> Dict:
        """
        Train LSTM on historical data
        
        Returns training metrics
        """
        if not TF_AVAILABLE or self.model is None:
            return {'error': 'TensorFlow not available'}
        
        X, y = self._prepare_sequences(df)
        
        if X is None or len(X) < 100:
            return {'error': 'Insufficient training data'}
        
        # Split train/val
        split_idx = int(0.8 * len(X))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train_dir = y['direction'][:split_idx]
        y_val_dir = y['direction'][split_idx:]
        y_train_ret = y['return'][:split_idx]
        y_val_ret = y['return'][split_idx:]
        
        # Callbacks
        early_stop = callbacks.EarlyStopping(
            monitor='val_direction_accuracy',
            patience=10,
            restore_best_weights=True
        )
        
        reduce_lr = callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=1e-6
        )
        
        # Train
        history = self.model.fit(
            X_train,
            {'direction': y_train_dir, 'return': y_train_ret},
            validation_data=(
                X_val,
                {'direction': y_val_dir, 'return': y_val_ret}
            ),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[early_stop, reduce_lr],
            verbose=1
        )
        
        # Save model
        self._save_model()
        
        return {
            'final_accuracy': float(history.history['direction_accuracy'][-1]),
            'val_accuracy': float(history.history['val_direction_accuracy'][-1]),
            'epochs_trained': len(history.history['loss'])
        }
    
    def predict(self, df: pd.DataFrame, symbol: str) -> LSTMSignal:
        """
        Generate trading signal from LSTM prediction
        
        Returns calibrated signal with uncertainty quantification
        """
        if not TF_AVAILABLE or self.model is None or self.scaler is None:
            # Fallback to rule-based
            return self._fallback_signal(df, symbol)
        
        try:
            # Prepare features
            features_df = self._engineer_features(df)
            features_df = features_df.dropna()
            
            if len(features_df) < self.sequence_length:
                return self._fallback_signal(df, symbol)
            
            # Get last sequence
            last_sequence = features_df.iloc[-self.sequence_length:]
            scaled_sequence = self.scaler.transform(last_sequence)
            X = np.array([scaled_sequence])
            
            # Predict with dropout for uncertainty (Monte Carlo)
            predictions = []
            for _ in range(10):  # MC dropout
                pred = self.model(X, training=True)  # Enable dropout
                predictions.append(pred)
            
            # Average predictions
            direction_probs = np.mean([p[0].numpy() for p in predictions], axis=0)[0]
            returns = [p[1].numpy()[0][0] for p in predictions]
            
            # Uncertainty as std of predictions
            uncertainty = np.std(returns)
            
            # Determine direction
            prob_down, prob_neutral, prob_up = direction_probs
            
            if prob_up > prob_down and prob_up > 0.4:
                direction = 'BUY'
                confidence = prob_up
            elif prob_down > prob_up and prob_down > 0.4:
                direction = 'SELL'
                confidence = prob_down
            else:
                direction = 'NEUTRAL'
                confidence = prob_neutral
            
            # Calibrate confidence with uncertainty
            confidence = confidence * (1 - min(uncertainty * 10, 0.5))
            
            # Feature importance (gradient-based)
            feature_importance = self._get_feature_importance(X)
            
            # Generate explanation
            top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:3]
            explanation = f"LSTM predicts {direction} based on: " + ", ".join([f[0] for f in top_features])
            
            return LSTMSignal(
                timestamp=datetime.now(),
                symbol=symbol,
                direction=direction,
                confidence=float(confidence),
                predicted_return=float(np.mean(returns)),
                probability_up=float(prob_up),
                probability_down=float(prob_down),
                model_uncertainty=float(uncertainty),
                feature_importance=feature_importance,
                explanation=explanation
            )
            
        except Exception as e:
            logger.error(f"LSTM prediction error: {e}")
            return self._fallback_signal(df, symbol)
    
    def _get_feature_importance(self, X: np.ndarray) -> Dict[str, float]:
        """Compute feature importance using gradients"""
        if not TF_AVAILABLE:
            return {}
        
        try:
            X_tensor = tf.convert_to_tensor(X, dtype=tf.float32)
            
            with tf.GradientTape() as tape:
                tape.watch(X_tensor)
                predictions = self.model(X_tensor)
                output = predictions[0][0][2]  # Probability of UP
            
            gradients = tape.gradient(output, X_tensor)
            importance = np.abs(gradients.numpy()[0]).mean(axis=0)
            
            return {
                name: float(imp)
                for name, imp in zip(self.feature_names, importance)
            }
        except:
            return {name: 0.0 for name in self.feature_names}
    
    def _fallback_signal(self, df: pd.DataFrame, symbol: str) -> LSTMSignal:
        """Fallback rule-based signal when LSTM unavailable"""
        # Simple momentum rule
        returns = df['close'].pct_change(20).iloc[-1]
        
        if returns > 0.02:
            direction, confidence = 'BUY', 0.6
        elif returns < -0.02:
            direction, confidence = 'SELL', 0.6
        else:
            direction, confidence = 'NEUTRAL', 0.5
        
        return LSTMSignal(
            timestamp=datetime.now(),
            symbol=symbol,
            direction=direction,
            confidence=confidence,
            predicted_return=float(returns),
            probability_up=0.33,
            probability_down=0.33,
            model_uncertainty=0.5,
            feature_importance={'momentum_20': 1.0},
            explanation=f"Fallback: {direction} based on 20-period momentum"
        )
    
    def _save_model(self):
        """Save model and scaler"""
        if TF_AVAILABLE and self.model is not None:
            model_path = os.path.join(self.model_dir, 'lstm_model.keras')
            self.model.save(model_path)
            
            if self.scaler is not None:
                scaler_path = os.path.join(self.model_dir, 'scaler.joblib')
                joblib.dump(self.scaler, scaler_path)
            
            logger.info(f"Model saved to {self.model_dir}")
    
    def _load_existing_model(self):
        """Load existing model if available"""
        if not TF_AVAILABLE:
            return
        
        model_path = os.path.join(self.model_dir, 'lstm_model.keras')
        scaler_path = os.path.join(self.model_dir, 'scaler.joblib')
        
        if os.path.exists(model_path):
            try:
                self.model = models.load_model(model_path)
                logger.info("Loaded existing LSTM model")
            except Exception as e:
                logger.warning(f"Failed to load model: {e}")
        
        if os.path.exists(scaler_path):
            try:
                self.scaler = joblib.load(scaler_path)
                logger.info("Loaded existing scaler")
            except Exception as e:
                logger.warning(f"Failed to load scaler: {e}")


def create_lstm_agent(model_path: Optional[str] = None) -> LSTMTechnicalAgent:
    """Factory function for LSTM agent"""
    return LSTMTechnicalAgent(model_path=model_path)
