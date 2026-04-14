"""
Meta-Learning for Agent Signal Stacking
Uses meta-learner to combine agent predictions with dynamic weights
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import logging
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import joblib
import os

logger = logging.getLogger(__name__)


@dataclass
class AgentPrediction:
    agent_name: str
    signal: int  # -1, 0, 1
    confidence: float
    features_used: Dict
    timestamp: datetime


@dataclass
class MetaLearningResult:
    final_signal: int
    confidence: float
    meta_features: Dict
    individual_predictions: List[AgentPrediction]
    model_used: str
    train_accuracy: float


class MetaLearner:
    """
    Meta-learner that combines agent predictions using machine learning
    Learns optimal combination weights from historical performance
    """
    
    def __init__(self, model_type: str = 'gradient_boosting'):
        self.model_type = model_type
        self.base_model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
        # Feature history for training
        self.feature_history: deque = deque(maxlen=1000)
        self.label_history: deque = deque(maxlen=1000)
        
        # Agent performance tracking
        self.agent_performance: Dict[str, List[float]] = {
            'technical': [],
            'macro': [],
            'sentiment': [],
            'geopolitical': []
        }
        
        # Model path for persistence
        self.model_path = f"meta_learner_{model_type}.joblib"
        
        self._load_model()
    
    def _create_model(self):
        """Create base model based on type"""
        if self.model_type == 'gradient_boosting':
            return GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=3,
                random_state=42
            )
        elif self.model_type == 'random_forest':
            return RandomForestClassifier(
                n_estimators=100,
                max_depth=5,
                random_state=42
            )
        elif self.model_type == 'logistic':
            return LogisticRegression(
                max_iter=1000,
                random_state=42
            )
        else:
            return GradientBoostingClassifier(n_estimators=100, random_state=42)
    
    def _load_model(self):
        """Load pre-trained model if exists"""
        if os.path.exists(self.model_path):
            try:
                data = joblib.load(self.model_path)
                self.base_model = data['model']
                self.scaler = data['scaler']
                self.is_trained = True
                logger.info(f"✅ Loaded meta-learner model from {self.model_path}")
            except Exception as e:
                logger.warning(f"Could not load model: {e}")
                self.base_model = self._create_model()
        else:
            self.base_model = self._create_model()
    
    def _save_model(self):
        """Save trained model"""
        try:
            data = {
                'model': self.base_model,
                'scaler': self.scaler,
                'timestamp': datetime.now()
            }
            joblib.dump(data, self.model_path)
            logger.info(f"💾 Saved meta-learner model to {self.model_path}")
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def _extract_meta_features(self, predictions: List[AgentPrediction], 
                              market_features: Optional[Dict] = None) -> np.ndarray:
        """
        Extract meta-features from agent predictions
        
        Features:
        - Individual agent signals (-1, 0, 1)
        - Individual agent confidences (0-1)
        - Signal agreement score
        - Weighted average signal
        - Market regime indicators (if provided)
        """
        features = []
        
        # Agent signals and confidences
        agent_signals = {}
        agent_confs = {}
        
        for pred in predictions:
            agent_signals[pred.agent_name] = pred.signal
            agent_confs[pred.agent_name] = pred.confidence
        
        # Ensure all agents are represented
        for agent in ['technical', 'macro', 'sentiment', 'geopolitical']:
            features.append(agent_signals.get(agent, 0))
            features.append(agent_confs.get(agent, 0.5))
        
        # Agreement metrics
        signals = list(agent_signals.values())
        buy_count = signals.count(1)
        sell_count = signals.count(-1)
        neutral_count = signals.count(0)
        
        features.append(buy_count / len(signals) if signals else 0)
        features.append(sell_count / len(signals) if signals else 0)
        features.append(neutral_count / len(signals) if signals else 0)
        
        # Consensus score (max agreement)
        consensus = max(buy_count, sell_count, neutral_count) / len(signals) if signals else 0
        features.append(consensus)
        
        # Weighted signal average
        total_conf = sum(agent_confs.values())
        if total_conf > 0:
            weighted_avg = sum(s * c for s, c in zip(signals, agent_confs.values())) / total_conf
        else:
            weighted_avg = 0
        features.append(weighted_avg)
        
        # Market features if available
        if market_features:
            features.append(market_features.get('volatility', 0.01))
            features.append(market_features.get('trend_strength', 0.5))
            features.append(1.0 if market_features.get('is_trending') else 0.0)
        else:
            features.extend([0.01, 0.5, 0.0])
        
        return np.array(features).reshape(1, -1)
    
    def predict(self, predictions: List[AgentPrediction], 
                market_features: Optional[Dict] = None) -> MetaLearningResult:
        """
        Generate meta-learning prediction
        
        Args:
            predictions: List of agent predictions
            market_features: Optional market regime features
        
        Returns:
            MetaLearningResult with final signal and confidence
        """
        # Extract features
        features = self._extract_meta_features(predictions, market_features)
        
        # Scale features
        if self.is_trained:
            features_scaled = self.scaler.transform(features)
        else:
            features_scaled = features
        
        # If not trained, use rule-based fallback
        if not self.is_trained:
            return self._rule_based_prediction(predictions, features[0])
        
        try:
            # Model prediction
            proba = self.base_model.predict_proba(features_scaled)[0]
            prediction = self.base_model.predict(features_scaled)[0]
            
            # Map to -1, 0, 1
            signal_map = {0: -1, 1: 0, 2: 1}  # Assumes classes are -1, 0, 1 mapped to 0, 1, 2
            final_signal = signal_map.get(prediction, 0)
            
            # Confidence from probability
            confidence = max(proba)
            
            # Feature importance if available
            feature_importance = {}
            if hasattr(self.base_model, 'feature_importances_'):
                feature_names = ['tech_sig', 'tech_conf', 'macro_sig', 'macro_conf',
                               'sent_sig', 'sent_conf', 'geo_sig', 'geo_conf',
                               'buy_ratio', 'sell_ratio', 'neutral_ratio', 'consensus', 'weighted_avg',
                               'volatility', 'trend_strength', 'is_trending']
                for name, importance in zip(feature_names, self.base_model.feature_importances_):
                    feature_importance[name] = float(importance)
            
            return MetaLearningResult(
                final_signal=final_signal,
                confidence=float(confidence),
                meta_features={
                    'raw_features': features[0].tolist(),
                    'feature_importance': feature_importance,
                    'class_probabilities': proba.tolist()
                },
                individual_predictions=predictions,
                model_used=self.model_type,
                train_accuracy=0.0  # Updated during training
            )
            
        except Exception as e:
            logger.error(f"Error in meta-learner prediction: {e}")
            return self._rule_based_prediction(predictions, features[0])
    
    def _rule_based_prediction(self, predictions: List[AgentPrediction], 
                               features: np.ndarray) -> MetaLearningResult:
        """Fallback rule-based prediction"""
        signals = [p.signal for p in predictions]
        confs = [p.confidence for p in predictions]
        
        # Weighted voting
        total_conf = sum(confs)
        if total_conf > 0:
            weighted_signal = sum(s * c for s, c in zip(signals, confs)) / total_conf
        else:
            weighted_signal = 0
        
        # Convert to discrete signal
        if weighted_signal > 0.3:
            final_signal = 1
            confidence = min(weighted_signal, 1.0)
        elif weighted_signal < -0.3:
            final_signal = -1
            confidence = min(abs(weighted_signal), 1.0)
        else:
            final_signal = 0
            confidence = 0.5
        
        return MetaLearningResult(
            final_signal=final_signal,
            confidence=float(confidence),
            meta_features={'rule_based': True, 'weighted_signal': weighted_signal},
            individual_predictions=predictions,
            model_used='rule_based_fallback',
            train_accuracy=0.0
        )
    
    def train(self, X: np.ndarray, y: np.ndarray):
        """
        Train meta-learner on historical data
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Labels (-1, 0, 1 for SELL, NEUTRAL, BUY)
        """
        try:
            # Map labels to 0, 1, 2 for sklearn
            y_mapped = y + 1  # -1->0, 0->1, 1->2
            
            # Scale features
            self.scaler.fit(X)
            X_scaled = self.scaler.transform(X)
            
            # Train model
            self.base_model.fit(X_scaled, y_mapped)
            
            # Calculate accuracy
            accuracy = self.base_model.score(X_scaled, y_mapped)
            
            self.is_trained = True
            self._save_model()
            
            logger.info(f"✅ Meta-learner trained: accuracy={accuracy:.3f}")
            
            return {'success': True, 'accuracy': accuracy}
            
        except Exception as e:
            logger.error(f"Error training meta-learner: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_with_outcome(self, predictions: List[AgentPrediction], 
                           actual_return: float, market_features: Optional[Dict] = None):
        """
        Update meta-learner with actual outcome for online learning
        
        Args:
            predictions: Agent predictions that led to signal
            actual_return: Actual return (-1 to 1 scale)
            market_features: Market conditions
        """
        # Extract features
        features = self._extract_meta_features(predictions, market_features)[0]
        
        # Determine if prediction was correct (simplified)
        # In practice, you'd track the signal generated and compare to actual
        signal = 1 if actual_return > 0.001 else -1 if actual_return < -0.001 else 0
        
        # Store for batch training
        self.feature_history.append(features)
        self.label_history.append(signal)
        
        # Train if enough data
        if len(self.feature_history) >= 100:
            self._batch_train()
    
    def _batch_train(self):
        """Train on accumulated batch"""
        if len(self.feature_history) < 50:
            return
        
        X = np.array(list(self.feature_history))
        y = np.array(list(self.label_history))
        
        result = self.train(X, y)
        
        if result['success']:
            logger.info(f"🔄 Meta-learner batch trained on {len(X)} samples")
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance if available"""
        if not self.is_trained or not hasattr(self.base_model, 'feature_importances_'):
            return {}
        
        feature_names = [
            'technical_signal', 'technical_confidence',
            'macro_signal', 'macro_confidence',
            'sentiment_signal', 'sentiment_confidence',
            'geopolitical_signal', 'geopolitical_confidence',
            'buy_ratio', 'sell_ratio', 'neutral_ratio',
            'consensus_score', 'weighted_signal',
            'market_volatility', 'trend_strength', 'is_trending'
        ]
        
        importance = self.base_model.feature_importances_
        return {name: float(imp) for name, imp in zip(feature_names, importance)}


