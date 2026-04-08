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

function normalizeApiBase(raw?: string): string {
    const base = (raw || "/api").trim().replace(/\/$/, "");
    if (!base) {
        return "/api";
    }
    if (base.endsWith("/api")) {
        return base;
    }
    return `${base}/api`;
}

const API_BASE = normalizeApiBase(process.env.NEXT_PUBLIC_API_URL);
const API_BASES = Array.from(new Set([API_BASE, "/api"]));

async function fetchWithTimeout(input: string, init: RequestInit = {}, timeoutMs = 15000): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
        return await fetch(input, {
            ...init,
            signal: controller.signal,
        });
    } finally {
        clearTimeout(timeoutId);
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

async function fetcher<T>(url: string): Promise<T> {
    let lastError: unknown = null;

    for (const base of API_BASES) {
        try {
            const res = await fetchWithTimeout(`${base}${url}`, { cache: "no-store" }, 15000);
            if (!res.ok) {
                lastError = new Error(`API error: ${res.status}`);
                continue;
            }
            return res.json();
        } catch (error) {
            lastError = error;
        }
    }

    throw lastError instanceof Error ? lastError : new Error("API fallback failed");
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

    triggerAgents: async (pair: string) => {
        for (const base of API_BASES) {
            try {
                const r = await fetch(`${base}/agents/run/`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ pair }),
                });
                if (r.ok) {
                    return r.json();
                }
            } catch {
                // try next base
            }
        }
        throw new ApiRequestError("Impossible de declencher les agents via les routes API configurees.");
    },

    // V2 Architecture Endpoints
    v2: {
        generateSignal: async (pair: string) => {
            try {
                let response: Response | null = null;
                for (const base of API_BASES) {
                    try {
                        const candidate = await fetchWithTimeout(
                            `${base}/v2/signals/generate_signal/`,
                            {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                cache: "no-store",
                                body: JSON.stringify({ pair }),
                            },
                            180000
                        );
                        response = candidate;
                        if (candidate.ok) {
                            break;
                        }
                    } catch {
                        // try next base
                    }
                }

                if (!response) {
                    throw new ApiRequestError("Aucune route API repondante pour generate_signal.");
                }

                if (!response.ok) {
                    let backendMessage = "";
                    try {
                        const payload = await response.json();
                        backendMessage = payload?.error || payload?.reason || "";
                    } catch {
                        // Ignore non-JSON error responses
                    }

                    const detail = backendMessage
                        ? ` (${backendMessage})`
                        : "";
                    throw new ApiRequestError(
                        `La generation du signal a echoue (HTTP ${response.status})${detail}.`,
                        response.status
                    );
                }

                return response.json();
            } catch (error) {
                if (error instanceof ApiRequestError) {
                    throw error;
                }

                if (error instanceof DOMException && error.name === "AbortError") {
                    throw new ApiRequestError(
                        "Le calcul du signal prend trop de temps (timeout 3 minutes). Reessayez.",
                    );
                }

                throw new ApiRequestError(
                    "Connexion API impossible. Verifiez la configuration NEXT_PUBLIC_API_URL et les routes /api.",
                );
            }
        },

        agentPerformance: () =>
            fetcher(`/v2/monitoring/agent_performance/`),

        healthCheck: () =>
            fetcher(`/v2/monitoring/health_check/`),

        driftDetection: () =>
            fetcher(`/v2/monitoring/drift_detection/`),

        freshnessHealth: (targetMinutes = 240) =>
            fetcher<FreshnessHealthV2>(`/v2/monitoring/freshness_health/?target_minutes=${targetMinutes}`),
    },
};

// â”€â”€â”€ Custom Hooks â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
// These can be used with React Query (already installed):
//
//   import { useQuery } from "@tanstack/react-query";
//   const { data } = useQuery({ queryKey: ["prices", pair], queryFn: () => api.prices(pair) });
//
// For now, pages use mock data with optional API overlay.

