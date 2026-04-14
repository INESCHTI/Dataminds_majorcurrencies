"""
FastAPI Wrapper for High-Performance Endpoints
Provides async endpoints for time-critical operations
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django settings BEFORE importing Django components
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

import numpy as np

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
import uvicorn
from datetime import datetime
import logging

# Import existing Django components
from signal_layer.coordinator_agent_v2 import CoordinatorAgentV2
from signal_layer.orchestrator_agent import orchestrate_query
from ai_layer.time_series_forecaster import create_ensemble_forecaster
from ai_layer.financial_nlp import create_news_analyzer
from ai_layer.regime_classifier import create_regime_classifier, RegimeAdaptiveCoordinator
from ai_layer.lstm_technical_agent import create_lstm_agent
from ai_layer.xgboost_macro_agent import create_xgboost_macro_agent
from ai_layer.xgboost_coordinator import create_xgboost_coordinator
from ai_layer.risk_management import create_portfolio_risk_manager
from data_layer.timeseries_loader import TimeSeriesLoader

logger = logging.getLogger(__name__)

# Helper function to calculate real risk margins
def calculate_risk_margins(direction: str, confidence: float, volatility: float = 0.15, pair: str = ""):
    """
    Calculate real risk margins based on signal, confidence, and market volatility
    
    Returns dynamic stop-loss, take-profit, and position sizing recommendations
    """
    # Base risk parameters adjusted by direction
    if direction == 'BUY':
        base_stop_pct = 0.015  # 1.5% base stop
        base_target_pct = 0.03  # 3% base target
        risk_reward = 1.8
        position_size_mult = min(1.0, 0.5 + confidence * 0.5)  # 50-100% based on confidence
    elif direction == 'SELL':
        base_stop_pct = 0.020  # 2% base stop (higher for shorts)
        base_target_pct = 0.035  # 3.5% base target
        risk_reward = 1.75
        position_size_mult = min(0.8, 0.4 + confidence * 0.4)  # 40-80% for shorts
    else:  # NEUTRAL
        base_stop_pct = 0.01
        base_target_pct = 0.02
        risk_reward = 2.0
        position_size_mult = 0.3  # Low size for neutral
    
    # Adjust by confidence (higher confidence = tighter stop, higher target)
    confidence_factor = max(0.5, confidence)
    
    # Adjust by volatility (higher vol = wider stops, lower position size)
    vol_adjustment = 1 + (volatility - 0.15) * 2  # Normalize around 15% vol
    
    # Calculate final values
    stop_loss_pct = base_stop_pct * vol_adjustment / confidence_factor
    take_profit_pct = base_target_pct * confidence_factor / vol_adjustment
    
    # Recalculate R:R based on actual values
    actual_rr = take_profit_pct / stop_loss_pct if stop_loss_pct > 0 else 1.0
    
    return {
        "margin_pct": round(stop_loss_pct * 100, 2),
        "stop_loss_pct": round(stop_loss_pct * 100, 2),
        "take_profit_pct": round(take_profit_pct * 100, 2),
        "risk_reward": round(actual_rr, 2),
        "position_size_pct": round(position_size_mult * 100, 0),
        "direction": direction,
        "recommended_leverage": round(min(10, 1 / stop_loss_pct), 1) if stop_loss_pct > 0 else 1.0
    }

# Initialize FastAPI app
app = FastAPI(
    title="FX Alpha FastAPI",
    description="High-performance async API for FX trading signals",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances (singleton pattern)
coordinator = CoordinatorAgentV2()
forecaster = create_ensemble_forecaster()
news_analyzer = create_news_analyzer()
data_loader = TimeSeriesLoader()
regime_coordinator = RegimeAdaptiveCoordinator()

# New ML agents
lstm_agent = create_lstm_agent()
xgboost_macro = create_xgboost_macro_agent()
xgboost_coordinator = create_xgboost_coordinator()
risk_manager = create_portfolio_risk_manager()


# Pydantic models
class SignalRequest(BaseModel):
    pair: str = "EURUSD"
    timeframe: str = "1H"
    use_orchestrator: bool = False
    query: Optional[str] = None


class SignalResponse(BaseModel):
    success: bool
    pair: str
    signal: str
    confidence: float
    direction: str
    timestamp: str
    execution_time_ms: float
    agent_votes: Dict
    market_regime: str


class ForecastRequest(BaseModel):
    pair: str = "EURUSD"
    periods: int = 24
    include_anomalies: bool = True


class ForecastResponse(BaseModel):
    success: bool
    pair: str
    direction: str
    confidence: float
    anomalies_detected: bool
    forecast_horizon: int
    timestamp: str


class SentimentRequest(BaseModel):
    texts: List[str]
    batch_size: int = 10


class NewsAnalysisRequest(BaseModel):
    title: str
    content: str
    source: str = "unknown"


class RegimeRequest(BaseModel):
    pair: str = "EURUSD"
    periods: int = 50  # Number of periods to analyze


class RegimeResponse(BaseModel):
    success: bool
    pair: str
    regime: str
    regime_id: int
    probability: float
    confidence: float
    volatility: float
    autocorr: float
    agent_recommendations: Dict[str, float]
    risk_adjustment: float
    timestamp: str


class LSTMSignalResponse(BaseModel):
    success: bool
    pair: str
    direction: str
    confidence: float
    predicted_return: float
    probability_up: float
    probability_down: float
    model_uncertainty: float
    feature_importance: Dict[str, float]
    explanation: str
    timestamp: str


class XGBoostMacroResponse(BaseModel):
    success: bool
    pair: str
    direction: str
    confidence: float
    expected_return: float
    probability: float
    macro_factors: Dict[str, float]
    feature_importance: Dict[str, float]
    explanation: str
    data_quality_score: float
    timestamp: str


class XGBoostFusionResponse(BaseModel):
    success: bool
    pair: str
    direction: str
    confidence: float
    expected_return: float
    probability_up: float
    probability_down: float
    agent_contributions: Dict[str, float]
    agent_disagreement: float
    regime_adjusted: bool
    explanation: str
    timestamp: str


class RiskMetricsResponse(BaseModel):
    success: bool
    pair: str
    var_95: float
    var_99: float
    cvar_95: float
    realized_vol: float
    ewma_vol: float
    current_drawdown: float
    max_drawdown: float
    position_size_mult: float
    risk_level: str
    recommendation: str
    timestamp: str


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }


@app.post("/signals/generate", response_model=SignalResponse)
async def generate_signal(request: SignalRequest):
    """
    Generate trading signal (async high-performance endpoint)
    
    - **pair**: Currency pair (EURUSD, GBPUSD, USDJPY, etc.)
    - **timeframe**: Timeframe (1H, 4H, 1D)
    - **use_orchestrator**: Use LLM-based orchestration
    - **query**: Optional natural language query for orchestrator
    """
    start_time = datetime.now()
    
    try:
        base = request.pair[:3]
        quote = request.pair[3:6]
        
        if request.use_orchestrator and request.query:
            # Use orchestrated signal generation
            result = await asyncio.to_thread(
                coordinator.generate_orchestrated_signal,
                symbol=request.pair,
                base_currency=base,
                quote_currency=quote,
                query=request.query
            )
        else:
            # Use standard signal generation
            result = await asyncio.to_thread(
                coordinator.generate_final_signal,
                request.pair,
                base,
                quote
            )
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Map signal to response
        signal_direction = "NEUTRAL"
        if result.get('final_signal', 0) == 1:
            signal_direction = "BUY"
        elif result.get('final_signal', 0) == -1:
            signal_direction = "SELL"
        
        return SignalResponse(
            success=True,
            pair=request.pair,
            signal=result.get('direction', signal_direction),
            confidence=result.get('confidence', 0.0),
            direction=signal_direction,
            timestamp=datetime.now().isoformat(),
            execution_time_ms=execution_time,
            agent_votes=result.get('agent_votes', {}),
            market_regime=result.get('market_regime', 'unknown')
        )
        
    except Exception as e:
        logger.error(f"Error generating signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/forecast/ensemble", response_model=ForecastResponse)
async def ensemble_forecast(request: ForecastRequest):
    """
    Generate ensemble forecast using Prophet + Kats
    
    - **pair**: Currency pair
    - **periods**: Number of periods to forecast
    - **include_anomalies**: Detect anomalies in data
    """
    try:
        # Load data
        df = await asyncio.to_thread(
            data_loader.load_ohlcv,
            request.pair,
            timeframe="1h"
        )
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data available for {request.pair}")
        
        # Generate forecast
        result = await asyncio.to_thread(
            forecaster.ensemble_forecast,
            df,
            request.pair,
            request.periods
        )
        
        return ForecastResponse(
            success=result.get('direction') != 'NEUTRAL',
            pair=request.pair,
            direction=result.get('direction', 'NEUTRAL'),
            confidence=result.get('confidence', 0.0),
            anomalies_detected=result.get('anomalies_detected', False),
            forecast_horizon=request.periods,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error in forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sentiment/analyze")
async def analyze_sentiment(request: SentimentRequest):
    """
    Analyze sentiment for multiple texts using FinBERT
    
    - **texts**: List of texts to analyze
    - **batch_size**: Batch size for processing
    """
    try:
        results = await asyncio.to_thread(
            news_analyzer.finbert.analyze_batch,
            request.texts[:request.batch_size]  # Limit batch size
        )
        
        return {
            "success": True,
            "count": len(results),
            "results": [
                {
                    "text": r.text[:100] + "..." if len(r.text) > 100 else r.text,
                    "sentiment": r.sentiment,
                    "confidence": r.confidence,
                    "entities": r.entities
                }
                for r in results
            ]
        }
        
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/news/analyze")
async def analyze_news(request: NewsAnalysisRequest):
    """
    Analyze a financial news article
    
    - **title**: Article title
    - **content**: Article content
    - **source**: News source
    """
    try:
        result = await asyncio.to_thread(
            news_analyzer.analyze_article,
            request.title,
            request.content,
            request.source
        )
        
        return {
            "success": True,
            "analysis": result
        }
        
    except Exception as e:
        logger.error(f"Error analyzing news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/prices/{pair}")
async def get_prices(pair: str, periods: int = 100):
    """Get OHLCV prices for a pair (fast endpoint)"""
    try:
        df = await asyncio.to_thread(
            data_loader.load_ohlcv,
            pair,
            timeframe="1h"
        )
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No price data for {pair}")
        
        # Return last N periods
        recent = df.tail(periods)
        
        return {
            "success": True,
            "pair": pair,
            "count": len(recent),
            "prices": [
                {
                    "timestamp": row['timestamp'].isoformat() if hasattr(row['timestamp'], 'isoformat') else str(row['timestamp']),
                    "open": float(row['open']),
                    "high": float(row['high']),
                    "low": float(row['low']),
                    "close": float(row['close']),
                    "volume": float(row['volume'])
                }
                for _, row in recent.iterrows()
            ]
        }
        
    except Exception as e:
        logger.error(f"Error fetching prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/status")
async def agents_status():
    """Get status of all agents"""
    return {
        "success": True,
        "agents": {
            "technical": {"status": "active", "weight": 0.30},
            "macro": {"status": "active", "weight": 0.25},
            "sentiment": {"status": "active", "weight": 0.20},
            "geopolitical": {"status": "active", "weight": 0.25}
        },
        "coordinator": {"status": "active"},
        "orchestrator": {"status": "active"},
        "timestamp": datetime.now().isoformat()
    }


@app.post("/regime/classify", response_model=RegimeResponse)
async def classify_regime(request: RegimeRequest):
    """
    Classify current market regime using HMM
    
    Returns regime classification and adaptive agent weights
    - **pair**: Currency pair to analyze
    - **periods**: Number of historical periods to use
    """
    try:
        # Load recent price data
        df = await asyncio.to_thread(
            data_loader.load_ohlcv,
            request.pair,
            timeframe="1h"
        )
        
        if df.empty or len(df) < 30:
            raise HTTPException(status_code=404, detail=f"Insufficient data for {request.pair}")
        
        # Use last N periods
        recent_df = df.tail(request.periods)
        
        # Get adaptive weights based on regime
        adaptive_weights = await asyncio.to_thread(
            regime_coordinator.get_adaptive_weights,
            recent_df
        )
        
        # Get risk parameters
        risk_params = regime_coordinator.get_risk_parameters()
        
        # Get current regime info
        current_regime = regime_coordinator.current_regime
        
        if current_regime is None:
            raise HTTPException(status_code=500, detail="Regime classification failed")
        
        return {
            "success": True,
            "pair": request.pair,
            "regime": current_regime.regime,
            "regime_id": current_regime.regime_id,
            "probability": current_regime.probability,
            "confidence": current_regime.confidence,
            "volatility": current_regime.volatility,
            "autocorr": current_regime.autocorr,
            "agent_recommendations": adaptive_weights,
            "risk_adjustment": risk_params['position_size_mult'],
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error classifying regime: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/regime/current")
async def get_current_regime(pair: str = "EURUSD"):
    """Get current regime without recalculating weights"""
    try:
        regime = regime_coordinator.current_regime
        
        if regime is None:
            # Try to classify
            df = await asyncio.to_thread(
                data_loader.load_ohlcv,
                pair,
                timeframe="1h"
            )
            if not df.empty:
                await asyncio.to_thread(
                    regime_coordinator.get_adaptive_weights,
                    df.tail(50)
                )
                regime = regime_coordinator.current_regime
        
        if regime is None:
            return {
                "success": False,
                "error": "No regime data available",
                "pair": pair
            }
        
        return {
            "success": True,
            "pair": pair,
            "regime": regime.regime,
            "regime_id": regime.regime_id,
            "confidence": regime.confidence,
            "volatility": regime.volatility,
            "agent_recommendations": regime.agent_recommendations,
            "risk_adjustment": regime.risk_adjustment,
            "timestamp": regime.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting current regime: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/lstm/signal", response_model=LSTMSignalResponse)
async def lstm_signal(pair: str = "EURUSD"):
    """
    Generate signal from LSTM Technical Agent
    
    Deep learning prediction with attention mechanism
    - **pair**: Currency pair to analyze
    """
    try:
        df = await asyncio.to_thread(
            data_loader.load_ohlcv,
            pair,
            timeframe="1h"
        )
        
        if df.empty or len(df) < 60:
            raise HTTPException(status_code=404, detail=f"Insufficient data for {pair}")
        
        signal = await asyncio.to_thread(
            lstm_agent.predict,
            df,
            pair
        )
        
        # Calculate real risk margins based on signal and market conditions
        realized_vol = df['close'].pct_change().std() * np.sqrt(252) if len(df) > 1 else 0.15
        risk_margins = calculate_risk_margins(
            signal.direction, 
            signal.confidence, 
            volatility=float(realized_vol),
            pair=pair
        )
        
        return {
            "success": True,
            "pair": pair,
            "direction": signal.direction,
            "confidence": signal.confidence,
            "predicted_return": signal.predicted_return,
            "probability_up": signal.probability_up,
            "probability_down": signal.probability_down,
            "model_uncertainty": signal.model_uncertainty,
            "feature_importance": signal.feature_importance,
            "explanation": signal.explanation,
            "timestamp": signal.timestamp.isoformat(),
            "risk_margins": risk_margins,
            "realized_volatility": round(float(realized_vol), 4)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LSTM signal error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/xgboost-macro/signal", response_model=XGBoostMacroResponse)
async def xgboost_macro_signal(pair: str = "EURUSD"):
    """
    Generate signal from XGBoost Macro Agent
    
    ML-based macroeconomic analysis with SHAP explanations
    - **pair**: Currency pair to analyze
    """
    try:
        # Load mock macro data (in production, this would come from FRED/DB)
        import pandas as pd
        base = pair[:3]
        quote = pair[3:6]
        
        rates_data = pd.DataFrame({
            f'{base}_rate': [5.25] * 10,
            f'{quote}_rate': [4.50] * 10,
        })
        
        inflation_data = pd.DataFrame({
            f'{base}_inflation': [3.2] * 10,
            f'{quote}_inflation': [2.8] * 10,
        })
        
        economic_data = pd.DataFrame({
            'gdp_surprise': [0.1] * 10,
            'pmi_surprise': [0.5] * 10,
            'employment_surprise': [-0.2] * 10,
            'cpi_surprise': [0.3] * 10,
        })
        
        signal = await asyncio.to_thread(
            xgboost_macro.predict,
            rates_data,
            inflation_data,
            economic_data,
            pair
        )
        
        # Calculate real risk margins
        risk_margins = calculate_risk_margins(
            signal.direction, 
            signal.confidence,
            volatility=0.12,  # Default for macro signals
            pair=pair
        )
        
        return {
            "success": True,
            "pair": pair,
            "direction": signal.direction,
            "confidence": signal.confidence,
            "expected_return": signal.expected_return,
            "probability": signal.probability,
            "macro_factors": signal.macro_factors,
            "feature_importance": signal.feature_importance,
            "explanation": signal.explanation,
            "data_quality_score": signal.data_quality_score,
            "timestamp": signal.timestamp.isoformat(),
            "risk_margins": risk_margins
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"XGBoost macro signal error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/fusion/xgboost", response_model=XGBoostFusionResponse)
async def xgboost_fusion(pair: str = "EURUSD"):
    """
    XGBoost-based signal fusion (meta-learner)
    
    Advanced coordinator using gradient boosting to combine agent signals
    - **pair**: Currency pair to analyze
    """
    try:
        # Gather agent signals
        agent_signals = {}
        
        # Load price data first
        df = await asyncio.to_thread(data_loader.load_ohlcv, pair, timeframe="1h")
        
        # Try to get LSTM signal
        if not df.empty and len(df) >= 60:
            try:
                lstm_sig = await asyncio.to_thread(lstm_agent.predict, df, pair)
                agent_signals['lstm'] = {
                    'signal': lstm_sig.direction,
                    'confidence': lstm_sig.confidence
                }
            except Exception as e:
                logger.warning(f"LSTM signal failed: {e}")
        
        # Get traditional agent signals
        base, quote = pair[:3], pair[3:6]
        result = await asyncio.to_thread(
            coordinator.generate_final_signal,
            pair, base, quote
        )
        
        # Extract agent votes (can be list or dict)
        if isinstance(result, dict):
            agent_votes = result.get('agent_votes', [])
            if isinstance(agent_votes, list):
                for agent_data in agent_votes:
                    if isinstance(agent_data, dict):
                        agent_signals[agent_data.get('agent', 'unknown')] = {
                            'signal': agent_data.get('signal', 0),
                            'confidence': agent_data.get('confidence', 0.5)
                        }
            elif isinstance(agent_votes, dict):
                # If it's a dict, use keys as agent names
                for agent_name, agent_data in agent_votes.items():
                    if isinstance(agent_data, dict):
                        agent_signals[agent_name] = {
                            'signal': agent_data.get('signal', 0),
                            'confidence': agent_data.get('confidence', 0.5)
                        }
                    else:
                        agent_signals[agent_name] = {'signal': 0, 'confidence': 0.5}
        else:
            logger.warning(f"result is not a dict: {type(result)}")
        
        # Get regime
        regime = None
        if not df.empty and len(df) >= 30:
            try:
                await asyncio.to_thread(
                    regime_coordinator.get_adaptive_weights,
                    df.tail(50)
                )
                current_regime = regime_coordinator.current_regime
                if current_regime:
                    regime = {
                        'regime_id': current_regime.regime_id,
                        'confidence': current_regime.confidence,
                        'volatility': current_regime.volatility,
                        'agent_recommendations': current_regime.agent_recommendations
                    }
            except Exception as e:
                logger.warning(f"Regime detection failed: {e}")
        
        # Fuse with XGBoost
        fusion = await asyncio.to_thread(
            xgboost_coordinator.fuse_signals,
            agent_signals,
            pair,
            regime,
            df if not df.empty else None
        )
        
        # Calculate real risk margins for fusion signal
        realized_vol = df['close'].pct_change().std() * np.sqrt(252) if not df.empty and len(df) > 1 else 0.15
        risk_margins = calculate_risk_margins(
            fusion.direction,
            fusion.confidence,
            volatility=float(realized_vol),
            pair=pair
        )
        
        return {
            "success": True,
            "pair": pair,
            "direction": fusion.direction,
            "confidence": fusion.confidence,
            "expected_return": fusion.expected_return,
            "probability_up": fusion.probability_up,
            "probability_down": fusion.probability_down,
            "agent_contributions": fusion.agent_contributions,
            "agent_disagreement": fusion.agent_disagreement,
            "regime_adjusted": fusion.regime_adjusted,
            "explanation": fusion.explanation,
            "timestamp": fusion.timestamp.isoformat(),
            "risk_margins": risk_margins,
            "realized_volatility": round(float(realized_vol), 4)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"XGBoost fusion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/xgboost-macro/train")
async def train_xgboost_macro(pair: str = "EURUSD", days: int = 90):
    """
    Train XGBoost Macro Agent on historical data
    
    - **pair**: Currency pair to train on
    - **days**: Number of days of historical data to use
    """
    try:
        import pandas as pd
        import numpy as np
        
        logger.info(f"Starting XGBoost macro training for {pair}")
        
        # Load historical price data
        df = await asyncio.to_thread(
            data_loader.load_ohlcv,
            pair,
            timeframe="1h"
        )
        
        if df.empty or len(df) < 100:
            raise HTTPException(status_code=404, detail=f"Insufficient data for {pair}")
        
        logger.info(f"Loaded {len(df)} data points")
        
        n_samples = len(df)
        base = pair[:3]
        quote = pair[3:6]
        
        # Generate synthetic macro data for training purposes
        rates_data = pd.DataFrame({
            f'{base}_rate': 5.0 + np.random.randn(n_samples).cumsum() * 0.1,
            f'{quote}_rate': 4.5 + np.random.randn(n_samples).cumsum() * 0.1,
        })
        
        inflation_data = pd.DataFrame({
            f'{base}_inflation': 3.0 + np.random.randn(n_samples) * 0.5,
            f'{quote}_inflation': 2.5 + np.random.randn(n_samples) * 0.5,
        })
        
        economic_data = pd.DataFrame({
            'gdp_surprise': np.random.randn(n_samples) * 0.3,
            'pmi_surprise': np.random.randn(n_samples) * 0.5,
            'employment_surprise': np.random.randn(n_samples) * 0.3,
            'cpi_surprise': np.random.randn(n_samples) * 0.4,
        })
        
        # Engineer features for all samples
        features_list = []
        targets = []
        
        max_samples = min(n_samples - 24, 500)
        logger.info(f"Generating {max_samples} training samples...")
        
        for i in range(max_samples):
            try:
                # Get window of data
                window_rates = rates_data.iloc[i:i+10]
                window_inf = inflation_data.iloc[i:i+10]
                window_econ = economic_data.iloc[i:i+10]
                
                # Engineer features
                features_df = xgboost_macro._engineer_features(
                    window_rates, window_inf, window_econ, base, quote
                )
                
                if features_df is None or features_df.empty:
                    logger.warning(f"Empty features at index {i}, skipping")
                    continue
                    
                features_list.append(features_df.iloc[0].values)
                
                # Target: future return direction
                future_return = (df['close'].iloc[i+24] - df['close'].iloc[i]) / df['close'].iloc[i]
                if future_return > 0.002:
                    targets.append(1)  # UP
                elif future_return < -0.002:
                    targets.append(-1)  # DOWN
                else:
                    targets.append(0)  # NEUTRAL
                    
            except Exception as e:
                logger.warning(f"Error processing sample {i}: {e}")
                continue
        
        logger.info(f"Generated {len(features_list)} valid samples")
        
        if len(features_list) < 50:
            raise HTTPException(status_code=400, detail=f"Insufficient training samples: {len(features_list)}")
        
        # Create DataFrame with feature names
        feature_names = xgboost_macro.feature_names if xgboost_macro.feature_names else [f'feat_{i}' for i in range(len(features_list[0]))]
        X = pd.DataFrame(features_list, columns=feature_names)
        y = np.array(targets)
        
        logger.info(f"Training with X shape: {X.shape}, y shape: {y.shape}")
        
        # Train model
        result = await asyncio.to_thread(
            xgboost_macro.train,
            X,
            y
        )
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=f"Training failed: {result['error']}")
        
        # Save model with joblib
        import joblib
        model_path = os.path.join(xgboost_macro.model_dir, 'xgb_macro_model.joblib')
        joblib.dump(xgboost_macro.model, model_path)
        
        # Verify model is fitted
        if not hasattr(xgboost_macro.model, 'feature_importances_'):
            raise HTTPException(status_code=500, detail="Model training failed - not fitted")
        
        logger.info(f"XGBoost macro model saved to {model_path}")
        
        # Convert numpy types to Python native types for JSON serialization
        def convert_to_native(obj):
            if hasattr(obj, 'item'):  # numpy scalar
                return obj.item()
            elif isinstance(obj, dict):
                return {k: convert_to_native(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_to_native(x) for x in obj]
            return obj
        
        return {
            "success": True,
            "pair": pair,
            "training_samples": int(len(X)),
            "train_accuracy": float(result.get('train_accuracy', 0)),
            "val_accuracy": float(result.get('val_accuracy', 0)),
            "model_path": str(model_path),
            "feature_importance": convert_to_native(result.get('feature_importance', {}))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"XGBoost macro training error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/fusion/xgboost/train")
async def train_xgboost_coordinator(pair: str = "EURUSD", samples: int = 200):
    """
    Train XGBoost Coordinator (meta-learner) on historical agent signals
    
    - **pair**: Currency pair to train on
    - **samples**: Number of training samples to generate
    """
    try:
        # Generate synthetic training data for coordinator
        np = __import__('numpy')
        
        agent_signals_history = []
        market_outcomes = []
        
        for _ in range(samples):
            # Generate random agent signals
            signals = {
                'technical': {
                    'signal': np.random.choice(['BUY', 'SELL', 'NEUTRAL']),
                    'confidence': np.random.uniform(0.5, 0.9)
                },
                'macro': {
                    'signal': np.random.choice(['BUY', 'SELL', 'NEUTRAL']),
                    'confidence': np.random.uniform(0.5, 0.9)
                },
                'sentiment': {
                    'signal': np.random.choice(['BUY', 'SELL', 'NEUTRAL']),
                    'confidence': np.random.uniform(0.5, 0.9)
                },
                'geopolitical': {
                    'signal': np.random.choice(['BUY', 'SELL', 'NEUTRAL']),
                    'confidence': np.random.uniform(0.5, 0.9)
                },
                'lstm': {
                    'signal': np.random.choice(['BUY', 'SELL', 'NEUTRAL']),
                    'confidence': np.random.uniform(0.5, 0.9)
                }
            }
            agent_signals_history.append(signals)
            
            # Generate random outcome (in practice, this would be historical results)
            market_outcomes.append(np.random.choice([-1, 0, 1]))
        
        # Train coordinator
        result = await asyncio.to_thread(
            xgboost_coordinator.train,
            agent_signals_history,
            np.array(market_outcomes)
        )
        
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
        
        # Save model with joblib
        import joblib
        model_path = os.path.join(xgboost_coordinator.model_dir, 'xgb_coordinator_model.joblib')
        joblib.dump(xgboost_coordinator.model, model_path)
        
        # Verify model is fitted
        if not hasattr(xgboost_coordinator.model, 'feature_importances_'):
            raise HTTPException(status_code=500, detail="Model training failed - not fitted")
        
        return {
            "success": True,
            "pair": pair,
            "training_samples": samples,
            "train_accuracy": result.get('train_accuracy', 0),
            "val_accuracy": result.get('val_accuracy', 0),
            "model_path": model_path,
            "n_features": result.get('n_features', 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"XGBoost coordinator training error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/regime/train")
async def train_regime_classifier(pair: str = "EURUSD", days: int = 180):
    """
    Train HMM Regime Classifier on historical price data
    
    - **pair**: Currency pair to train on
    - **days**: Number of days of historical data
    """
    try:
        df = await asyncio.to_thread(
            data_loader.load_ohlcv,
            pair,
            timeframe="1h"
        )
        
        if df.empty or len(df) < 100:
            raise HTTPException(status_code=404, detail=f"Insufficient data for {pair}")
        
        # Train regime classifier
        await asyncio.to_thread(
            regime_coordinator.fit_classifier,
            df
        )
        
        # Save model
        import joblib
        hmm = regime_coordinator.regime_classifier
        model_path = os.path.join(hmm.model_dir, 'hmm_regime_model.joblib')
        joblib.dump(hmm.model, model_path)
        
        # Save scaler
        scaler_path = os.path.join(hmm.model_dir, 'scaler.joblib')
        joblib.dump({
            'mean': hmm.scaler_mean,
            'std': hmm.scaler_std
        }, scaler_path)
        
        return {
            "success": True,
            "pair": pair,
            "training_samples": len(df),
            "model_path": model_path,
            "n_regimes": hmm.n_regimes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Regime classifier training error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/risk/metrics", response_model=RiskMetricsResponse)
async def risk_metrics(pair: str = "EURUSD"):
    """
    Calculate comprehensive risk metrics
    
    VaR, CVaR, volatility, and position sizing recommendations
    - **pair**: Currency pair to analyze
    """
    try:
        df = await asyncio.to_thread(
            data_loader.load_ohlcv,
            pair,
            timeframe="1h"
        )
        
        if df.empty or len(df) < 30:
            raise HTTPException(status_code=404, detail=f"Insufficient data for {pair}")
        
        metrics = await asyncio.to_thread(
            risk_manager.calculate_risk_metrics,
            pair,
            df,
            position_value=10000,  # 10k position
            current_equity=100000  # 100k account
        )
        
        return {
            "success": True,
            "pair": pair,
            "var_95": metrics.var_95,
            "var_99": metrics.var_99,
            "cvar_95": metrics.cvar_95,
            "realized_vol": metrics.realized_vol,
            "ewma_vol": metrics.ewma_vol,
            "current_drawdown": metrics.current_drawdown,
            "max_drawdown": metrics.max_drawdown,
            "position_size_mult": metrics.position_size_mult,
            "risk_level": metrics.risk_level,
            "recommendation": metrics.recommendation,
            "timestamp": metrics.timestamp.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Risk metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for real-time signals
from fastapi import WebSocket

@app.websocket("/ws/signals")
async def websocket_signals(websocket: WebSocket):
    """WebSocket for real-time signal updates"""
    await websocket.accept()
    
    try:
        while True:
            # Receive pair from client
            data = await websocket.receive_json()
            pair = data.get('pair', 'EURUSD')
            
            # Generate signal
            result = coordinator.generate_and_record_signal(pair)
            
            # Send back to client
            await websocket.send_json({
                "pair": pair,
                "signal": result.get('direction', 'NEUTRAL'),
                "confidence": result.get('confidence', 0.0),
                "timestamp": datetime.now().isoformat()
            })
            
            # Rate limiting
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()


def start_fastapi_server(host: str = "0.0.0.0", port: int = 8001):
    """Start FastAPI server"""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_fastapi_server()
