"""
ML Models Module for Forex Alpha Prediction
TDSP Phase 4 - Modeling
Implements various ML models and ensemble techniques
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import joblib
import warnings
warnings.filterwarnings('ignore')

# ML Libraries
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.ensemble import (RandomForestClassifier, RandomForestRegressor,
                              GradientBoostingClassifier, GradientBoostingRegressor,
                              VotingClassifier, VotingRegressor)
from sklearn.linear_model import LogisticRegression, Ridge, Lasso
from sklearn.svm import SVC, SVR
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             roc_auc_score, mean_squared_error, mean_absolute_error, r2_score)

# Advanced ML
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("Warning: XGBoost not available")

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    print("Warning: LightGBM not available")

try:
    from catboost import CatBoostClassifier, CatBoostRegressor
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False
    print("Warning: CatBoost not available")


class ForexMLModel:
    """
    Base class for Forex ML models
    """
    
    def __init__(self, model_type: str = 'classification', name: str = None):
        """
        Initialize ML model
        
        Args:
            model_type: 'classification' or 'regression'
            name: Model name
        """
        self.model_type = model_type
        self.name = name or f"{model_type}_model"
        self.model = None
        self.scaler = RobustScaler()
        self.is_fitted = False
        self.feature_names = []
        self.training_history = []
        
    def fit(self, X_train, y_train, X_val=None, y_val=None):
        """Fit the model"""
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        self.feature_names = list(X_train.columns) if hasattr(X_train, 'columns') else []
        
        # Train model
        if X_val is not None and y_val is not None:
            X_val_scaled = self.scaler.transform(X_val)
            
            # Determine model type and pass appropriate parameters
            model_class_name = self.model.__class__.__name__
            
            if 'XGB' in model_class_name:
                # XGBoost supports eval_set with verbose
                self.model.fit(X_train_scaled, y_train, 
                              eval_set=[(X_val_scaled, y_val)],
                              verbose=False)
            elif 'LGB' in model_class_name or 'CatBoost' in model_class_name:
                # LightGBM and CatBoost use eval_set but different verbose handling
                self.model.fit(X_train_scaled, y_train, 
                              eval_set=[(X_val_scaled, y_val)])
            else:
                # For other models (RandomForest, Neural Network, etc.)
                self.model.fit(X_train_scaled, y_train)
        else:
            self.model.fit(X_train_scaled, y_train)
        
        self.is_fitted = True
        
        # Calculate training metrics
        train_pred = self.predict(X_train)
        train_metrics = self.evaluate(y_train, train_pred)
        
        if X_val is not None:
            val_pred = self.predict(X_val)
            val_metrics = self.evaluate(y_val, val_pred)
        else:
            val_metrics = {}
        
        self.training_history.append({
            'timestamp': datetime.now(),
            'train_metrics': train_metrics,
            'val_metrics': val_metrics
        })
        
        return self
    
    def predict(self, X):
        """Make predictions"""
        if not self.is_fitted:
            raise ValueError("Model not fitted yet")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X):
        """Predict probabilities (classification only)"""
        if not self.is_fitted:
            raise ValueError("Model not fitted yet")
        if self.model_type != 'classification':
            raise ValueError("predict_proba only available for classification")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)
    
    def evaluate(self, y_true, y_pred) -> Dict:
        """Evaluate model performance"""
        if self.model_type == 'classification':
            return {
                'accuracy': accuracy_score(y_true, y_pred),
                'precision': precision_score(y_true, y_pred, average='weighted', zero_division=0),
                'recall': recall_score(y_true, y_pred, average='weighted', zero_division=0),
                'f1': f1_score(y_true, y_pred, average='weighted', zero_division=0)
            }
        else:  # regression
            return {
                'mse': mean_squared_error(y_true, y_pred),
                'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
                'mae': mean_absolute_error(y_true, y_pred),
                'r2': r2_score(y_true, y_pred)
            }
    
    def save(self, filepath: str):
        """Save model to disk"""
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'model_type': self.model_type,
            'name': self.name,
            'training_history': self.training_history
        }, filepath)
        print(f"Model saved to {filepath}")
    
    def load(self, filepath: str):
        """Load model from disk"""
        data = joblib.load(filepath)
        self.model = data['model']
        self.scaler = data['scaler']
        self.feature_names = data['feature_names']
        self.model_type = data['model_type']
        self.name = data['name']
        self.training_history = data.get('training_history', [])
        self.is_fitted = True
        print(f"Model loaded from {filepath}")
        return self


class RandomForestModel(ForexMLModel):
    """Random Forest model for Forex prediction"""
    
    def __init__(self, model_type='classification', **kwargs):
        super().__init__(model_type, name='RandomForest')
        
        if model_type == 'classification':
            self.model = RandomForestClassifier(
                n_estimators=kwargs.get('n_estimators', 200),
                max_depth=kwargs.get('max_depth', 15),
                min_samples_split=kwargs.get('min_samples_split', 10),
                min_samples_leaf=kwargs.get('min_samples_leaf', 5),
                random_state=42,
                n_jobs=-1
            )
        else:
            self.model = RandomForestRegressor(
                n_estimators=kwargs.get('n_estimators', 200),
                max_depth=kwargs.get('max_depth', 15),
                min_samples_split=kwargs.get('min_samples_split', 10),
                min_samples_leaf=kwargs.get('min_samples_leaf', 5),
                random_state=42,
                n_jobs=-1
            )


class XGBoostModel(ForexMLModel):
    """XGBoost model for Forex prediction"""
    
    def __init__(self, model_type='classification', **kwargs):
        super().__init__(model_type, name='XGBoost')
        
        if not XGBOOST_AVAILABLE:
            raise ImportError("XGBoost not available")
        
        if model_type == 'classification':
            self.model = xgb.XGBClassifier(
                n_estimators=kwargs.get('n_estimators', 200),
                max_depth=kwargs.get('max_depth', 6),
                learning_rate=kwargs.get('learning_rate', 0.1),
                subsample=kwargs.get('subsample', 0.8),
                colsample_bytree=kwargs.get('colsample_bytree', 0.8),
                random_state=42,
                n_jobs=-1,
                eval_metric='logloss'
            )
        else:
            self.model = xgb.XGBRegressor(
                n_estimators=kwargs.get('n_estimators', 200),
                max_depth=kwargs.get('max_depth', 6),
                learning_rate=kwargs.get('learning_rate', 0.1),
                subsample=kwargs.get('subsample', 0.8),
                colsample_bytree=kwargs.get('colsample_bytree', 0.8),
                random_state=42,
                n_jobs=-1,
                eval_metric='rmse'
            )


class LightGBMModel(ForexMLModel):
    """LightGBM model for Forex prediction"""
    
    def __init__(self, model_type='classification', **kwargs):
        super().__init__(model_type, name='LightGBM')
        
        if not LIGHTGBM_AVAILABLE:
            raise ImportError("LightGBM not available")
        
        if model_type == 'classification':
            self.model = lgb.LGBMClassifier(
                n_estimators=kwargs.get('n_estimators', 200),
                max_depth=kwargs.get('max_depth', 6),
                learning_rate=kwargs.get('learning_rate', 0.1),
                num_leaves=kwargs.get('num_leaves', 31),
                random_state=42,
                n_jobs=-1,
                verbose=-1
            )
        else:
            self.model = lgb.LGBMRegressor(
                n_estimators=kwargs.get('n_estimators', 200),
                max_depth=kwargs.get('max_depth', 6),
                learning_rate=kwargs.get('learning_rate', 0.1),
                num_leaves=kwargs.get('num_leaves', 31),
                random_state=42,
                n_jobs=-1,
                verbose=-1
            )


class NeuralNetworkModel(ForexMLModel):
    """Neural Network model for Forex prediction"""
    
    def __init__(self, model_type='classification', **kwargs):
        super().__init__(model_type, name='NeuralNetwork')
        
        hidden_layers = kwargs.get('hidden_layers', (100, 50, 25))
        
        if model_type == 'classification':
            self.model = MLPClassifier(
                hidden_layer_sizes=hidden_layers,
                activation='relu',
                solver='adam',
                alpha=0.0001,
                learning_rate='adaptive',
                max_iter=kwargs.get('max_iter', 500),
                random_state=42,
                early_stopping=True,
                validation_fraction=0.1
            )
        else:
            self.model = MLPRegressor(
                hidden_layer_sizes=hidden_layers,
                activation='relu',
                solver='adam',
                alpha=0.0001,
                learning_rate='adaptive',
                max_iter=kwargs.get('max_iter', 500),
                random_state=42,
                early_stopping=True,
                validation_fraction=0.1
            )


class MLEnsemble:
    """
    Ensemble of multiple ML models for robust predictions
    """
    
    def __init__(self, model_type: str = 'classification'):
        """
        Initialize ML Ensemble
        
        Args:
            model_type: 'classification' or 'regression'
        """
        self.model_type = model_type
        self.models = {}
        self.ensemble_weights = {}
        self.is_fitted = False
        
    def add_model(self, model: ForexMLModel, weight: float = 1.0):
        """Add a model to the ensemble"""
        self.models[model.name] = {
            'model': model,
            'weight': weight
        }
        self.ensemble_weights[model.name] = weight
        
    def fit(self, X_train, y_train, X_val=None, y_val=None):
        """Fit all models in the ensemble"""
        print(f"Training {len(self.models)} models in ensemble...")
        
        for name, model_dict in self.models.items():
            print(f"\nTraining {name}...")
            model = model_dict['model']
            model.fit(X_train, y_train, X_val, y_val)
            
            # Evaluate on validation set
            if X_val is not None:
                val_pred = model.predict(X_val)
                metrics = model.evaluate(y_val, val_pred)
                print(f"{name} validation metrics: {metrics}")
        
        self.is_fitted = True
        return self
    
    def predict(self, X, method='weighted_average'):
        """
        Make ensemble predictions
        
        Args:
            X: Features
            method: 'weighted_average', 'voting', or 'stacking'
            
        Returns:
            Ensemble predictions
        """
        if not self.is_fitted:
            raise ValueError("Ensemble not fitted yet")
        
        predictions = {}
        for name, model_dict in self.models.items():
            model = model_dict['model']
            predictions[name] = model.predict(X)
        
        if method == 'weighted_average':
            return self._weighted_average_prediction(predictions)
        elif method == 'voting':
            return self._voting_prediction(predictions)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _weighted_average_prediction(self, predictions: Dict) -> np.ndarray:
        """Weighted average of predictions"""
        total_weight = sum(self.ensemble_weights.values())
        
        if self.model_type == 'classification':
            # Majority voting with weights
            weighted_preds = []
            for name, pred in predictions.items():
                weight = self.ensemble_weights[name]
                weighted_preds.append(pred * weight)
            
            # Average and round
            return np.round(np.mean(weighted_preds, axis=0)).astype(int)
        else:
            # Weighted average for regression
            weighted_sum = np.zeros_like(next(iter(predictions.values())))
            for name, pred in predictions.items():
                weight = self.ensemble_weights[name]
                weighted_sum += pred * weight
            
            return weighted_sum / total_weight
    
    def _voting_prediction(self, predictions: Dict) -> np.ndarray:
        """Majority voting (classification) or median (regression)"""
        pred_array = np.array(list(predictions.values()))
        
        if self.model_type == 'classification':
            # Majority voting
            from scipy import stats
            return stats.mode(pred_array, axis=0)[0].flatten()
        else:
            # Median
            return np.median(pred_array, axis=0)
    
    def evaluate(self, X_test, y_test) -> Dict:
        """Evaluate ensemble performance"""
        predictions = self.predict(X_test)
        
        if self.model_type == 'classification':
            return {
                'accuracy': accuracy_score(y_test, predictions),
                'precision': precision_score(y_test, predictions, average='weighted', zero_division=0),
                'recall': recall_score(y_test, predictions, average='weighted', zero_division=0),
                'f1': f1_score(y_test, predictions, average='weighted', zero_division=0)
            }
        else:
            return {
                'mse': mean_squared_error(y_test, predictions),
                'rmse': np.sqrt(mean_squared_error(y_test, predictions)),
                'mae': mean_absolute_error(y_test, predictions),
                'r2': r2_score(y_test, predictions)
            }
    
    def get_model_contributions(self, X) -> pd.DataFrame:
        """Get individual model predictions"""
        contributions = {}
        for name, model_dict in self.models.items():
            model = model_dict['model']
            contributions[name] = model.predict(X)
        
        return pd.DataFrame(contributions)
    
    def save(self, directory: str):
        """Save ensemble to directory"""
        import os
        os.makedirs(directory, exist_ok=True)
        
        for name, model_dict in self.models.items():
            model = model_dict['model']
            filepath = os.path.join(directory, f"{name}.joblib")
            model.save(filepath)
        
        # Save ensemble metadata
        metadata = {
            'model_type': self.model_type,
            'ensemble_weights': self.ensemble_weights,
            'model_names': list(self.models.keys())
        }
        joblib.dump(metadata, os.path.join(directory, 'ensemble_metadata.joblib'))
        print(f"Ensemble saved to {directory}")
    
    def load(self, directory: str):
        """Load ensemble from directory"""
        import os
        
        # Load metadata
        metadata = joblib.load(os.path.join(directory, 'ensemble_metadata.joblib'))
        self.model_type = metadata['model_type']
        self.ensemble_weights = metadata['ensemble_weights']
        
        # Load models
        for name in metadata['model_names']:
            filepath = os.path.join(directory, f"{name}.joblib")
            model = ForexMLModel(self.model_type, name)
            model.load(filepath)
            self.add_model(model, self.ensemble_weights[name])
        
        self.is_fitted = True
        print(f"Ensemble loaded from {directory}")
        return self


class ModelFactory:
    """Factory for creating ML models"""
    
    @staticmethod
    def create_model(model_name: str, model_type: str = 'classification', **kwargs) -> ForexMLModel:
        """
        Create a model by name
        
        Args:
            model_name: 'random_forest', 'xgboost', 'lightgbm', 'neural_network'
            model_type: 'classification' or 'regression'
            **kwargs: Model-specific parameters
            
        Returns:
            ForexMLModel instance
        """
        if model_name == 'random_forest':
            return RandomForestModel(model_type, **kwargs)
        elif model_name == 'xgboost':
            return XGBoostModel(model_type, **kwargs)
        elif model_name == 'lightgbm':
            return LightGBMModel(model_type, **kwargs)
        elif model_name == 'neural_network':
            return NeuralNetworkModel(model_type, **kwargs)
        else:
            raise ValueError(f"Unknown model: {model_name}")
    
    @staticmethod
    def create_default_ensemble(model_type: str = 'classification') -> MLEnsemble:
        """
        Create a default ensemble with all available models
        
        Args:
            model_type: 'classification' or 'regression'
            
        Returns:
            MLEnsemble with default models
        """
        ensemble = MLEnsemble(model_type)
        
        # Add Random Forest
        rf = RandomForestModel(model_type)
        ensemble.add_model(rf, weight=1.0)
        
        # Add XGBoost if available
        if XGBOOST_AVAILABLE:
            xgb_model = XGBoostModel(model_type)
            ensemble.add_model(xgb_model, weight=1.2)
        
        # Add LightGBM if available
        if LIGHTGBM_AVAILABLE:
            lgb_model = LightGBMModel(model_type)
            ensemble.add_model(lgb_model, weight=1.1)
        
        # Add Neural Network
        nn = NeuralNetworkModel(model_type)
        ensemble.add_model(nn, weight=0.8)
        
        print(f"Created ensemble with {len(ensemble.models)} models")
        return ensemble


if __name__ == "__main__":
    print("ML Models Module - Example Usage")
    
    # Create sample data
    from sklearn.datasets import make_classification, make_regression
    
    # Classification example
    print("\n=== Classification Example ===")
    X, y = make_classification(n_samples=1000, n_features=20, random_state=42)
    X_train, X_test = X[:800], X[800:]
    y_train, y_test = y[:800], y[800:]
    
    X_train_df = pd.DataFrame(X_train, columns=[f'feature_{i}' for i in range(20)])
    X_test_df = pd.DataFrame(X_test, columns=[f'feature_{i}' for i in range(20)])
    
    # Create and train ensemble
    ensemble = ModelFactory.create_default_ensemble('classification')
    ensemble.fit(X_train_df, y_train)
    
    # Evaluate
    metrics = ensemble.evaluate(X_test_df, y_test)
    print(f"\nEnsemble metrics: {metrics}")
