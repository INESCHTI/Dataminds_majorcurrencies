// Type definitions for FastAPI and new backend features

// Signal Types
export interface SignalRequest {
    pair: string;
    timeframe?: string;
    use_orchestrator?: boolean;
    query?: string;
}

export interface SignalResponse {
    success: boolean;
    pair: string;
    signal: string;
    confidence: number;
    direction: 'BUY' | 'SELL' | 'NEUTRAL';
    timestamp: string;
    execution_time_ms: number;
    agent_votes: {
        [agentName: string]: {
            signal: number;
            confidence: number;
        };
    };
    market_regime: string;
}

// Forecast Types
export interface ForecastRequest {
    pair: string;
    periods?: number;
    include_anomalies?: boolean;
}

export interface ForecastResponse {
    success: boolean;
    pair: string;
    direction: 'UPTREND' | 'DOWNTREND' | 'SIDEWAYS';
    confidence: number;
    anomalies_detected: boolean;
    forecast_horizon: number;
    timestamp: string;
    individual_forecasts?: {
        [modelName: string]: {
            direction: string;
            confidence: number;
        };
    };
}

// Sentiment Analysis Types
export interface SentimentRequest {
    texts: string[];
    batch_size?: number;
}

export interface SentimentResult {
    text: string;
    sentiment: 'bullish' | 'bearish' | 'neutral';
    confidence: number;
    entities: string[];
}

export interface SentimentResponse {
    success: boolean;
    count: number;
    results: SentimentResult[];
}

// News Analysis Types
export interface NewsAnalysisRequest {
    title: string;
    content: string;
    source?: string;
}

export interface NewsAnalysisResponse {
    success: boolean;
    analysis: {
        title: string;
        sentiment: 'bullish' | 'bearish' | 'neutral';
        sentiment_confidence: number;
        relevance: number;
        impact_score: number;
        category: 'breaking' | 'central_bank' | 'economic_data' | 'market_analysis' | 'general';
        entities: string[];
        aspects: string[];
        source: string;
        timestamp: string;
    };
}

// Pattern Recognition Types
export interface Pattern {
    type: string;
    confidence: number;
    direction: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
    source: 'cnn' | 'technical';
    price_level: number;
}

export interface PatternAnalysisResponse {
    symbol: string;
    patterns: Pattern[];
    cnn_count: number;
    traditional_count: number;
    hybrid_confidence: number;
    chart_image?: string;
}

// Meta-Learning Types
export interface AgentPrediction {
    agent_name: string;
    signal: number;
    confidence: number;
}

export interface MetaLearningResponse {
    signal: number;
    direction: 'BUY' | 'SELL' | 'NEUTRAL';
    confidence: number;
    individual_results: {
        [modelName: string]: {
            signal: number;
            confidence: number;
            model: string;
        };
    };
    meta_features: {
        feature_importance?: { [feature: string]: number };
        class_probabilities?: number[];
    };
}

// COT (Commitment of Traders) Types
export interface COTPositioning {
    date: string;
    commercial_net: number;
    managed_net: number;
    commercial_pct: number;
    managed_pct: number;
    managed_extreme_pct: number;
    signal: 'bullish' | 'bearish' | 'neutral';
    signal_strength: number;
    total_open_interest: number;
}

export interface COTSignalResponse {
    pair: string;
    signal: 'strong_buy' | 'buy' | 'neutral' | 'sell' | 'strong_sell';
    confidence: number;
    base_positioning: {
        currency: string;
        positioning: COTPositioning;
    };
    quote_positioning: {
        currency: string;
        positioning: COTPositioning;
    };
    timestamp: string;
}

// Agent Status
export interface AgentStatus {
    success: boolean;
    agents: {
        [agentName: string]: {
            status: 'active' | 'inactive' | 'error';
            weight: number;
            last_signal?: string;
            last_update?: string;
        };
    };
    coordinator: {
        status: 'active' | 'inactive';
    };
    orchestrator: {
        status: 'active' | 'inactive';
    };
    timestamp: string;
}

// Time Series Data
export interface OHLCV {
    timestamp: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
}

// WebSocket Types
export interface WebSocketSignal {
    pair: string;
    signal: 'BUY' | 'SELL' | 'NEUTRAL';
    confidence: number;
    timestamp: string;
}

// ═══ Regime Classification ════════════════════════════════

export interface RegimeRequest {
    pair: string;
    periods?: number;
}

export interface RegimeResponse {
    success: boolean;
    pair: string;
    regime: 'trending' | 'ranging' | 'crisis' | 'recovery' | string;
    regime_id: number;
    probability: number;
    confidence: number;
    volatility: number;
    autocorr: number;
    agent_recommendations: Record<string, number>;
    risk_adjustment: number;
    timestamp: string;
}

export interface CurrentRegimeResponse {
    success: boolean;
    pair: string;
    regime: string;
    regime_id: number;
    confidence: number;
    volatility: number;
    agent_recommendations: Record<string, number>;
    risk_adjustment: number;
    timestamp: string;
    error?: string;
}

// ═══ New ML Agent Types ═══════════════════════════════════

export interface RiskMargins {
    margin_pct: number;
    stop_loss_pct: number;
    take_profit_pct: number;
    risk_reward: number;
    position_size_pct: number;
    direction: string;
    recommended_leverage: number;
}

export interface LSTMSignalResponse {
    success: boolean;
    pair: string;
    direction: 'BUY' | 'SELL' | 'NEUTRAL';
    confidence: number;
    predicted_return: number;
    probability_up: number;
    probability_down: number;
    model_uncertainty: number;
    feature_importance: Record<string, number>;
    explanation: string;
    timestamp: string;
    risk_margins?: RiskMargins;
    realized_volatility?: number;
}

export interface XGBoostMacroResponse {
    success: boolean;
    pair: string;
    direction: 'BUY' | 'SELL' | 'NEUTRAL';
    confidence: number;
    expected_return: number;
    probability: number;
    macro_factors: Record<string, number>;
    feature_importance: Record<string, number>;
    explanation: string;
    data_quality_score: number;
    timestamp: string;
    risk_margins?: RiskMargins;
}

export interface XGBoostFusionResponse {
    success: boolean;
    pair: string;
    direction: 'BUY' | 'SELL' | 'NEUTRAL';
    confidence: number;
    expected_return: number;
    probability_up: number;
    probability_down: number;
    agent_contributions: Record<string, number>;
    agent_disagreement: number;
    regime_adjusted: boolean;
    explanation: string;
    timestamp: string;
    risk_margins?: RiskMargins;
    realized_volatility?: number;
}

export interface RiskMetricsResponse {
    success: boolean;
    pair: string;
    var_95: number;
    var_99: number;
    cvar_95: number;
    realized_vol: number;
    ewma_vol: number;
    current_drawdown: number;
    max_drawdown: number;
    position_size_mult: number;
    risk_level: 'LOW' | 'MODERATE' | 'HIGH' | 'EXTREME';
    recommendation: string;
    timestamp: string;
}
