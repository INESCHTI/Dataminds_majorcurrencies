"""
XGBoost-Based Coordinator Agent
Advanced meta-learning signal fusion using gradient boosting
Replaces weighted voting with learned agent interactions
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
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
    logging.warning("XGBoost not available")

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class CoordinatorOutput:
    """Enhanced signal output from XGBoost coordinator"""
    timestamp: datetime
    symbol: str
    direction: str  # 'BUY', 'SELL', 'NEUTRAL'
    confidence: float
    expected_return: float
    probability_up: float
    probability_down: float
    agent_contributions: Dict[str, float]  # How much each agent contributed
    agent_disagreement: float  # Measure of agent consensus
    regime_adjusted: bool
    risk_adjusted_confidence: float
    explanation: str
    feature_importance: Dict[str, float]
    shap_explanation: Optional[Dict[str, float]]


class XGBoostCoordinator:
    """
    XGBoost-based coordinator for agent signal fusion
    
    Advantages over weighted voting:
    - Learns non-linear agent interactions
    - Captures context-dependent agent reliability
    - Provides SHAP-based explainability
    - Handles missing agent signals gracefully
    
    Input features:
    - Individual agent signals (direction + confidence)
    - Agent historical performance (rolling Sharpe)
    - Market regime indicators
    - Cross-agent correlation structure
    """
    
    def __init__(
        self,
        agents: List[str] = None,
        n_estimators: int = 300,
        max_depth: int = 8,
        learning_rate: float = 0.03,
        model_path: Optional[str] = None
    ):
        self.agents = agents or ['technical', 'macro', 'sentiment', 'geopolitical', 'lstm']
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.model = None
        self.shap_explainer = None
        self.agent_performance_history = {agent: [] for agent in self.agents}
        
        # Model persistence
        self.model_dir = model_path or os.path.join(
            os.path.dirname(__file__), 'models', 'xgboost_coordinator'
        )
        os.makedirs(self.model_dir, exist_ok=True)
        
        if XGB_AVAILABLE:
            self._build_model()
            self._load_existing_model()
    
    def _build_model(self):
        """Build XGBoost classifier for signal fusion"""
        if not XGB_AVAILABLE:
            return
        
        self.model = xgb.XGBClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            subsample=0.8,
            colsample_bytree=0.9,
            colsample_bylevel=0.8,
            min_child_weight=3,
            gamma=0.1,
            reg_alpha=0.1,
            reg_lambda=1.0,
            objective='multi:softprob',
            num_class=3,
            eval_metric='mlogloss',
            random_state=42,
            n_jobs=-1
        )
    
    def _create_meta_features(
        self,
        agent_signals: Dict[str, Dict],
        market_regime: Optional[Dict] = None,
        price_data: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Create meta-features from agent signals
        
        Features capture:
        - Individual agent predictions
        - Confidence calibration
        - Agent interactions
        - Historical performance
        - Market context
        """
        features = {}
        
        # 1. Individual agent signals
        for agent in self.agents:
            signal = agent_signals.get(agent, {})
            
            # Direction encoded as -1, 0, 1
            direction = signal.get('signal', 0)
            if isinstance(direction, str):
                direction = {'BUY': 1, 'SELL': -1, 'NEUTRAL': 0}.get(direction, 0)
            
            features[f'{agent}_signal'] = direction
            features[f'{agent}_confidence'] = signal.get('confidence', 0.5)
            
            # Signal strength = direction * confidence
            features[f'{agent}_strength'] = direction * signal.get('confidence', 0.5)
        
        # 2. Agent consensus features
        signals = [features[f'{a}_signal'] for a in self.agents]
        confidences = [features[f'{a}_confidence'] for a in self.agents]
        strengths = [features[f'{a}_strength'] for a in self.agents]
        
        # Simple voting
        features['consensus_signal'] = np.sign(np.mean(signals))
        features['consensus_confidence'] = np.mean(confidences)
        
        # Weighted voting (baseline)
        features['weighted_signal'] = np.sum(strengths) / (sum(confidences) + 1e-6)
        
        # Agreement metrics
        features['signal_std'] = np.std(signals)
        features['confidence_std'] = np.std(confidences)
        
        # Agreement ratio (how many agree with majority)
        majority_signal = np.sign(np.sum(signals))
        agreeing = sum(1 for s in signals if np.sign(s) == majority_signal)
        features['agreement_ratio'] = agreeing / len(signals)
        
        # Disagreement (used for uncertainty)
        features['agent_disagreement'] = 1 - features['agreement_ratio']
        
        # 3. Agent performance features (rolling)
        for agent in self.agents:
            history = self.agent_performance_history.get(agent, [])
            if len(history) >= 5:
                features[f'{agent}_recent_accuracy'] = np.mean(history[-5:])
                features[f'{agent}_performance_trend'] = history[-1] - history[-5] if len(history) >= 5 else 0
            else:
                features[f'{agent}_recent_accuracy'] = 0.5
                features[f'{agent}_performance_trend'] = 0
        
        # 4. Market regime features
        if market_regime:
            features['regime_id'] = market_regime.get('regime_id', 1)
            features['regime_confidence'] = market_regime.get('confidence', 0.5)
            features['volatility_regime'] = market_regime.get('volatility', 0.1)
            
            # Agent weights from regime
            regime_weights = market_regime.get('agent_recommendations', {})
            for agent in self.agents:
                features[f'{agent}_regime_weight'] = regime_weights.get(agent, 0.25)
        else:
            # Default regime
            features['regime_id'] = 1
            features['regime_confidence'] = 0.5
            features['volatility_regime'] = 0.1
            for agent in self.agents:
                features[f'{agent}_regime_weight'] = 0.25
        
        # 5. Price-based features (if available)
        if price_data is not None and len(price_data) > 20:
            returns = price_data['close'].pct_change()
            features['recent_volatility'] = returns.tail(20).std()
            features['recent_trend'] = returns.tail(5).mean()
            
            # Distance from moving averages
            ma20 = price_data['close'].rolling(20).mean().iloc[-1]
            ma50 = price_data['close'].rolling(50).mean().iloc[-1]
            current = price_data['close'].iloc[-1]
            
            features['dist_ma20'] = (current - ma20) / ma20 if ma20 != 0 else 0
            features['dist_ma50'] = (current - ma50) / ma50 if ma50 != 0 else 0
        else:
            features['recent_volatility'] = 0.1
            features['recent_trend'] = 0
            features['dist_ma20'] = 0
            features['dist_ma50'] = 0
        
        # 6. Interaction features
        # Technical-Macro interaction
        features['tech_macro_agree'] = (
            1 if np.sign(features.get('technical_signal', 0)) == 
                 np.sign(features.get('macro_signal', 0)) else 0
        )
        
        # Sentiment-Technical momentum alignment
        features['sentiment_tech_align'] = (
            features.get('sentiment_signal', 0) * 
            features.get('technical_signal', 0)
        )
        
        return pd.DataFrame([features])
    
    def train(
        self,
        agent_signals_history: List[Dict],
        market_outcomes: np.ndarray,
        market_regimes: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Train coordinator on historical agent signals and outcomes
        
        Args:
            agent_signals_history: List of agent signal dicts over time
            market_outcomes: Array of realized directions (-1, 0, 1)
            market_regimes: Optional regime classifications
        """
        if not XGB_AVAILABLE:
            return {'error': 'XGBoost not available'}
        
        # Create training dataset
        X_list = []
        for i, signals in enumerate(agent_signals_history):
            regime = market_regimes[i] if market_regimes and i < len(market_regimes) else None
            features = self._create_meta_features(signals, regime)
            X_list.append(features)
        
        X = pd.concat(X_list, ignore_index=True)
        y = market_outcomes + 1  # Map -1,0,1 to 0,1,2
        
        # Split
        split_idx = int(0.8 * len(X))
        X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        if len(X_train) < 50:
            return {'error': 'Insufficient training data'}
        
        # Train
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False
        )
        
        # Build SHAP explainer
        if SHAP_AVAILABLE:
            try:
                self.shap_explainer = shap.TreeExplainer(self.model)
            except:
                pass
        
        # Save
        self._save_model()
        
        # Return metrics
        train_acc = (self.model.predict(X_train) == y_train).mean()
        val_acc = (self.model.predict(X_val) == y_val).mean()
        
        # Feature importance
        importance = dict(zip(X.columns, self.model.feature_importances_))
        
        return {
            'train_accuracy': float(train_acc),
            'val_accuracy': float(val_acc),
            'best_iteration': getattr(self.model, 'best_iteration', self.n_estimators),
            'feature_importance': importance,
            'n_features': len(X.columns)
        }
    
    def fuse_signals(
        self,
        agent_signals: Dict[str, Dict],
        symbol: str,
        market_regime: Optional[Dict] = None,
        price_data: Optional[pd.DataFrame] = None
    ) -> CoordinatorOutput:
        """
        Fuse agent signals using XGBoost meta-learner
        
        This replaces simple weighted voting with learned interactions
        """
        timestamp = datetime.now()
        
        try:
            # Create meta-features
            features_df = self._create_meta_features(agent_signals, market_regime, price_data)
            
            # Check if model is available and fitted
            model_ready = False
            if XGB_AVAILABLE and self.model is not None:
                try:
                    from sklearn.utils.validation import check_is_fitted
                    check_is_fitted(self.model, 'classes_')
                    model_ready = True
                except:
                    model_ready = False
            
            if not model_ready:
                logger.warning("XGBoost coordinator not fitted, using fallback fusion")
                return self._fallback_fusion(agent_signals, symbol)
            
            # Predict
            probabilities = self.model.predict_proba(features_df)[0]
            prob_down, prob_neutral, prob_up = probabilities
            
            # Determine direction
            if prob_up > prob_down and prob_up > 0.45:
                direction = 'BUY'
                confidence = prob_up
            elif prob_down > prob_up and prob_down > 0.45:
                direction = 'SELL'
                confidence = prob_down
            else:
                direction = 'NEUTRAL'
                confidence = prob_neutral
            
            # Adjust for agent disagreement
            disagreement = features_df['agent_disagreement'].iloc[0]
            adjusted_confidence = confidence * (1 - disagreement * 0.5)
            
            # Risk adjustment based on disagreement
            risk_adjusted_conf = adjusted_confidence * 0.9  # Conservative adjustment
            
            # Agent contributions (feature importance weighted)
            importance = self.model.feature_importances_
            contributions = {}
            for agent in self.agents:
                agent_features = [i for i, col in enumerate(features_df.columns) 
                                 if col.startswith(agent)]
                contributions[agent] = sum(importance[i] for i in agent_features)
            
            # Normalize contributions
            total = sum(contributions.values()) or 1
            contributions = {k: v/total for k, v in contributions.items()}
            
            # SHAP explanation
            shap_values = None
            if self.shap_explainer is not None:
                try:
                    sv = self.shap_explainer.shap_values(features_df)
                    pred_class = np.argmax(probabilities)
                    shap_values = dict(zip(features_df.columns, sv[pred_class][0]))
                except:
                    pass
            
            # Generate explanation
            top_features = sorted(
                dict(zip(features_df.columns, importance)).items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            explanation = f"XGBoost fusion {direction}: " + ", ".join([f[0] for f in top_features])
            
            return CoordinatorOutput(
                timestamp=timestamp,
                symbol=symbol,
                direction=direction,
                confidence=float(confidence),
                expected_return=float(confidence * 0.01 * (1 if direction == 'BUY' else -1)),
                probability_up=float(prob_up),
                probability_down=float(prob_down),
                agent_contributions=contributions,
                agent_disagreement=float(disagreement),
                regime_adjusted=market_regime is not None,
                risk_adjusted_confidence=float(risk_adjusted_conf),
                explanation=explanation,
                feature_importance=dict(zip(features_df.columns, importance)),
                shap_explanation=shap_values
            )
            
        except Exception as e:
            logger.error(f"XGBoost fusion error: {e}")
            return self._fallback_fusion(agent_signals, symbol)
    
    def _fallback_fusion(
        self,
        agent_signals: Dict[str, Dict],
        symbol: str
    ) -> CoordinatorOutput:
        """Fallback weighted voting"""
        total_strength = 0
        contributions = {}
        
        for agent in self.agents:
            signal = agent_signals.get(agent, {})
            direction = signal.get('signal', 0)
            if isinstance(direction, str):
                direction = {'BUY': 1, 'SELL': -1, 'NEUTRAL': 0}.get(direction, 0)
            
            confidence = signal.get('confidence', 0.5)
            strength = direction * confidence
            contributions[agent] = abs(strength)
            total_strength += strength
        
        # Determine direction
        if total_strength > 0.2:
            direction = 'BUY'
        elif total_strength < -0.2:
            direction = 'SELL'
        else:
            direction = 'NEUTRAL'
        
        confidence = min(abs(total_strength) / len(self.agents) * 2, 1.0)
        
        # Normalize contributions
        total = sum(contributions.values()) or 1
        contributions = {k: v/total for k, v in contributions.items()}
        
        return CoordinatorOutput(
            timestamp=datetime.now(),
            symbol=symbol,
            direction=direction,
            confidence=confidence,
            expected_return=confidence * 0.01 * (1 if direction == 'BUY' else -1),
            probability_up=0.33,
            probability_down=0.33,
            agent_contributions=contributions,
            agent_disagreement=0.5,
            regime_adjusted=False,
            risk_adjusted_confidence=confidence * 0.9,
            explanation=f"Fallback weighted voting: {direction}",
            feature_importance={},
            shap_explanation=None
        )
    
    def update_performance(self, agent: str, was_correct: bool):
        """Update rolling performance tracking for agent"""
        if agent in self.agent_performance_history:
            self.agent_performance_history[agent].append(1 if was_correct else 0)
            # Keep last 50
            self.agent_performance_history[agent] = self.agent_performance_history[agent][-50:]
    
    def _save_model(self):
        """Save model"""
        if XGB_AVAILABLE and self.model is not None:
            model_path = os.path.join(self.model_dir, 'coordinator_model.json')
            self.model.save_model(model_path)
            logger.info(f"Coordinator model saved to {self.model_dir}")
    
    def _load_existing_model(self):
        """Load existing model from joblib or JSON"""
        if not XGB_AVAILABLE:
            return
        
        # Try joblib format first
        joblib_path = os.path.join(self.model_dir, 'xgb_coordinator_model.joblib')
        json_path = os.path.join(self.model_dir, 'coordinator_model.json')
        
        if os.path.exists(joblib_path):
            try:
                import joblib
                loaded_model = joblib.load(joblib_path)
                # Verify model is fitted using hasattr
                if hasattr(loaded_model, 'feature_importances_'):
                    self.model = loaded_model
                    logger.info("Loaded coordinator model from joblib")
                else:
                    logger.warning("Loaded coordinator model is not fitted")
            except Exception as e:
                logger.warning(f"Failed to load joblib model: {e}")
        
        # Fallback to JSON format
        elif os.path.exists(json_path):
            try:
                self.model.load_model(json_path)
                logger.info("Loaded coordinator model from JSON")
            except Exception as e:
                logger.warning(f"Failed to load JSON model: {e}")


def create_xgboost_coordinator(
    agents: List[str] = None,
    model_path: Optional[str] = None
) -> XGBoostCoordinator:
    """Factory function for XGBoost coordinator"""
    return XGBoostCoordinator(agents=agents, model_path=model_path)
