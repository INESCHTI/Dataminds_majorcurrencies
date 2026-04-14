/* API client for FastAPI async endpoints (port 8001) */
import type {
    SignalRequest,
    SignalResponse,
    ForecastRequest,
    ForecastResponse,
    SentimentRequest,
    SentimentResponse,
    NewsAnalysisRequest,
    NewsAnalysisResponse,
    PatternAnalysisResponse,
    MetaLearningResponse,
    COTSignalResponse,
    AgentStatus,
    RegimeResponse,
    CurrentRegimeResponse,
    LSTMSignalResponse,
    XGBoostMacroResponse,
    XGBoostFusionResponse,
    RiskMetricsResponse,
} from "@/types/fastapi";

const FASTAPI_BASE = "http://localhost:8001";

async function fetchWithTimeout(input: string, init: RequestInit = {}, timeoutMs = 30000): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
        const response = await fetch(input, {
            ...init,
            signal: controller.signal,
        });
        clearTimeout(timeoutId);
        return response;
    } catch (error) {
        clearTimeout(timeoutId);
        if (error instanceof Error && error.name === 'AbortError') {
            throw new Error(`Request timeout after ${timeoutMs}ms`);
        }
        throw error;
    }
}

export class FastApiError extends Error {
    status?: number;

    constructor(message: string, status?: number) {
        super(message);
        this.name = "FastApiError";
        this.status = status;
    }
}

