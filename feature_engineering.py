"""
Feature Engineering Module for Forex Alpha Prediction
TDSP Phase 3 - Data Preparation
Generates features for ML models from agent signals and market data
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from scipy import stats
import warnings
warnings.filterwarnings('ignore')


class FeatureEngineer:
    """
    Feature Engineering for Forex Prediction ML Models
    Creates technical, fundamental, sentiment, and ensemble features
    """
    
    def __init__(self):
        self.feature_names = []
        self.feature_importance = {}
        
    def create_technical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create technical analysis features
        
        Args:
            df: DataFrame with OHLCV data (open, high, low, close, volume)
            
        Returns:
            DataFrame with technical features added
        """
        result = df.copy()
        
        # Moving Averages
        for period in [5, 10, 20, 50, 100, 200]:
            result[f'sma_{period}'] = result['close'].rolling(window=period).mean()
            result[f'ema_{period}'] = result['close'].ewm(span=period, adjust=False).mean()
        
        # Price Distance from MAs
        for period in [20, 50, 200]:
            result[f'dist_sma_{period}'] = (result['close'] - result[f'sma_{period}']) / result[f'sma_{period}']
        
        # RSI (Relative Strength Index)
        for period in [6, 14, 21]:
            delta = result['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            result[f'rsi_{period}'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema12 = result['close'].ewm(span=12, adjust=False).mean()
        ema26 = result['close'].ewm(span=26, adjust=False).mean()
        result['macd'] = ema12 - ema26
        result['macd_signal'] = result['macd'].ewm(span=9, adjust=False).mean()
        result['macd_histogram'] = result['macd'] - result['macd_signal']
        
        # Bollinger Bands
        for period in [20, 50]:
            rolling_mean = result['close'].rolling(window=period).mean()
            rolling_std = result['close'].rolling(window=period).std()
            result[f'bb_upper_{period}'] = rolling_mean + (rolling_std * 2)
            result[f'bb_lower_{period}'] = rolling_mean - (rolling_std * 2)
            result[f'bb_width_{period}'] = (result[f'bb_upper_{period}'] - result[f'bb_lower_{period}']) / rolling_mean
            result[f'bb_position_{period}'] = (result['close'] - result[f'bb_lower_{period}']) / (result[f'bb_upper_{period}'] - result[f'bb_lower_{period}'])
        
        # Volatility
        result['returns'] = result['close'].pct_change()
        for period in [5, 10, 20]:
            result[f'volatility_{period}'] = result['returns'].rolling(window=period).std()
            result[f'volatility_{period}_annualized'] = result[f'volatility_{period}'] * np.sqrt(252)
        
        # ATR (Average True Range)
        high_low = result['high'] - result['low']
        high_close = np.abs(result['high'] - result['close'].shift())
        low_close = np.abs(result['low'] - result['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        result['atr_14'] = true_range.rolling(14).mean()
        
        # Momentum
        for period in [5, 10, 20]:
            result[f'momentum_{period}'] = result['close'].diff(period)
            result[f'roc_{period}'] = (result['close'] - result['close'].shift(period)) / result['close'].shift(period) * 100
        
        # Volume features
        if 'volume' in result.columns:
            result['volume_sma_20'] = result['volume'].rolling(window=20).mean()
            result['volume_ratio'] = result['volume'] / result['volume_sma_20']
            result['price_volume'] = result['close'] * result['volume']
        
        # Candle patterns
        result['body'] = result['close'] - result['open']
        result['body_ratio'] = result['body'] / (result['high'] - result['low'])
        result['upper_shadow'] = result['high'] - result[['close', 'open']].max(axis=1)
        result['lower_shadow'] = result[['close', 'open']].min(axis=1) - result['low']
        
        # Trend strength
        result['adx'] = self._calculate_adx(result)
        
        return result
    
    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average Directional Index (ADX)"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        plus_dm = high.diff()
        minus_dm = -low.diff()
        
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        tr1 = pd.DataFrame(high - low)
        tr2 = pd.DataFrame(abs(high - close.shift(1)))
        tr3 = pd.DataFrame(abs(low - close.shift(1)))
        frames = [tr1, tr2, tr3]
        tr = pd.concat(frames, axis=1, join='inner').max(axis=1)
        atr = tr.rolling(period).mean()
        
        plus_di = 100 * (plus_dm.ewm(alpha=1/period).mean() / atr)
        minus_di = 100 * (minus_dm.ewm(alpha=1/period).mean() / atr)
        dx = (abs(plus_di - minus_di) / abs(plus_di + minus_di)) * 100
        adx = dx.ewm(alpha=1/period).mean()
        
        return adx
    
    def create_fundamental_features(self, df: pd.DataFrame, 
                                   economic_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Create fundamental analysis features
        
        Args:
            df: DataFrame with market data
            economic_data: Dictionary of economic indicators DataFrames
                          Keys: 'interest_rates', 'cpi', 'gdp', 'unemployment', etc.
            
        Returns:
            DataFrame with fundamental features added
        """
        result = df.copy()
        
        # Interest rate differentials
        if 'interest_rates' in economic_data:
            rates = economic_data['interest_rates']
            result = result.merge(rates, how='left', left_index=True, right_index=True, suffixes=('', '_rate'))
        
        # Inflation (CPI)
        if 'cpi' in economic_data:
            cpi = economic_data['cpi']
            result = result.merge(cpi, how='left', left_index=True, right_index=True, suffixes=('', '_cpi'))
            # Calculate YoY inflation rate
            result['inflation_yoy'] = result['cpi'].pct_change(12) * 100
        
        # GDP growth
        if 'gdp' in economic_data:
            gdp = economic_data['gdp']
            result = result.merge(gdp, how='left', left_index=True, right_index=True, suffixes=('', '_gdp'))
            result['gdp_growth'] = result['gdp'].pct_change(4) * 100
        
        # Unemployment rate
        if 'unemployment' in economic_data:
            unemployment = economic_data['unemployment']
            result = result.merge(unemployment, how='left', left_index=True, right_index=True, suffixes=('', '_unemployment'))
        
        # Forward-fill economic data (published monthly/quarterly)
        economic_columns = [col for col in result.columns if any(x in col for x in ['rate', 'cpi', 'gdp', 'unemployment', 'inflation'])]
        result[economic_columns] = result[economic_columns].fillna(method='ffill')
        
        return result
    
    def create_sentiment_features(self, df: pd.DataFrame,
                                  news_data: pd.DataFrame) -> pd.DataFrame:
        """
        Create sentiment analysis features
        
        Args:
            df: DataFrame with market data
            news_data: DataFrame with news sentiment scores
            
        Returns:
            DataFrame with sentiment features added
        """
        result = df.copy()
        
        if news_data.empty:
            result['sentiment_score'] = 0.0
            result['sentiment_volume'] = 0
            return result
        
        # Aggregate news sentiment by date
        news_daily = news_data.groupby(news_data.index.date).agg({
            'sentiment_score': ['mean', 'std', 'min', 'max'],
            'headline': 'count'
        })
        news_daily.columns = ['sentiment_mean', 'sentiment_std', 'sentiment_min', 'sentiment_max', 'news_count']
        news_daily.index = pd.to_datetime(news_daily.index)
        
        # Merge with market data
        result = result.merge(news_daily, how='left', left_index=True, right_index=True)
        
        # Fill missing sentiment data
        result[['sentiment_mean', 'sentiment_std', 'sentiment_min', 'sentiment_max']] = \
            result[['sentiment_mean', 'sentiment_std', 'sentiment_min', 'sentiment_max']].fillna(0)
        result['news_count'] = result['news_count'].fillna(0)
        
        # Rolling sentiment features
        for period in [3, 7, 14]:
            result[f'sentiment_{period}d'] = result['sentiment_mean'].rolling(window=period).mean()
            result[f'sentiment_trend_{period}d'] = result['sentiment_mean'].diff(period)
        
        return result
    
    def create_agent_signal_features(self, df: pd.DataFrame,
                                    agent_signals: pd.DataFrame) -> pd.DataFrame:
        """
        Create features from agent signals
        
        Args:
            df: DataFrame with market data
            agent_signals: DataFrame with agent signals (direction, confidence)
            
        Returns:
            DataFrame with agent signal features added
        """
        result = df.copy()
        
        if agent_signals.empty:
            return result
        
        # Encode signal directions
        signal_mapping = {'BUY': 1, 'HOLD': 0, 'SELL': -1}
        
        # Agent signals
        for agent in ['technical', 'fundamental', 'sentiment', 'ensemble']:
            if f'{agent}_direction' in agent_signals.columns:
                result[f'{agent}_signal'] = agent_signals[f'{agent}_direction'].map(signal_mapping)
                result[f'{agent}_confidence'] = agent_signals[f'{agent}_confidence']
                
                # Historical signal features
                for period in [5, 10, 20]:
                    result[f'{agent}_signal_avg_{period}'] = result[f'{agent}_signal'].rolling(window=period).mean()
                    result[f'{agent}_confidence_avg_{period}'] = result[f'{agent}_confidence'].rolling(window=period).mean()
        
        return result
    
    def create_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create time-based features
        
        Args:
            df: DataFrame with datetime index
            
        Returns:
            DataFrame with time features added
        """
        result = df.copy()
        
        # Ensure index is datetime
        if not isinstance(result.index, pd.DatetimeIndex):
            result.index = pd.to_datetime(result.index)
        
        # Time components
        result['hour'] = result.index.hour
        result['day_of_week'] = result.index.dayofweek
        result['day_of_month'] = result.index.day
        result['month'] = result.index.month
        result['quarter'] = result.index.quarter
        
        # Cyclical encoding
        result['hour_sin'] = np.sin(2 * np.pi * result['hour'] / 24)
        result['hour_cos'] = np.cos(2 * np.pi * result['hour'] / 24)
        result['day_sin'] = np.sin(2 * np.pi * result['day_of_week'] / 7)
        result['day_cos'] = np.cos(2 * np.pi * result['day_of_week'] / 7)
        result['month_sin'] = np.sin(2 * np.pi * result['month'] / 12)
        result['month_cos'] = np.cos(2 * np.pi * result['month'] / 12)
        
        # Market session
        result['is_asian_session'] = ((result['hour'] >= 0) & (result['hour'] < 9)).astype(int)
        result['is_european_session'] = ((result['hour'] >= 7) & (result['hour'] < 16)).astype(int)
        result['is_american_session'] = ((result['hour'] >= 13) & (result['hour'] < 22)).astype(int)
        
        # Weekend flag
        result['is_weekend'] = (result['day_of_week'] >= 5).astype(int)
        
        return result
    
    def create_target_variables(self, df: pd.DataFrame,
                               horizons: List[int] = [1, 5, 10, 20]) -> pd.DataFrame:
        """
        Create target variables for supervised learning
        
        Args:
            df: DataFrame with market data (must have 'close' column)
            horizons: List of forward-looking periods
            
        Returns:
            DataFrame with target variables added
        """
        result = df.copy()
        
        for horizon in horizons:
            # Future returns
            result[f'return_{horizon}'] = result['close'].pct_change(horizon).shift(-horizon)
            
            # Binary classification targets
            result[f'target_up_{horizon}'] = (result[f'return_{horizon}'] > 0).astype(int)
            result[f'target_down_{horizon}'] = (result[f'return_{horizon}'] < 0).astype(int)
            
            # Multi-class targets (strong up, up, neutral, down, strong down)
            result[f'target_class_{horizon}'] = pd.cut(
                result[f'return_{horizon}'],
                bins=[-np.inf, -0.01, -0.001, 0.001, 0.01, np.inf],
                labels=['strong_down', 'down', 'neutral', 'up', 'strong_up']
            )
        
        return result
    
    def create_all_features(self, 
                           market_data: pd.DataFrame,
                           economic_data: Dict[str, pd.DataFrame] = None,
                           news_data: pd.DataFrame = None,
                           agent_signals: pd.DataFrame = None,
                           create_targets: bool = True) -> pd.DataFrame:
        """
        Create all features at once
        
        Args:
            market_data: DataFrame with OHLCV data
            economic_data: Dictionary of economic indicators
            news_data: DataFrame with news sentiment
            agent_signals: DataFrame with agent signals
            create_targets: Whether to create target variables
            
        Returns:
            DataFrame with all features
        """
        result = market_data.copy()
        
        # Technical features
        print("Creating technical features...")
        result = self.create_technical_features(result)
        
        # Fundamental features
        if economic_data:
            print("Creating fundamental features...")
            result = self.create_fundamental_features(result, economic_data)
        
        # Sentiment features
        if news_data is not None:
            print("Creating sentiment features...")
            result = self.create_sentiment_features(result, news_data)
        
        # Agent signal features
        if agent_signals is not None:
            print("Creating agent signal features...")
            result = self.create_agent_signal_features(result, agent_signals)
        
        # Time features
        print("Creating time features...")
        result = self.create_time_features(result)
        
        # Target variables
        if create_targets:
            print("Creating target variables...")
            result = self.create_target_variables(result)
        
        # Store feature names
        self.feature_names = [col for col in result.columns if col not in ['open', 'high', 'low', 'close', 'volume']]
        
        print(f"Total features created: {len(self.feature_names)}")
        
        return result
    
    def select_features(self, df: pd.DataFrame, target_col: str,
                       method: str = 'correlation', top_k: int = 50) -> List[str]:
        """
        Select most important features
        
        Args:
            df: DataFrame with features and target
            target_col: Name of target column
            method: 'correlation', 'mutual_info', or 'random_forest'
            top_k: Number of top features to select
            
        Returns:
            List of selected feature names
        """
        from sklearn.feature_selection import mutual_info_regression, SelectKBest
        from sklearn.ensemble import RandomForestRegressor
        
        # Get feature columns
        feature_cols = [col for col in df.columns if col != target_col and 
                       not col.startswith('target_') and not col.startswith('return_')]
        
        # Remove rows with NaN in target
        clean_df = df[[target_col] + feature_cols].dropna()
        
        if clean_df.empty:
            print("Warning: No clean data available for feature selection")
            return feature_cols[:top_k]
        
        X = clean_df[feature_cols]
        y = clean_df[target_col]
        
        if method == 'correlation':
            # Correlation-based selection
            correlations = X.corrwith(y).abs().sort_values(ascending=False)
            selected = correlations.head(top_k).index.tolist()
            self.feature_importance = correlations.to_dict()
            
        elif method == 'mutual_info':
            # Mutual information-based selection
            mi_scores = mutual_info_regression(X, y, random_state=42)
            mi_df = pd.Series(mi_scores, index=feature_cols).sort_values(ascending=False)
            selected = mi_df.head(top_k).index.tolist()
            self.feature_importance = mi_df.to_dict()
            
        elif method == 'random_forest':
            # Random forest-based selection
            rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
            rf.fit(X, y)
            importances = pd.Series(rf.feature_importances_, index=feature_cols).sort_values(ascending=False)
            selected = importances.head(top_k).index.tolist()
            self.feature_importance = importances.to_dict()
        
        else:
            raise ValueError(f"Unknown method: {method}")
        
        print(f"Selected {len(selected)} features using {method} method")
        return selected
    
    def prepare_ml_dataset(self, df: pd.DataFrame, target_col: str,
                          selected_features: List[str] = None,
                          train_size: float = 0.7,
                          val_size: float = 0.15) -> Tuple:
        """
        Prepare dataset for ML training
        
        Args:
            df: DataFrame with features and targets
            target_col: Name of target column
            selected_features: List of features to use (None = use all)
            train_size: Proportion of training data
            val_size: Proportion of validation data (rest is test)
            
        Returns:
            Tuple of (X_train, X_val, X_test, y_train, y_val, y_test)
        """
        # Select features
        if selected_features is None:
            feature_cols = [col for col in df.columns if col != target_col and 
                           not col.startswith('target_') and not col.startswith('return_')]
        else:
            feature_cols = selected_features
        
        # Remove rows with NaN
        clean_df = df[[target_col] + feature_cols].dropna()
        
        # Split data (time series split - no shuffling)
        n = len(clean_df)
        train_end = int(n * train_size)
        val_end = int(n * (train_size + val_size))
        
        train_df = clean_df.iloc[:train_end]
        val_df = clean_df.iloc[train_end:val_end]
        test_df = clean_df.iloc[val_end:]
        
        X_train = train_df[feature_cols]
        X_val = val_df[feature_cols]
        X_test = test_df[feature_cols]
        
        y_train = train_df[target_col]
        y_val = val_df[target_col]
        y_test = test_df[target_col]
        
        print(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
        
        return X_train, X_val, X_test, y_train, y_val, y_test


if __name__ == "__main__":
    # Example usage
    print("Feature Engineering Module - Example Usage")
    
    # Create sample data
    dates = pd.date_range(start='2024-01-01', end='2026-02-23', freq='1H')
    sample_data = pd.DataFrame({
        'open': np.random.randn(len(dates)).cumsum() + 100,
        'high': np.random.randn(len(dates)).cumsum() + 101,
        'low': np.random.randn(len(dates)).cumsum() + 99,
        'close': np.random.randn(len(dates)).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, len(dates))
    }, index=dates)
    
    # Initialize feature engineer
    fe = FeatureEngineer()
    
    # Create features
    features_df = fe.create_all_features(sample_data)
    
    print(f"\nShape: {features_df.shape}")
    print(f"Features created: {len(fe.feature_names)}")
    print(f"\nSample features:\n{features_df.head()}")
