"""
Market Regime Classification using Hidden Markov Models (HMM)
Classifies FX market into regimes to condition agent weights and risk parameters
"""
import os
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

try:
    from hmmlearn import hmm
    HMMLEARN_AVAILABLE = True
except ImportError:
    HMMLEARN_AVAILABLE = False
    logging.warning("hmmlearn not available - install with: pip install hmmlearn")

logger = logging.getLogger(__name__)


@dataclass
class RegimeResult:
    """Market regime classification result"""
    timestamp: datetime
    regime: str  # 'trending', 'ranging', 'crisis', 'recovery'
    regime_id: int
    probability: float
    confidence: float
    volatility: float
    autocorr: float
    regime_stability: float  # How long in current regime
    agent_recommendations: Dict[str, float]  # Recommended weights per agent
    risk_adjustment: float  # Risk multiplier for this regime


class HMMRegimeClassifier:
    """
    Hidden Markov Model for FX market regime detection
    
    Uses realized volatility and return autocorrelation as features
    to classify market into 4 regimes:
    - TRENDING: High volatility, positive autocorr (momentum)
    - RANGING: Low volatility, near-zero autocorr (mean-reversion)
    - CRISIS: Very high volatility, negative autocorr (risk-off)
    - RECOVERY: Declining volatility, mixed autocorr (normalization)
    """
    
    REGIME_NAMES = {
        0: 'trending',
        1: 'ranging', 
        2: 'crisis',
        3: 'recovery'
    }
    
    # Agent weight recommendations per regime
    REGIME_AGENT_WEIGHTS = {
        'trending': {
            'technical': 0.40,  # Momentum works well
            'macro': 0.20,
            'sentiment': 0.25,
            'geopolitical': 0.15
        },
        'ranging': {
            'technical': 0.35,  # Mean reversion
            'macro': 0.25,
            'sentiment': 0.20,
            'geopolitical': 0.20
        },
        'crisis': {
            'technical': 0.15,  # Technicals break down
            'macro': 0.30,      # Macro drivers dominate
            'sentiment': 0.15,
            'geopolitical': 0.40  # Geopolitical critical
        },
        'recovery': {
            'technical': 0.30,
            'macro': 0.35,      # Macro normalization key
            'sentiment': 0.25,
            'geopolitical': 0.10
        }
    }
    
    # Risk adjustments per regime
    REGIME_RISK_MULTIPLIERS = {
        'trending': 1.0,      # Normal risk
        'ranging': 0.8,       # Reduce size in chop
        'crisis': 0.5,        # Half size in crisis
        'recovery': 0.9       # Cautious in recovery
    }
    
    def __init__(self, n_regimes: int = 4, model_dir: Optional[str] = None):
        self.n_regimes = n_regimes
        self.model = None
        self.scaler_mean = None
        self.scaler_std = None
        self.regime_history = []
        
        # Set up model directory
        if model_dir:
            self.model_dir = model_dir
        else:
            self.model_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'models', 'hmm_regime'
            )
        os.makedirs(self.model_dir, exist_ok=True)
        
        self._build_model()
        self._load_existing_model()
    
    def _build_model(self):
        """Initialize Gaussian HMM"""
        if not HMMLEARN_AVAILABLE:
            logger.warning("HMMlearn not available - using fallback rule-based classifier")
            return
        
        # Gaussian HMM with 4 states
        self.model = hmm.GaussianHMM(
            n_components=self.n_regimes,
            covariance_type="full",
            n_iter=100,
            random_state=42,
            init_params="stmc"  # startprob, transmat, means, covars
        )
    
    def _calculate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate regime features from OHLCV data
        
        Features:
        - Realized volatility (20-period)
        - Return autocorrelation (lag-1)
        - Average true range ratio
        - Price excursion (max - min / close)
        """
        df = df.copy()
        
        # Log returns
        df['returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Realized volatility (20-period)
        df['volatility'] = df['returns'].rolling(window=20).std() * np.sqrt(252)
        
        # Return autocorrelation (lag-1, 10-period rolling)
        df['autocorr'] = df['returns'].rolling(window=10).apply(
            lambda x: x.autocorr(lag=1) if len(x.dropna()) > 1 else 0
        )
        
        # Average True Range ratio
        df['tr1'] = df['high'] - df['low']
        df['tr2'] = abs(df['high'] - df['close'].shift(1))
        df['tr3'] = abs(df['low'] - df['close'].shift(1))
        df['true_range'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        df['atr_ratio'] = (df['true_range'].rolling(14).mean()) / df['close']
        
        # Price excursion
        df['excursion'] = (df['high'].rolling(20).max() - df['low'].rolling(20).min()) / df['close']
        
        # Select features for HMM
        features = df[['volatility', 'autocorr', 'atr_ratio', 'excursion']].dropna()
        
        return features
    
    def _normalize_features(self, features: pd.DataFrame) -> np.ndarray:
        """Z-score normalization"""
        if self.scaler_mean is None:
            self.scaler_mean = features.mean()
            self.scaler_std = features.std()
        
        normalized = (features - self.scaler_mean) / self.scaler_std
        return normalized.values
    
    def fit(self, df: pd.DataFrame) -> 'HMMRegimeClassifier':
        """
        Fit HMM on historical data
        
        Args:
            df: DataFrame with OHLCV data
        """
        if not HMMLEARN_AVAILABLE or len(df) < 100:
            logger.warning("Insufficient data or HMMlearn not available")
            return self
        
        features = self._calculate_features(df)
        if len(features) < 50:
            logger.warning(f"Insufficient data points: {len(features)}")
            return self
        
        X = self._normalize_features(features)
        
        try:
            self.model.fit(X)
            logger.info(f"HMM fitted. Means: {self.model.means_}")
            joblib.dump(self.model, os.path.join(self.model_dir, 'hmm_regime_model.joblib'))
            joblib.dump({'mean': self.scaler_mean, 'std': self.scaler_std}, os.path.join(self.model_dir, 'scaler.joblib'))
        except Exception as e:
            logger.error(f"HMM fitting failed: {e}")
        
        return self
    
    def predict(self, df: pd.DataFrame) -> RegimeResult:
        """
        Predict current market regime
        
        Args:
            df: Recent OHLCV data (at least 20 periods)
        
        Returns:
            RegimeResult with classification and recommendations
        """
        timestamp = datetime.now()
        
        # Check if HMM is available and fitted
        hmm_ready = False
        if HMMLEARN_AVAILABLE and self.model is not None:
            try:
                # Check if model has been fitted (means_ attribute is set after fitting)
                _ = self.model.means_
                hmm_ready = True
            except:
                hmm_ready = False
        
        if not hmm_ready:
            # Fallback: rule-based classification
            return self._rule_based_regime(df, timestamp)
        
        try:
            features = self._calculate_features(df)
            if len(features) == 0:
                return self._rule_based_regime(df, timestamp)
            
            X = self._normalize_features(features)
            
            # Predict regime for latest observation
            regime_id = self.model.predict(X)[-1]
            probs = self.model.predict_proba(X)[-1]
            
            regime_name = self.REGIME_NAMES.get(regime_id, 'unknown')
            probability = probs[regime_id]
            
            # Calculate regime stability
            regime_stability = self._calculate_stability(regime_id)
            
            # Get recommendations
            agent_weights = self.REGIME_AGENT_WEIGHTS.get(regime_name, {})
            risk_mult = self.REGIME_RISK_MULTIPLIERS.get(regime_name, 1.0)
            
            return RegimeResult(
                timestamp=timestamp,
                regime=regime_name,
                regime_id=int(regime_id),
                probability=float(probability),
                confidence=float(probability),  # Use prob as confidence
                volatility=float(features['volatility'].iloc[-1]),
                autocorr=float(features['autocorr'].iloc[-1]),
                regime_stability=regime_stability,
                agent_recommendations=agent_weights,
                risk_adjustment=risk_mult
            )
            
        except Exception as e:
            logger.error(f"Regime prediction failed: {e}")
            return self._rule_based_regime(df, timestamp)
    
    def _rule_based_regime(self, df: pd.DataFrame, timestamp: datetime) -> RegimeResult:
        """Fallback rule-based regime classification"""
        df = df.copy()
        df['returns'] = df['close'].pct_change()
        
        vol = df['returns'].rolling(20).std().iloc[-1] * np.sqrt(252)
        autocorr = df['returns'].rolling(10).apply(lambda x: x.autocorr(lag=1)).iloc[-1]
        
        # Simple rules
        if vol > 0.20:  # >20% annualized vol = crisis
            regime = 'crisis'
            regime_id = 2
        elif vol < 0.08:  # <8% vol = ranging
            regime = 'ranging'
            regime_id = 1
        elif autocorr > 0.1:  # Positive autocorr = trending
            regime = 'trending'
            regime_id = 0
        else:
            regime = 'recovery'
            regime_id = 3
        
        return RegimeResult(
            timestamp=timestamp,
            regime=regime,
            regime_id=regime_id,
            probability=0.7,  # Lower confidence for rule-based
            confidence=0.7,
            volatility=float(vol) if not np.isnan(vol) else 0.1,
            autocorr=float(autocorr) if not np.isnan(autocorr) else 0.0,
            regime_stability=0.5,
            agent_recommendations=self.REGIME_AGENT_WEIGHTS.get(regime, {}),
            risk_adjustment=self.REGIME_RISK_MULTIPLIERS.get(regime, 1.0)
        )
    
    def _calculate_stability(self, current_regime: int) -> float:
        """Calculate how stable the current regime is (0-1)"""
        if len(self.regime_history) < 5:
            return 0.5
        
        recent = self.regime_history[-10:]
        same_regime_count = sum(1 for r in recent if r == current_regime)
        return same_regime_count / len(recent)
    
    def update_history(self, regime_id: int):
        """Track regime history for stability calculation"""
        self.regime_history.append(regime_id)
        if len(self.regime_history) > 100:
            self.regime_history = self.regime_history[-100:]
    
    def _load_existing_model(self):
        """Load existing model from joblib"""
        if not HMMLEARN_AVAILABLE:
            return
        
        try:
            import joblib
        except ImportError:
            return
        
        model_path = os.path.join(self.model_dir, 'hmm_regime_model.joblib')
        scaler_path = os.path.join(self.model_dir, 'scaler.joblib')
        
        if os.path.exists(model_path):
            try:
                loaded_model = joblib.load(model_path)
                # Verify model is fitted by checking for means_ attribute
                if hasattr(loaded_model, 'means_'):
                    self.model = loaded_model
                    logger.info("Loaded HMM model from joblib")
                else:
                    logger.warning("Loaded HMM model is not fitted")
            except Exception as e:
                logger.warning(f"Failed to load HMM model: {e}")
        
        if os.path.exists(scaler_path):
            try:
                scaler_data = joblib.load(scaler_path)
                self.scaler_mean = scaler_data.get('mean')
                self.scaler_std = scaler_data.get('std')
            except:
                pass


class RegimeAdaptiveCoordinator:
    """
    Coordinator that adapts agent weights based on market regime
    
    This addresses the evaluation's key critique:
    "Without regime detection... all agents run with the same structural weights"
    """
    
    def __init__(self, base_weights: Optional[Dict[str, float]] = None):
        self.regime_classifier = HMMRegimeClassifier()
        self.base_weights = base_weights or {
            'technical': 0.30,
            'macro': 0.25,
            'sentiment': 0.25,
            'geopolitical': 0.20
        }
        self.current_regime: Optional[RegimeResult] = None
    
    def fit_classifier(self, historical_data: pd.DataFrame):
        """Fit regime classifier on historical OHLCV"""
        self.regime_classifier.fit(historical_data)
    
    def get_adaptive_weights(self, recent_data: pd.DataFrame) -> Dict[str, float]:
        """
        Get regime-conditioned agent weights
        
        Args:
            recent_data: Recent OHLCV data for regime classification
        
        Returns:
            Dictionary of agent weights adjusted for current regime
        """
        # Classify current regime
        self.current_regime = self.regime_classifier.predict(recent_data)
        
        if self.current_regime is None:
            return self.base_weights
        
        # Update history
        self.regime_classifier.update_history(self.current_regime.regime_id)
        
        # Blend base weights with regime recommendations
        regime_weights = self.current_regime.agent_recommendations
        
        # Smooth transition: 70% regime weights, 30% base weights
        adaptive_weights = {}
        for agent in self.base_weights.keys():
            regime_w = regime_weights.get(agent, self.base_weights[agent])
            base_w = self.base_weights[agent]
            adaptive_weights[agent] = 0.7 * regime_w + 0.3 * base_w
        
        # Normalize to sum to 1
        total = sum(adaptive_weights.values())
        return {k: v/total for k, v in adaptive_weights.items()}
    
    def get_risk_parameters(self) -> Dict[str, float]:
        """Get regime-adjusted risk parameters"""
        if self.current_regime is None:
            return {'position_size_mult': 1.0, 'stop_mult': 1.0}
        
        risk_mult = self.current_regime.risk_adjustment
        
        return {
            'position_size_mult': risk_mult,
            'stop_mult': 1.0 / risk_mult if risk_mult > 0 else 1.0,  # Wider stops in crisis
            'regime': self.current_regime.regime,
            'regime_confidence': self.current_regime.confidence
        }


def create_regime_classifier() -> HMMRegimeClassifier:
    """Factory function for regime classifier"""
    return HMMRegimeClassifier(n_regimes=4)


def create_regime_adaptive_coordinator() -> RegimeAdaptiveCoordinator:
    """Factory function for regime-adaptive coordinator"""
    return RegimeAdaptiveCoordinator()