async function fetcher<T>(url: string, options: RequestInit = {}): Promise<T> {
    try {
        const res = await fetchWithTimeout(`${FASTAPI_BASE}${url}`, { 
            cache: "no-store",
            ...options 
        }, 30000);
        
        if (!res.ok) {
            throw new FastApiError(`API error: ${res.status}`, res.status);
        }
        
        return await res.json();
    } catch (error) {
        if (error instanceof FastApiError) {
            throw error;
        }
        throw new FastApiError(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
}

async function postFetcher<T>(url: string, data: any = {}): Promise<T> {
    try {
        const res = await fetchWithTimeout(`${FASTAPI_BASE}${url}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
            cache: "no-store",
        }, 30000);
        
        if (!res.ok) {
            throw new FastApiError(`API error: ${res.status}`, res.status);
        }
        
        return await res.json();
    } catch (error) {
        if (error instanceof FastApiError) {
            throw error;
        }
        throw new FastApiError(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
}

// ═══ FastAPI Endpoints ═══════════════════════════════════════
export const fastApi = {
    // Health check
    healthCheck: () =>
        fetcher<{ status: string; timestamp: string; version: string }>('/health'),

    // Signal Generation
    generateSignal: (request: SignalRequest) =>
        postFetcher<SignalResponse>('/signals/generate', request),

    // Ensemble Forecasting (Prophet + Kats)
    ensembleForecast: (request: ForecastRequest) =>
        postFetcher<ForecastResponse>('/forecast/ensemble', request),

    // Sentiment Analysis (FinBERT)
    analyzeSentiment: (request: SentimentRequest) =>
        postFetcher<SentimentResponse>('/sentiment/analyze', request),

    // News Analysis
    analyzeNews: (request: NewsAnalysisRequest) =>
        postFetcher<NewsAnalysisResponse>('/news/analyze', request),

    // Price Data
    getPrices: (pair: string, periods: number = 100) =>
        fetcher<{ success: boolean; pair: string; prices: Array<{
            timestamp: string;
            open: number;
            high: number;
            low: number;
            close: number;
            volume: number;
        }> }>(`/prices/${pair}?periods=${periods}`),

    // Agent Status
    getAgentStatus: () =>
        fetcher<AgentStatus>('/agents/status'),

    // Advanced Pattern Recognition (CNN + Technical)
    patterns: {
        analyze: async (symbol: string, timeframe: string = "1h") => {
            // This would call the Django backend which uses the new CNN module
            const res = await fetchWithTimeout(`http://localhost:8000/api/patterns/advanced/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbol, timeframe }),
                cache: "no-store"
            }, 30000);
            if (!res.ok) throw new FastApiError(`API error: ${res.status}`, res.status);
            return res.json() as Promise<PatternAnalysisResponse>;
        },
    },

    // Meta-Learning Ensemble
    metaLearner: {
        predict: async (predictions: any[], marketFeatures?: any) => {
            const res = await fetchWithTimeout(`http://localhost:8000/api/meta/predict/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ predictions, market_features: marketFeatures }),
                cache: "no-store"
            }, 15000);
            if (!res.ok) throw new FastApiError(`API error: ${res.status}`, res.status);
            return res.json() as Promise<MetaLearningResponse>;
        },
    },

    // COT (Commitment of Traders) Data
    cot: {
        getSignal: async (pair: string) => {
            const res = await fetchWithTimeout(`http://localhost:8000/api/cot/signal/?pair=${pair}`, {
                cache: "no-store"
            }, 15000);
            if (!res.ok) throw new FastApiError(`API error: ${res.status}`, res.status);
            return res.json() as Promise<COTSignalResponse>;
        },

        getAllCurrencies: async () => {
            const res = await fetchWithTimeout(`http://localhost:8000/api/cot/all/`, {
                cache: "no-store"
            }, 15000);
            if (!res.ok) throw new FastApiError(`API error: ${res.status}`, res.status);
            return res.json();
        },
    },

    // Regime Classification
    regime: {
        classify: async (pair: string, periods: number = 50) => {
            const res = await fetchWithTimeout(
                `http://localhost:8001/regime/classify`,
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ pair, periods }),
                },
                30000
            );
            if (!res.ok) throw new FastApiError(`API error: ${res.status}`, res.status);
            return res.json() as Promise<RegimeResponse>;
        },

        getCurrent: async (pair: string) => {
            const res = await fetchWithTimeout(
                `http://localhost:8001/regime/current?pair=${pair}`,
                { cache: "no-store" },
                15000
            );
            if (!res.ok) throw new FastApiError(`API error: ${res.status}`, res.status);
            return res.json() as Promise<CurrentRegimeResponse>;
        },
    },

    // New ML Agents
    lstm: {
        getSignal: async (pair: string) => {
            const res = await fetchWithTimeout(
                `http://localhost:8001/agents/lstm/signal?pair=${pair}`,
                { method: "POST", cache: "no-store" },
                30000
            );
            if (!res.ok) throw new FastApiError(`API error: ${res.status}`, res.status);
            return res.json() as Promise<LSTMSignalResponse>;
        },
    },

    xgboostMacro: {
        getSignal: async (pair: string) => {
            const res = await fetchWithTimeout(
                `http://localhost:8001/agents/xgboost-macro/signal?pair=${pair}`,
                { method: "POST", cache: "no-store" },
                30000
            );
            if (!res.ok) throw new FastApiError(`API error: ${res.status}`, res.status);
            return res.json() as Promise<XGBoostMacroResponse>;
        },
    },

    xgboostFusion: {
        fuse: async (pair: string) => {
            const res = await fetchWithTimeout(
                `http://localhost:8001/fusion/xgboost?pair=${pair}`,
                { method: "POST", cache: "no-store" },
                30000
            );
            if (!res.ok) throw new FastApiError(`API error: ${res.status}`, res.status);
            return res.json() as Promise<XGBoostFusionResponse>;
        },
    },

    risk: {
        getMetrics: async (pair: string) => {
            const res = await fetchWithTimeout(
                `http://localhost:8001/risk/metrics?pair=${pair}`,
                { cache: "no-store" },
                15000
            );
            if (!res.ok) throw new FastApiError(`API error: ${res.status}`, res.status);
            return res.json() as Promise<RiskMetricsResponse>;
        },
    },

    // WebSocket for real-time signals
    webSocket: {
        connect: (onMessage: (data: any) => void, onError?: (error: Event) => void, onConnect?: () => void) => {
            let ws: WebSocket | null = null;
            let messageQueue: any[] = [];
            let isOpen = false;
            let hasConnected = false;

            try {
                ws = new WebSocket(`ws://localhost:8001/ws/signals`);
            } catch (e) {
                console.warn('⚠️ WebSocket creation failed - FastAPI server may not be running');
                return {
                    send: () => {}, // No-op
                    close: () => {},
                    isConnected: () => false,
                };
            }
            
            ws.onopen = () => {
                console.log('✅ WebSocket connected');
                isOpen = true;
                hasConnected = true;
                // Send any queued messages
                while (messageQueue.length > 0) {
                    const msg = messageQueue.shift();
                    ws?.send(JSON.stringify(msg));
                }
                onConnect?.();
            };
            
            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    onMessage(data);
                } catch (e) {
                    console.error('WebSocket message parse error:', e);
                }
            };
            
            ws.onerror = (error) => {
                // Only log error if we haven't connected yet (prevents spam)
                if (!hasConnected) {
                    console.warn('⚠️ WebSocket connection failed - FastAPI server not available (this is OK if not using real-time features)');
                }
                onError?.(error);
            };
            
            ws.onclose = () => {
                if (isOpen) {
                    console.log('WebSocket disconnected');
                }
                isOpen = false;
            };
            
            return {
                send: (data: any) => {
                    if (isOpen && ws?.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify(data));
                    } else {
                        // Queue message until connected
                        messageQueue.push(data);
                    }
                },
                close: () => {
                    ws?.close();
                    isOpen = false;
                },
                isConnected: () => ws?.readyState === WebSocket.OPEN || false,
            };
        },
    },
};

export default fastApi;
