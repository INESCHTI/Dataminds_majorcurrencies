"""
Complete Modeling Pipeline for Forex Alpha Prediction
TDSP Phase 4 - Modeling
Orchestrates feature engineering, model training, and prediction
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import json
import os

from feature_engineering import FeatureEngineer
from ml_models import MLEnsemble, ModelFactory
from agents.ensemble_agent import EnsembleAgent
from agents.technical_agent import TechnicalAgent
from agents.fundamental_agent import FundamentalAgent
from agents.sentiment_agent import SentimentAgent


class ForexModelingPipeline:
    """
    Complete modeling pipeline for Forex Alpha prediction
    Combines rule-based agents with ML models
    """
    
    def __init__(self, symbol: str = 'EURUSD', horizon: int = 5):
        """
        Initialize modeling pipeline
        
        Args:
            symbol: Trading pair symbol
            horizon: Prediction horizon in periods
        """
        self.symbol = symbol
        self.horizon = horizon
        
        # Initialize components
        self.feature_engineer = FeatureEngineer()
        self.agent_ensemble = EnsembleAgent()
        self.ml_ensemble = None
        
        # Data storage
        self.features_df = None
        self.selected_features = []
        self.training_summary = {}
        
        # Model state
        self.is_trained = False
        
    def prepare_data(self, 
                    market_data: pd.DataFrame,
                    economic_data: Dict[str, pd.DataFrame] = None,
                    news_data: pd.DataFrame = None) -> pd.DataFrame:
        """
        Prepare data with feature engineering and agent signals
        
        Args:
            market_data: OHLCV data
            economic_data: Economic indicators
            news_data: News sentiment data
            
        Returns:
            DataFrame with all features and targets
        """
        print(f"\n{'='*60}")
        print(f"PREPARING DATA FOR {self.symbol}")
        print(f"{'='*60}\n")
        
        # Step 1: Get agent signals
        print("Step 1: Generating agent signals...")
        agent_signals = self._generate_agent_signals(market_data, economic_data, news_data)
        
        # Step 2: Create features
        print("\nStep 2: Creating features...")
        self.features_df = self.feature_engineer.create_all_features(
            market_data=market_data,
            economic_data=economic_data,
            news_data=news_data,
            agent_signals=agent_signals,
            create_targets=True
        )
        
        # Step 3: Select important features
        print("\nStep 3: Selecting features...")
        target_col = f'target_up_{self.horizon}'
        self.selected_features = self.feature_engineer.select_features(
            self.features_df, 
            target_col=target_col,
            method='random_forest',
            top_k=50
        )
        
        print(f"\nData preparation complete!")
        print(f"Total samples: {len(self.features_df)}")
        print(f"Total features: {len(self.feature_engineer.feature_names)}")
        print(f"Selected features: {len(self.selected_features)}")
        
        return self.features_df
    
    def _generate_agent_signals(self,
                               market_data: pd.DataFrame,
                               economic_data: Dict = None,
                               news_data: pd.DataFrame = None) -> pd.DataFrame:
        """Generate signals from rule-based agents"""
        
        signals_list = []
        
        # Sample every N rows to speed up (agents are slow on large datasets)
        sample_rate = max(1, len(market_data) // 100)  # Max 100 signals
        sampled_indices = range(0, len(market_data), sample_rate)
        
        for i in sampled_indices:
            index = market_data.index[i]
            
            # Prepare data for agents
            historical_data = market_data.loc[:index].tail(200)
            
            # Skip if not enough data
            if len(historical_data) < 50:
                continue
            
            # Get signals from each agent
            try:
                tech_signal = self.agent_ensemble.technical_agent.analyze(
                    self.symbol,
                    historical_data
                )
                
                signals_list.append({
                    'timestamp': index,
                    'technical_direction': tech_signal.direction,
                    'technical_confidence': tech_signal.confidence,
                    'fundamental_direction': 'HOLD',
                    'fundamental_confidence': 0.0,
                    'sentiment_direction': 'HOLD',
                    'sentiment_confidence': 0.0
                })
            except Exception as e:
                # If analysis fails, use neutral signal
                signals_list.append({
                    'timestamp': index,
                    'technical_direction': 'HOLD',
                    'technical_confidence': 0.0,
                    'fundamental_direction': 'HOLD',
                    'fundamental_confidence': 0.0,
                    'sentiment_direction': 'HOLD',
                    'sentiment_confidence': 0.0
                })
        
        # Create DataFrame and forward-fill for missing timestamps
        signals_df = pd.DataFrame(signals_list).set_index('timestamp')
        
        # Reindex to match market_data and forward-fill
        signals_df = signals_df.reindex(market_data.index, method='ffill').fillna({
            'technical_direction': 'HOLD',
            'technical_confidence': 0.0,
            'fundamental_direction': 'HOLD',
            'fundamental_confidence': 0.0,
            'sentiment_direction': 'HOLD',
            'sentiment_confidence': 0.0
        })
        
        return signals_df
    
    def train_models(self, 
                    train_size: float = 0.7,
                    val_size: float = 0.15,
                    model_type: str = 'classification') -> Dict:
        """
        Train ML ensemble models
        
        Args:
            train_size: Proportion for training
            val_size: Proportion for validation
            model_type: 'classification' or 'regression'
            
        Returns:
            Training summary dictionary
        """
        if self.features_df is None:
            raise ValueError("Data not prepared. Call prepare_data() first.")
        
        print(f"\n{'='*60}")
        print(f"TRAINING MODELS FOR {self.symbol}")
        print(f"{'='*60}\n")
        
        # Prepare ML dataset
        target_col = f'target_up_{self.horizon}'
        X_train, X_val, X_test, y_train, y_val, y_test = \
            self.feature_engineer.prepare_ml_dataset(
                self.features_df,
                target_col=target_col,
                selected_features=self.selected_features,
                train_size=train_size,
                val_size=val_size
            )
        
        # Create ML ensemble
        print("\nCreating ML ensemble...")
        self.ml_ensemble = ModelFactory.create_default_ensemble(model_type)
        
        # Train ensemble
        print("\nTraining ensemble...")
        self.ml_ensemble.fit(X_train, y_train, X_val, y_val)
        
        # Evaluate on all sets
        print("\n" + "="*60)
        print("MODEL EVALUATION")
        print("="*60)
        
        train_metrics = self.ml_ensemble.evaluate(X_train, y_train)
        val_metrics = self.ml_ensemble.evaluate(X_val, y_val)
        test_metrics = self.ml_ensemble.evaluate(X_test, y_test)
        
        print(f"\nTrain metrics: {train_metrics}")
        print(f"Val metrics:   {val_metrics}")
        print(f"Test metrics:  {test_metrics}")
        
        # Store training summary
        self.training_summary = {
            'symbol': self.symbol,
            'horizon': self.horizon,
            'train_size': len(X_train),
            'val_size': len(X_val),
            'test_size': len(X_test),
            'n_features': len(self.selected_features),
            'train_metrics': train_metrics,
            'val_metrics': val_metrics,
            'test_metrics': test_metrics,
            'timestamp': datetime.now().isoformat()
        }
        
        self.is_trained = True
        
        print("\n" + "="*60)
        print("TRAINING COMPLETE!")
        print("="*60)
        
        return self.training_summary
    
    def predict(self, market_data: pd.DataFrame,
               economic_data: Dict = None,
               news_data: pd.DataFrame = None) -> Dict:
        """
        Make predictions on new data
        
        Args:
            market_data: Current and historical market data
            economic_data: Economic indicators
            news_data: News sentiment data
            
        Returns:
            Prediction dictionary with signal and confidence
        """
        if not self.is_trained:
            raise ValueError("Models not trained. Call train_models() first.")
        
        # Prepare features
        agent_signals = self._generate_agent_signals(market_data, economic_data, news_data)
        features = self.feature_engineer.create_all_features(
            market_data=market_data,
            economic_data=economic_data,
            news_data=news_data,
            agent_signals=agent_signals,
            create_targets=False
        )
        
        # Get latest data point
        latest_features = features[self.selected_features].iloc[[-1]].dropna()
        
        if latest_features.empty:
            return {
                'direction': 'HOLD',
                'confidence': 0.0,
                'ml_prediction': None,
                'agent_signal': 'HOLD',
                'timestamp': datetime.now()
            }
        
        # ML prediction
        ml_pred = self.ml_ensemble.predict(latest_features)[0]
        ml_direction = 'BUY' if ml_pred == 1 else 'SELL'
        
        # Agent prediction
        agent_result = self.agent_ensemble.analyze(
            self.symbol,
            forex_data=market_data
        )
        agent_direction = agent_result.get('direction', 'HOLD')
        agent_confidence = agent_result.get('confidence', 0.5)
        
        # Combine predictions
        if ml_direction == agent_direction:
            # Agreement: high confidence
            final_direction = ml_direction
            confidence = min(0.95, agent_confidence + 0.3)
        else:
            # Disagreement: moderate confidence, prefer ML
            final_direction = ml_direction
            confidence = 0.5
        
        return {
            'direction': final_direction,
            'confidence': confidence,
            'ml_prediction': ml_direction,
            'agent_signal': agent_direction,
            'agent_confidence': agent_confidence,
            'timestamp': datetime.now()
        }
    
    def save_pipeline(self, directory: str):
        """Save complete pipeline to directory"""
        os.makedirs(directory, exist_ok=True)
        
        # Save ML ensemble
        ensemble_dir = os.path.join(directory, 'ml_ensemble')
        self.ml_ensemble.save(ensemble_dir)
        
        # Save metadata
        metadata = {
            'symbol': self.symbol,
            'horizon': self.horizon,
            'selected_features': self.selected_features,
            'training_summary': self.training_summary,
            'feature_importance': self.feature_engineer.feature_importance
        }
        
        with open(os.path.join(directory, 'pipeline_metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\nPipeline saved to {directory}")
    
    def load_pipeline(self, directory: str):
        """Load pipeline from directory"""
        # Load metadata
        with open(os.path.join(directory, 'pipeline_metadata.json'), 'r') as f:
            metadata = json.load(f)
        
        self.symbol = metadata['symbol']
        self.horizon = metadata['horizon']
        self.selected_features = metadata['selected_features']
        self.training_summary = metadata['training_summary']
        self.feature_engineer.feature_importance = metadata['feature_importance']
        
        # Load ML ensemble
        ensemble_dir = os.path.join(directory, 'ml_ensemble')
        self.ml_ensemble = MLEnsemble()
        self.ml_ensemble.load(ensemble_dir)
        
        self.is_trained = True
        
        print(f"\nPipeline loaded from {directory}")
        return self


class MultiCurrencyPipeline:
    """
    Manage multiple currency pair pipelines
    """
    
    def __init__(self, symbols: List[str] = None):
        """
        Initialize multi-currency pipeline
        
        Args:
            symbols: List of currency pairs
        """
        self.symbols = symbols or ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']
        self.pipelines = {}
        
        for symbol in self.symbols:
            self.pipelines[symbol] = ForexModelingPipeline(symbol=symbol)
    
    def train_all(self, data_dict: Dict[str, pd.DataFrame]) -> Dict:
        """
        Train pipelines for all currency pairs
        
        Args:
            data_dict: Dictionary mapping symbol to market data
            
        Returns:
            Dictionary of training summaries
        """
        summaries = {}
        
        for symbol in self.symbols:
            if symbol not in data_dict:
                print(f"Warning: No data for {symbol}, skipping...")
                continue
            
            print(f"\n\n{'#'*60}")
            print(f"# PROCESSING {symbol}")
            print(f"{'#'*60}\n")
            
            pipeline = self.pipelines[symbol]
            
            # Prepare and train
            pipeline.prepare_data(data_dict[symbol])
            summary = pipeline.train_models()
            
            summaries[symbol] = summary
        
        return summaries
    
    def predict_all(self, data_dict: Dict[str, pd.DataFrame]) -> Dict:
        """
        Make predictions for all currency pairs
        
        Args:
            data_dict: Dictionary mapping symbol to market data
            
        Returns:
            Dictionary of predictions
        """
        predictions = {}
        
        for symbol in self.symbols:
            if symbol not in data_dict:
                continue
            
            pipeline = self.pipelines[symbol]
            if pipeline.is_trained:
                predictions[symbol] = pipeline.predict(data_dict[symbol])
        
        return predictions
    
    def save_all(self, base_directory: str):
        """Save all pipelines"""
        for symbol, pipeline in self.pipelines.items():
            if pipeline.is_trained:
                symbol_dir = os.path.join(base_directory, symbol)
                pipeline.save_pipeline(symbol_dir)
    
    def load_all(self, base_directory: str):
        """Load all pipelines"""
        for symbol in self.symbols:
            symbol_dir = os.path.join(base_directory, symbol)
            if os.path.exists(symbol_dir):
                self.pipelines[symbol].load_pipeline(symbol_dir)


if __name__ == "__main__":
    print("Modeling Pipeline - Example Usage")
    
    # Create sample data
    dates = pd.date_range(start='2024-01-01', end='2026-02-23', freq='1H')
    sample_data = pd.DataFrame({
        'open': np.random.randn(len(dates)).cumsum() + 100,
        'high': np.random.randn(len(dates)).cumsum() + 101,
        'low': np.random.randn(len(dates)).cumsum() + 99,
        'close': np.random.randn(len(dates)).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, len(dates))
    }, index=dates)
    
    # Initialize pipeline
    pipeline = ForexModelingPipeline(symbol='EURUSD', horizon=5)
    
    # Prepare data
    features = pipeline.prepare_data(sample_data)
    
    # Train models
    summary = pipeline.train_models()
    
    print("\n\nPipeline ready for predictions!")