class StackingEnsemble:
    """
    Advanced stacking ensemble with multiple base models
    and a meta-learner on top
    """
    
    def __init__(self):
        self.meta_learners = {
            'gradient_boosting': MetaLearner('gradient_boosting'),
            'random_forest': MetaLearner('random_forest'),
            'logistic': MetaLearner('logistic')
        }
        self.ensemble_weights = {
            'gradient_boosting': 0.5,
            'random_forest': 0.3,
            'logistic': 0.2
        }
    
    def ensemble_predict(self, predictions: List[AgentPrediction],
                        market_features: Optional[Dict] = None) -> Dict:
        """
        Generate ensemble prediction from multiple meta-learners
        """
        results = {}
        
        # Get predictions from each meta-learner
        for name, learner in self.meta_learners.items():
            result = learner.predict(predictions, market_features)
            results[name] = result
        
        # Weighted ensemble
        weighted_signal = 0
        total_confidence = 0
        
        for name, result in results.items():
            weight = self.ensemble_weights.get(name, 0.33)
            weighted_signal += result.final_signal * result.confidence * weight
            total_confidence += result.confidence * weight
        
        # Normalize
        if total_confidence > 0:
            weighted_signal /= total_confidence
        
        # Convert to discrete
        if weighted_signal > 0.3:
            final_signal = 1
        elif weighted_signal < -0.3:
            final_signal = -1
        else:
            final_signal = 0
        
        confidence = abs(weighted_signal) if weighted_signal != 0 else 0.5
        
        return {
            'signal': final_signal,
            'direction': 'BUY' if final_signal == 1 else 'SELL' if final_signal == -1 else 'NEUTRAL',
            'confidence': float(confidence),
            'individual_results': {
                name: {
                    'signal': r.final_signal,
                    'confidence': r.confidence,
                    'model': r.model_used
                }
                for name, r in results.items()
            },
            'meta_features': results['gradient_boosting'].meta_features if 'gradient_boosting' in results else {}
        }


# Factory functions
def create_meta_learner(model_type: str = 'gradient_boosting') -> MetaLearner:
    """Create meta-learner"""
    return MetaLearner(model_type)


def create_stacking_ensemble() -> StackingEnsemble:
    """Create stacking ensemble"""
    return StackingEnsemble()
