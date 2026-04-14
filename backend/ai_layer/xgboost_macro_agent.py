"""
XGBoost-Based Macro Agent
Gradient boosting agent for economic data prediction
Replaces rule-based logic with ML-based macro analysis
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import os
import joblib

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
    logging.warning("XGBoost not available - install with: pip install xgboost")

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class MacroSignal:
    """Signal output from XGBoost macro agent"""
    timestamp: datetime
    symbol: str
    direction: str
    confidence: float
    expected_return: float
    probability: float
    feature_importance: Dict[str, float]
    shap_values: Optional[Dict[str, float]]
    macro_factors: Dict[str, float]
    explanation: str
    data_quality_score: float


class XGBoostMacroAgent:
    """
    XGBoost-based macroeconomic analysis agent
    
    Predicts FX moves based on:
    - Interest rate differentials (real and nominal)
    - Inflation differentials
    - Economic surprise indices
    - Yield curve dynamics
    - PMI/CPI/PPI momentum
    
    Uses gradient boosting for non-linear macro relationships
    """
    
    def __init__(
        self,
        n_estimators: int = 200,
        max_depth: int = 6,
        learning_rate: float = 0.05,
        model_path: Optional[str] = None
    ):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.model = None
        self.scaler = None
        self.feature_names = []
        self.shap_explainer = None
        
        # Model persistence
        self.model_dir = model_path or os.path.join(
            os.path.dirname(__file__), 'models', 'xgboost_macro'
        )
        os.makedirs(self.model_dir, exist_ok=True)
        
        if XGB_AVAILABLE:
            self._build_model()
            self._load_existing_model()
    
    def _build_model(self):
        """Build XGBoost classifier"""
        if not XGB_AVAILABLE:
            return
        
        self.model = xgb.XGBClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            subsample=0.8,
            colsample_bytree=0.8,
            objective='multi:softprob',
            num_class=3,  # DOWN, NEUTRAL, UP
            eval_metric='mlogloss',
            random_state=42,
            n_jobs=-1
        )
        
        logger.info(f"XGBoost model built: {self.n_estimators} trees, depth {self.max_depth}")
    
    def _engineer_features(
        self,
        rates_data: pd.DataFrame,
        inflation_data: pd.DataFrame,
        economic_data: pd.DataFrame,
        base_currency: str,
        quote_currency: str
    ) -> pd.DataFrame:
        """
        Engineer macro features from economic data
        
        Features:
        - Rate differentials (nominal and real)
        - Rate momentum (change over time)
        - Inflation differential
        - Economic surprise indices
        - Yield curve slope
        - PMI momentum
        """
        features = {}
        
        # Interest rate features
        base_rate = rates_data.get(f'{base_currency}_rate', pd.Series([0]))
        quote_rate = rates_data.get(f'{quote_currency}_rate', pd.Series([0]))
        
        # Current differential
        features['rate_diff'] = base_rate.iloc[-1] - quote_rate.iloc[-1]
        
        # Rate momentum (changes)
        for window in [1, 3, 6]:
            if len(base_rate) >= window + 1:
                features[f'rate_diff_chg_{window}m'] = (
                    base_rate.iloc[-1] - base_rate.iloc[-(window+1)] -
                    (quote_rate.iloc[-1] - quote_rate.iloc[-(window+1)])
                )
            else:
                features[f'rate_diff_chg_{window}m'] = 0
        
        # Real rate differential (using inflation)
        base_inflation = inflation_data.get(f'{base_currency}_inflation', pd.Series([2.0]))
        quote_inflation = inflation_data.get(f'{quote_currency}_inflation', pd.Series([2.0]))
        
        features['real_rate_diff'] = (
            base_rate.iloc[-1] - base_inflation.iloc[-1] -
            (quote_rate.iloc[-1] - quote_inflation.iloc[-1])
        )
        
        # Inflation differential
        features['inflation_diff'] = base_inflation.iloc[-1] - quote_inflation.iloc[-1]
        
        # Inflation momentum
        if len(base_inflation) >= 3:
            features['inflation_diff_chg'] = (
                (base_inflation.iloc[-1] - base_inflation.iloc[-3]) -
                (quote_inflation.iloc[-1] - quote_inflation.iloc[-3])
            )
        else:
            features['inflation_diff_chg'] = 0
        
        # Economic surprise indices (if available)
        for metric in ['gdp', 'pmi', 'employment', 'cpi']:
            surprise = economic_data.get(f'{metric}_surprise', pd.Series([0]))
            features[f'{metric}_surprise'] = surprise.iloc[-1]
            
            # Surprise momentum
            if len(surprise) >= 3:
                features[f'{metric}_surprise_chg'] = surprise.iloc[-1] - surprise.iloc[-3]
            else:
                features[f'{metric}_surprise_chg'] = 0
        
        # Yield curve slope (if available)
        base_10y = rates_data.get(f'{base_currency}_10y', base_rate)
        base_2y = rates_data.get(f'{base_currency}_2y', base_rate)
        quote_10y = rates_data.get(f'{quote_currency}_10y', quote_rate)
        quote_2y = rates_data.get(f'{quote_currency}_2y', quote_rate)
        
        features['base_yield_curve'] = base_10y.iloc[-1] - base_2y.iloc[-1]
        features['quote_yield_curve'] = quote_10y.iloc[-1] - quote_2y.iloc[-1]
        features['yield_curve_diff'] = features['base_yield_curve'] - features['quote_yield_curve']
        
        # Carry trade attractiveness
        features['carry_attractiveness'] = features['rate_diff'] / 10  # Normalized
        
        # Create DataFrame
        df = pd.DataFrame([features])
        self.feature_names = list(features.keys())
        
        return df
    
    def train(
        self,
        features_df: pd.DataFrame,
        targets: np.ndarray,
        validation_split: float = 0.2
    ) -> Dict:
        """
        Train XGBoost on historical macro data
        
        Args:
            features_df: DataFrame of engineered features
            targets: Array of directional outcomes (-1, 0, 1)
        """
        if not XGB_AVAILABLE or self.model is None:
            return {'error': 'XGBoost not available'}
        
        # Convert targets to 0, 1, 2 for XGBoost
        targets_mapped = targets + 1  # -1->0, 0->1, 1->2
        
        # Split data
        n_samples = len(features_df)
        split_idx = int(n_samples * (1 - validation_split))
        
        X_train = features_df.iloc[:split_idx]
        X_val = features_df.iloc[split_idx:]
        y_train = targets_mapped[:split_idx]
        y_val = targets_mapped[split_idx:]
        
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
                logger.warning("SHAP explainer failed to build")
        
        # Save
        self._save_model()
        
        # Feature importance
        importance = self.model.feature_importances_
        feature_imp = dict(zip(self.feature_names, importance))
        
        return {
            'best_iteration': self.model.best_iteration if hasattr(self.model, 'best_iteration') else self.n_estimators,
            'train_accuracy': float(self.model.score(X_train, y_train)),
            'val_accuracy': float(self.model.score(X_val, y_val)),
            'feature_importance': feature_imp
        }
    
    def predict(
        self,
        rates_data: pd.DataFrame,
        inflation_data: pd.DataFrame,
        economic_data: pd.DataFrame,
        symbol: str
    ) -> MacroSignal:
        """
        Generate macro-based trading signal
        
        Returns calibrated signal with SHAP explanations
        """
        timestamp = datetime.now()
        
        # Extract currencies
        base = symbol[:3]
        quote = symbol[3:6]
        
        try:
            # Engineer features
            features_df = self._engineer_features(
                rates_data, inflation_data, economic_data,
                base, quote
            )
            
            # Check data quality
            missing_ratio = features_df.isnull().sum().sum() / (len(features_df) * len(features_df.columns))
            data_quality = 1.0 - missing_ratio
            
            # Fill missing values
            features_df = features_df.fillna(0)
            
            # Check if model is available and fitted
            model_ready = False
            if XGB_AVAILABLE and self.model is not None:
                try:
                    # Check if model has been fitted (sklearn_is_fitted is the standard way)
                    from sklearn.utils.validation import check_is_fitted
                    check_is_fitted(self.model, 'classes_')
                    model_ready = True
                except:
                    model_ready = False
            
            if not model_ready:
                logger.warning("XGBoost model not fitted, using fallback")
                return self._fallback_signal(base, quote, features_df, data_quality)
            
            # Predict
            probabilities = self.model.predict_proba(features_df)[0]
            prob_down, prob_neutral, prob_up = probabilities
            
            # Determine direction
            if prob_up > prob_down and prob_up > 0.4:
                direction = 'BUY'
                confidence = prob_up
            elif prob_down > prob_up and prob_down > 0.4:
                direction = 'SELL'
                confidence = prob_down
            else:
                direction = 'NEUTRAL'
                confidence = prob_neutral
            
            # Feature importance
            importance = dict(zip(self.feature_names, self.model.feature_importances_))
            
            # SHAP values for explanation
            shap_values = None
            if self.shap_explainer is not None:
                try:
                    sv = self.shap_explainer.shap_values(features_df)
                    # For multi-class, use the predicted class
                    pred_class = np.argmax(probabilities)
                    shap_values = dict(zip(self.feature_names, sv[pred_class][0]))
                except:
                    pass
            
            # Macro factors summary
            macro_factors = {
                'rate_differential': float(features_df['rate_diff'].iloc[0]),
                'real_rate_differential': float(features_df['real_rate_diff'].iloc[0]),
                'inflation_differential': float(features_df['inflation_diff'].iloc[0]),
                'yield_curve_diff': float(features_df['yield_curve_diff'].iloc[0])
            }
            
            # Generate explanation
            top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:3]
            explanation = f"XGBoost {direction}: driven by " + ", ".join([f[0] for f in top_features])
            
            return MacroSignal(
                timestamp=timestamp,
                symbol=symbol,
                direction=direction,
                confidence=float(confidence),
                expected_return=float(confidence * 0.01),  # Rough estimate
                probability=float(max(prob_up, prob_down, prob_neutral)),
                feature_importance=importance,
                shap_values=shap_values,
                macro_factors=macro_factors,
                explanation=explanation,
                data_quality_score=float(data_quality)
            )
            
        except Exception as e:
            logger.error(f"XGBoost prediction error: {e}")
            return self._fallback_signal(base, quote, pd.DataFrame(), 0.5)
    
    def _fallback_signal(
        self,
        base: str,
        quote: str,
        features_df: pd.DataFrame,
        data_quality: float
    ) -> MacroSignal:
        """Fallback rule-based signal"""
        # Simple rate differential rule
        if 'rate_diff' in features_df.columns:
            rate_diff = features_df['rate_diff'].iloc[0]
        else:
            rate_diff = 0
        
        if rate_diff > 0.5:
            direction, confidence = 'BUY', 0.6
        elif rate_diff < -0.5:
            direction, confidence = 'SELL', 0.6
        else:
            direction, confidence = 'NEUTRAL', 0.5
        
        return MacroSignal(
            timestamp=datetime.now(),
            symbol=f"{base}{quote}",
            direction=direction,
            confidence=confidence,
            expected_return=rate_diff * 0.001,
            probability=confidence,
            feature_importance={'rate_diff': 1.0},
            shap_values=None,
            macro_factors={'rate_differential': rate_diff},
            explanation=f"Fallback: {direction} based on {base}-{quote} rate differential",
            data_quality_score=data_quality
        )
    
    def _save_model(self):
        """Save model and scaler"""
        if XGB_AVAILABLE and self.model is not None:
            model_path = os.path.join(self.model_dir, 'xgboost_model.json')
            self.model.save_model(model_path)
            
            # Save feature names
            feature_path = os.path.join(self.model_dir, 'feature_names.joblib')
            joblib.dump(self.feature_names, feature_path)
            
            logger.info(f"XGBoost model saved to {self.model_dir}")
    
    def _load_existing_model(self):
        """Load existing model from joblib"""
        if not XGB_AVAILABLE:
            return
        
        # Try joblib format first
        joblib_path = os.path.join(self.model_dir, 'xgb_macro_model.joblib')
        json_path = os.path.join(self.model_dir, 'xgboost_model.json')
        feature_path = os.path.join(self.model_dir, 'feature_names.joblib')
        
        if os.path.exists(joblib_path):
            try:
                import joblib
                loaded_model = joblib.load(joblib_path)
                # Verify model is fitted
                if hasattr(loaded_model, 'feature_importances_'):
                    self.model = loaded_model
                    logger.info("Loaded XGBoost model from joblib")
                else:
                    logger.warning("Loaded model is not fitted")
            except Exception as e:
                logger.warning(f"Failed to load joblib model: {e}")
        
        # Fallback to JSON format
        elif os.path.exists(json_path):
            try:
                self.model.load_model(json_path)
                logger.info("Loaded XGBoost model from JSON")
            except Exception as e:
                logger.warning(f"Failed to load JSON model: {e}")
        
        if os.path.exists(feature_path):
            try:
                self.feature_names = joblib.load(feature_path)
            except:
                pass


def create_xgboost_macro_agent(model_path: Optional[str] = None) -> XGBoostMacroAgent:
    """Factory function for XGBoost macro agent"""
    return XGBoostMacroAgent(model_path=model_path)
