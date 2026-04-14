/* API client + React Query hooks for the Django backend. */
import type {
    CandleData,
    TradingSignal,
    AgentStatusResponse,
    KpiScorecard,
    TechnicalAnalysis,
    EconomicEvent,
    DailyPerformance,
    FreshnessHealthV2,
} from "@/types";

const API_BASE = "http://localhost:8000/api";

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

export class ApiRequestError extends Error {
    status?: number;

    constructor(message: string, status?: number) {
        super(message);
        this.name = "ApiRequestError";
        this.status = status;
    }
}

async function fetcher<T>(url: string, options: RequestInit = {}): Promise<T> {
    try {
        const res = await fetchWithTimeout(`${API_BASE}${url}`, { 
            cache: "no-store",
            ...options 
        }, 30000);
        
        if (!res.ok) {
            throw new ApiRequestError(`API error: ${res.status}`, res.status);
        }
        
        // Check if response has content
        const contentType = res.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await res.json();
        } else {
            throw new ApiRequestError(`Invalid content type: ${contentType}`);
        }
    } catch (error) {
        if (error instanceof ApiRequestError) {
            throw error;
        }
        throw new ApiRequestError(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
}

async function postFetcher<T>(url: string, data: any = {}): Promise<T> {
    try {
        const res = await fetchWithTimeout(`${API_BASE}${url}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
            cache: "no-store",
        }, 30000);
        
        if (!res.ok) {
            throw new ApiRequestError(`API error: ${res.status}`, res.status);
        }
        
        // Check if response has content
        const contentType = res.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await res.json();
        } else {
            throw new ApiRequestError(`Invalid content type: ${contentType}`);
        }
    } catch (error) {
        if (error instanceof ApiRequestError) {
            throw error;
        }
        throw new ApiRequestError(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
}

// â”€â”€â”€ API Functions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export const api = {
    prices: (pair: string, timeframe = "1D", limit = 200) =>
        fetcher<CandleData[]>(`/prices/${pair}/?timeframe=${timeframe}&limit=${limit}`),

    latestSignals: () =>
        fetcher<TradingSignal[]>("/signals/latest/"),

    agentStatus: () =>
        fetcher<AgentStatusResponse>("/agents/status/"),

    kpis: () =>
        fetcher<KpiScorecard>("/kpis/"),

    performance: () =>
        fetcher<DailyPerformance[]>("/analytics/performance/"),

    technicals: (pair: string) =>
        fetcher<TechnicalAnalysis>(`/technicals/${pair}/`),

    calendar: () =>
        fetcher<EconomicEvent[]>("/calendar/"),

    news: () =>
        fetcher<{ results: Array<{ title: string; source: string; published_at: string }> }>("/news/"),

    triggerAgents: (pair: string) =>
        fetch(`${API_BASE}/agents/run/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pair }),
        }).then((r) => r.json()),

    // V2 Monitoring endpoints
    v2: {
        healthCheck: () =>
            fetcher('/monitoring/health_check/'),
        
        driftDetection: () =>
            fetcher('/monitoring/drift_detection/'),
        
        agentPerformance: (days?: number) =>
            fetcher(`/monitoring/agent_performance/${days ? `?days=${days}` : ''}`),
        
        freshnessHealth: (targetMinutes: number = 240) =>
            fetcher(`/monitoring/freshness_health/?target_minutes=${targetMinutes}`),
        
        generateSignal: async (pair: string) => {
            const res = await fetchWithTimeout(`${API_BASE}/test/generate_signal`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pair }),
                cache: "no-store"
            }, 60000);  // 60 seconds for real signal generation
            if (!res.ok) throw new Error(`API error: ${res.status}`);
            return res.json();
        },
    },

    // Tactical Analysis endpoints
    tactical: {
        multitimeframeSignal: (symbol: string) =>
            postFetcher('/tactical/multitimeframe_signal/', { symbol }),
        
        generateTacticalReport: (includePositions: boolean = true) =>
            postFetcher('/tactical/generate_tactical_report/', { include_positions: includePositions }),
        
        mt5Status: () =>
            fetcher('/tactical/mt5_status/'),
        
        startMt5Service: () =>
            postFetcher('/tactical/start_mt5_service/'),
        
        stopMt5Service: () =>
            postFetcher('/tactical/stop_mt5_service/'),
    },

    // MCP Agent System endpoints
    mcp: {
        // Test endpoint for debugging
        testEndpoint: () =>
            postFetcher('/mcp/test/'),
        
        // MCP Agent Collecteur (Data Collection)
        startCollecteur: () =>
            postFetcher('/mcp/collecteur/start/'),
        
        stopCollecteur: () =>
            postFetcher('/mcp/collecteur/stop/'),
        
        getCollecteurStatus: () =>
            fetcher('/mcp/collecteur/status/'),
        
        getCollecteurContext: () =>
            fetcher('/mcp/collecteur/context/'),
        
        getCollecteurTools: () =>
            fetcher('/mcp/collecteur/tools/'),
        
        // MCP Agent Feeder (Data Distribution)
        startFeeder: () =>
            postFetcher('/mcp/feeder/start/'),
        
        stopFeeder: () =>
            postFetcher('/mcp/feeder/stop/'),
        
        getFeederStatus: () =>
            fetcher('/mcp/feeder/status/'),
        
        getFeederFeeds: () =>
            fetcher('/mcp/feeder/feeds/'),
        
        getFeederAgents: () =>
            fetcher('/mcp/feeder/agents/'),
        
        // Real-time agent data
        getAgentData: (agentName: string) =>
            fetcher(`/mcp/agents/${agentName}/data/`),
        
        getAgentSignals: () =>
            fetcher('/mcp/agents/signals/'),
        
        // System overview
        getSystemOverview: () =>
            fetcher('/mcp/system/overview/'),
        
        getRealTimeStats: () =>
            fetcher('/mcp/system/realtime-stats/'),
    },
    advanced: {
        llm: {
            getSampleStatements: () =>
                fetcher('/llm/sample_statements/'),
            
            analyzeStatements: async (statements: any[]) => {
                const res = await fetchWithTimeout(`${API_BASE}/llm/analyze_multiple_statements/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ statements }),
                    cache: "no-store"
                }, 15000);
                if (!res.ok) throw new Error(`API error: ${res.status}`);
                return res.json();
            },
        },
        
        patterns: {
            analyzeWithSampleData: async (symbol: string, timeframe: string) => {
                const res = await fetchWithTimeout(`${API_BASE}/patterns/analyze_with_sample_data/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ symbol, timeframe }),
                    cache: "no-store"
                }, 15000);
                if (!res.ok) throw new Error(`API error: ${res.status}`);
                return res.json();
            },
        },
        
        rl: {
            getOptimizationStats: () =>
                fetcher('/rl/get_optimization_stats/'),
            
            optimizeWeights: async (weights: any) => {
                const res = await fetchWithTimeout(`${API_BASE}/rl/optimize_weights/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(weights),
                    cache: "no-store"
                }, 15000);
                if (!res.ok) throw new Error(`API error: ${res.status}`);
                return res.json();
            },
        },
        
        timezone: {
            getCurrentSession: () =>
                fetcher('/timezone/get_current_session/'),
            
            getSessionRecommendations: async (currency: string) => {
                const res = await fetchWithTimeout(`${API_BASE}/timezone/get_session_recommendations/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ currency_pair: currency }),
                    cache: "no-store"
                }, 15000);
                if (!res.ok) throw new Error(`API error: ${res.status}`);
                return res.json();
            },
            
            optimizeSessionWeights: async (data: any) => {
                const res = await fetchWithTimeout(`${API_BASE}/timezone/optimize_session_weights/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data),
                    cache: "no-store"
                }, 15000);
                if (!res.ok) throw new Error(`API error: ${res.status}`);
                return res.json();
            },
            
            getSessionStatistics: () =>
                fetcher('/timezone/get_session_statistics/'),
        },
    },
};

// â”€â”€â”€ Custom Hooks â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
// These can be used with React Query (already installed):
//
//   import { useQuery } from "@tanstack/react-query";
//   const { data } = useQuery({ queryKey: ["prices", pair], queryFn: () => api.prices(pair) });
//
// For now, pages use mock data with optional API overlay.

