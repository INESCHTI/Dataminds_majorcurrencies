"""
Time Series Forecasting with Prophet and Kats
Advanced forecasting for FX price prediction and trend analysis
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logging.warning("Prophet not available - install with: pip install prophet")

try:
    from kats.consts import TimeSeriesData
    from kats.models.linear_model import LinearModel
    from kats.models.holtwinters import HoltWintersModel
    from kats.models.arima import ARIMAModel
    from kats.detectors.cusum_detection import CUSUMDetector
    KATS_AVAILABLE = True
except (ImportError, AttributeError) as e:
    KATS_AVAILABLE = False
    logging.warning(f"Kats not available: {e}")

logger = logging.getLogger(__name__)


@dataclass
class ForecastResult:
    symbol: str
    forecast: pd.DataFrame
    trend_direction: str
    confidence: float
    change_point_dates: List[datetime]
    anomaly_detected: bool
    model_type: str


class ProphetForecaster:
    """
    Facebook Prophet forecaster for FX trend prediction
    Handles seasonality, holidays, and changepoint detection
    """
    
    def __init__(self):
        self.models = {}  # Cache models per symbol
        self.last_training = {}
        
    def _get_or_create_model(self, symbol: str) -> Optional["Prophet"]:
        """Get cached model or create new one"""
        if symbol in self.models:
            # Retrain if older than 24 hours
            last_train = self.last_training.get(symbol)
            if last_train and (datetime.now() - last_train) < timedelta(hours=24):
                return self.models[symbol]
        
        if not PROPHET_AVAILABLE:
            return None
        
        # Create new Prophet model optimized for FX
        model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=False,  # FX doesn't have strong yearly seasonality
            changepoint_prior_scale=0.05,  # Conservative changepoint detection
            seasonality_prior_scale=10.0,
            interval_width=0.95
        )
        
        # Add custom seasonality for trading sessions
        model.add_seasonality(
            name='trading_session',
            period=1,
            fourier_order=3,
            condition_name='is_trading_hours'
        )
        
        self.models[symbol] = model
        return model
    
    def forecast(self, df: pd.DataFrame, symbol: str, 
                 periods: int = 24, freq: str = 'H') -> Optional[ForecastResult]:
        """
        Generate forecast using Prophet
        
        Args:
            df: DataFrame with 'timestamp' and 'close' columns
            symbol: Currency pair symbol
            periods: Number of periods to forecast
            freq: Frequency ('H' for hourly, 'D' for daily)
        """
        if not PROPHET_AVAILABLE:
            logger.error("Prophet not available - cannot generate forecast")
            return None
        
        try:
            # Prepare data for Prophet (requires 'ds' and 'y' columns)
            prophet_df = pd.DataFrame({
                'ds': pd.to_datetime(df['timestamp']),
                'y': df['close'].values,
                'is_trading_hours': self._is_trading_hours(pd.to_datetime(df['timestamp']))
            })
            
            # Get or create model
            model = self._get_or_create_model(symbol)
            if model is None:
                return None
            
            # Fit model
            model.fit(prophet_df)
            self.last_training[symbol] = datetime.now()
            
            # Generate future dataframe
            future = model.make_future_dataframe(periods=periods, freq=freq)
            future['is_trading_hours'] = self._is_trading_hours(future['ds'])
            
            # Predict
            forecast = model.predict(future)
            
            # Extract changepoints
            changepoints = model.changepoints.tolist()
            change_point_dates = [cp for cp in changepoints if cp > prophet_df['ds'].max()]
            
            # Determine trend direction
            last_price = prophet_df['y'].iloc[-1]
            forecast_mean = forecast['yhat'].iloc[-periods:].mean()
            
            if forecast_mean > last_price * 1.005:
                trend_direction = 'UPTREND'
                confidence = min(0.9, (forecast_mean / last_price - 1) * 100)
            elif forecast_mean < last_price * 0.995:
                trend_direction = 'DOWNTREND'
                confidence = min(0.9, (1 - forecast_mean / last_price) * 100)
            else:
                trend_direction = 'SIDEWAYS'
                confidence = 0.5
            
            # Anomaly detection via uncertainty intervals
            last_forecast = forecast.iloc[-1]
            uncertainty_width = last_forecast['yhat_upper'] - last_forecast['yhat_lower']
            anomaly_detected = uncertainty_width > last_forecast['yhat'] * 0.02  # 2% uncertainty
            
            return ForecastResult(
                symbol=symbol,
                forecast=forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper', 'trend']].tail(periods),
                trend_direction=trend_direction,
                confidence=float(confidence),
                change_point_dates=change_point_dates[:5],  # Top 5 changepoints
                anomaly_detected=anomaly_detected,
                model_type='prophet'
            )
            
        except Exception as e:
            logger.error(f"Error in Prophet forecast for {symbol}: {e}")
            return None
    
    def _is_trading_hours(self, timestamps: pd.DatetimeIndex) -> pd.Series:
        """Mark trading hours (8AM - 5PM UTC)"""
        timestamps = pd.to_datetime(timestamps)
        hours = timestamps.dt.hour
        return pd.Series((hours >= 8) & (hours <= 17))


class KatsForecaster:
    """
    Kats time series forecasting and anomaly detection
    Uses multiple models: Linear, Holt-Winters, ARIMA
    """
    
    def __init__(self):
        self.model_results = {}
    
    def forecast_linear(self, df: pd.DataFrame, symbol: str, 
                       periods: int = 24) -> Optional[ForecastResult]:
        """Linear model forecast"""
        if not KATS_AVAILABLE:
            return None
        
        try:
            # Prepare Kats TimeSeriesData
            kats_df = pd.DataFrame({
                'time': pd.to_datetime(df['timestamp']),
                'value': df['close'].values
            })
            ts = TimeSeriesData(kats_df)
            
            # Fit linear model
            model = LinearModel(ts, freq='H')
            model.fit()
            
            # Forecast
            forecast = model.predict(steps=periods)
            
            return self._process_kats_forecast(
                forecast, symbol, df['close'].iloc[-1], 'linear'
            )
            
        except Exception as e:
            logger.error(f"Error in Kats linear forecast: {e}")
            return None
    
    def forecast_holt_winters(self, df: pd.DataFrame, symbol: str, 
                             periods: int = 24) -> Optional[ForecastResult]:
        """Holt-Winters exponential smoothing forecast"""
        if not KATS_AVAILABLE:
            return None
        
        try:
            kats_df = pd.DataFrame({
                'time': pd.to_datetime(df['timestamp']),
                'value': df['close'].values
            })
            ts = TimeSeriesData(kats_df)
            
            model = HoltWintersModel(
                data=ts,
                seasonal_periods=24  # Hourly seasonality
            )
            model.fit()
            
            forecast = model.predict(steps=periods)
            
            return self._process_kats_forecast(
                forecast, symbol, df['close'].iloc[-1], 'holt_winters'
            )
            
        except Exception as e:
            logger.error(f"Error in Holt-Winters forecast: {e}")
            return None
    
    def detect_anomalies(self, df: pd.DataFrame) -> List[Dict]:
        """Detect anomalies using CUSUM"""
        if not KATS_AVAILABLE:
            return []
        
        try:
            kats_df = pd.DataFrame({
                'time': pd.to_datetime(df['timestamp']),
                'value': df['close'].values
            })
            ts = TimeSeriesData(kats_df)
            
            detector = CUSUMDetector(ts)
            change_points = detector.detector(
                interest_window=[len(ts) - 50, len(ts)],  # Last 50 points
                threshold=0.01
            )
            
            anomalies = []
            for cp in change_points:
                anomalies.append({
                    'timestamp': cp.start_time,
                    'change_point': True,
                    'metric': cp.metric,
                    'direction': 'up' if cp.direction == 1 else 'down'
                })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            return []
    
    def _process_kats_forecast(self, forecast, symbol: str, 
                               last_price: float, model_type: str) -> ForecastResult:
        """Process Kats forecast into standard format"""
        forecast_mean = forecast['fcst'].mean()
        
        if forecast_mean > last_price * 1.002:
            trend_direction = 'UPTREND'
            confidence = min(0.85, (forecast_mean / last_price - 1) * 200)
        elif forecast_mean < last_price * 0.998:
            trend_direction = 'DOWNTREND'
            confidence = min(0.85, (1 - forecast_mean / last_price) * 200)
        else:
            trend_direction = 'SIDEWAYS'
            confidence = 0.4
        
        return ForecastResult(
            symbol=symbol,
            forecast=forecast,
            trend_direction=trend_direction,
            confidence=float(confidence),
            change_point_dates=[],
            anomaly_detected=False,
            model_type=model_type
        )


class EnsembleForecaster:
    """
    Ensemble forecaster combining Prophet and Kats
    Uses weighted ensemble for robust predictions
    """
    
    def __init__(self):
        self.prophet = ProphetForecaster()
        self.kats = KatsForecaster()
        self.model_weights = {
            'prophet': 0.5,
            'linear': 0.25,
            'holt_winters': 0.25
        }
    
    def ensemble_forecast(self, df: pd.DataFrame, symbol: str, 
                         periods: int = 24) -> Dict:
        """
        Generate ensemble forecast from multiple models
        """
        forecasts = {}
        
        # Prophet forecast
        if PROPHET_AVAILABLE:
            prophet_result = self.prophet.forecast(df, symbol, periods)
            if prophet_result:
                forecasts['prophet'] = prophet_result
        
        # Kats forecasts
        if KATS_AVAILABLE:
            linear_result = self.kats.forecast_linear(df, symbol, periods)
            if linear_result:
                forecasts['linear'] = linear_result
            
            hw_result = self.kats.forecast_holt_winters(df, symbol, periods)
            if hw_result:
                forecasts['holt_winters'] = hw_result
        
        # Check for consensus
        if not forecasts:
            return {
                'symbol': symbol,
                'error': 'No forecasting models available',
                'direction': 'NEUTRAL',
                'confidence': 0.0
            }
        
        # Weighted ensemble
        weighted_direction = self._calculate_weighted_direction(forecasts)
        
        # Anomaly detection
        anomalies = self.kats.detect_anomalies(df) if KATS_AVAILABLE else []
        
        return {
            'symbol': symbol,
            'direction': weighted_direction['direction'],
            'confidence': weighted_direction['confidence'],
            'individual_forecasts': {
                name: {
                    'direction': f.trend_direction,
                    'confidence': f.confidence
                }
                for name, f in forecasts.items()
            },
            'anomalies_detected': len(anomalies) > 0,
            'anomaly_details': anomalies[:3],  # Top 3 anomalies
            'forecast_horizon': periods,
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_weighted_direction(self, forecasts: Dict[str, ForecastResult]) -> Dict:
        """Calculate weighted ensemble direction"""
        direction_scores = {'UPTREND': 0, 'DOWNTREND': 0, 'SIDEWAYS': 0}
        total_confidence = 0
        
        for model_name, forecast in forecasts.items():
            weight = self.model_weights.get(model_name, 0.33)
            confidence = forecast.confidence * weight
            direction_scores[forecast.trend_direction] += confidence
            total_confidence += confidence
        
        # Find dominant direction
        dominant_direction = max(direction_scores, key=direction_scores.get)
        
        # Calculate normalized confidence
        if total_confidence > 0:
            normalized_confidence = direction_scores[dominant_direction] / total_confidence
        else:
            normalized_confidence = 0.0
        
        return {
            'direction': dominant_direction,
            'confidence': min(0.95, normalized_confidence),
            'scores': direction_scores
        }


# Factory functions
def create_prophet_forecaster() -> ProphetForecaster:
    """Create Prophet forecaster"""
    return ProphetForecaster()


def create_kats_forecaster() -> KatsForecaster:
    """Create Kats forecaster"""
    return KatsForecaster()


def create_ensemble_forecaster() -> EnsembleForecaster:
    """Create ensemble forecaster"""
    return EnsembleForecaster()
