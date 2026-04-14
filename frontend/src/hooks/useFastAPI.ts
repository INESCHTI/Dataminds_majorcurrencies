/* React Query hooks for FastAPI endpoints */
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fastApi } from "@/lib/fastapi";
import type {
    SignalRequest,
    ForecastRequest,
    SentimentRequest,
    NewsAnalysisRequest,
    SignalResponse,
    ForecastResponse,
    SentimentResponse,
    NewsAnalysisResponse,
    PatternAnalysisResponse,
    MetaLearningResponse,
    COTSignalResponse,
    AgentStatus,
    WebSocketSignal,
} from "@/types/fastapi";
import { useEffect, useRef, useState, useCallback } from "react";

// ═══ Signal Generation Hooks ═══════════════════════════════════

export function useGenerateSignal() {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: (request: SignalRequest) => fastApi.generateSignal(request),
        onSuccess: (data) => {
            // Invalidate related queries
            queryClient.invalidateQueries({ queryKey: ["signals"] });
        },
    });
}

export function useSignal(pair: string, useOrchestrator: boolean = false, query?: string) {
    return useQuery({
        queryKey: ["signal", pair, useOrchestrator, query],
        queryFn: () => fastApi.generateSignal({
            pair,
            use_orchestrator: useOrchestrator,
            query,
        }),
        enabled: !!pair,
        refetchInterval: 60000, // Refetch every minute
        staleTime: 30000,
    });
}

// ═══ Forecasting Hooks (Prophet + Kats) ════════════════════════

export function useEnsembleForecast() {
    return useMutation({
        mutationFn: (request: ForecastRequest) => fastApi.ensembleForecast(request),
    });
}

export function useForecast(pair: string, periods: number = 24) {
    return useQuery({
        queryKey: ["forecast", pair, periods],
        queryFn: () => fastApi.ensembleForecast({ pair, periods }),
        enabled: !!pair,
        refetchInterval: 300000, // Refetch every 5 minutes
        staleTime: 180000,
    });
}

// ═══ Sentiment Analysis Hooks (FinBERT) ════════════════════════

export function useAnalyzeSentiment() {
    return useMutation({
        mutationFn: (request: SentimentRequest) => fastApi.analyzeSentiment(request),
    });
}

export function useSentimentBatch(texts: string[]) {
    return useQuery({
        queryKey: ["sentiment", texts],
        queryFn: () => fastApi.analyzeSentiment({ texts, batch_size: 10 }),
        enabled: texts.length > 0,
    });
}

// ═══ News Analysis Hooks ══════════════════════════════════════

export function useAnalyzeNews() {
    return useMutation({
        mutationFn: (request: NewsAnalysisRequest) => fastApi.analyzeNews(request),
    });
}

// ═══ Pattern Recognition Hooks (CNN + Technical) ═════════════════

export function usePatternAnalysis() {
    return useMutation({
        mutationFn: ({ symbol, timeframe }: { symbol: string; timeframe: string }) =>
            fastApi.patterns.analyze(symbol, timeframe),
    });
}

export function usePatterns(symbol: string, timeframe: string = "1h") {
    return useQuery({
        queryKey: ["patterns", symbol, timeframe],
        queryFn: () => fastApi.patterns.analyze(symbol, timeframe),
        enabled: !!symbol,
        refetchInterval: 300000, // Refetch every 5 minutes
    });
}

// ═══ Meta-Learning Hooks ══════════════════════════════════════

export function useMetaLearner() {
    return useMutation({
        mutationFn: ({ predictions, marketFeatures }: { 
            predictions: any[]; 
            marketFeatures?: any 
        }) => fastApi.metaLearner.predict(predictions, marketFeatures),
    });
}

// ═══ COT (Commitment of Traders) Hooks ═══════════════════════

export function useCOTSignal(pair: string) {
    return useQuery({
        queryKey: ["cot", pair],
        queryFn: () => fastApi.cot.getSignal(pair),
        enabled: !!pair,
        refetchInterval: 3600000, // Refetch every hour (COT is weekly data)
        staleTime: 1800000,
    });
}

export function useAllCOTData() {
    return useQuery({
        queryKey: ["cot-all"],
        queryFn: () => fastApi.cot.getAllCurrencies(),
        refetchInterval: 3600000,
    });
}

// ═══ Price Data Hooks ════════════════════════════════════════

export function usePrices(pair: string, periods: number = 100) {
    return useQuery({
        queryKey: ["prices", pair, periods],
        queryFn: () => fastApi.getPrices(pair, periods),
        enabled: !!pair,
        refetchInterval: 60000,
    });
}

// ═══ Agent Status Hooks ══════════════════════════════════════

export function useAgentStatus() {
    return useQuery({
        queryKey: ["agent-status"],
        queryFn: () => fastApi.getAgentStatus(),
        refetchInterval: 30000, // Refetch every 30 seconds
    });
}

// ═══ Health Check Hook ═══════════════════════════════════════

export function useFastApiHealth() {
    return useQuery({
        queryKey: ["fastapi-health"],
        queryFn: () => fastApi.healthCheck(),
        refetchInterval: 30000,
        retry: 3,
    });
}

// ═══ WebSocket Hook for Real-time Signals ══════════════════════

export function useWebSocketSignals(pair: string) {
    const [signal, setSignal] = useState<WebSocketSignal | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const [error, setError] = useState<Error | null>(null);
    const wsRef = useRef<{ send: (data: any) => void; close: () => void; isConnected: () => boolean } | null>(null);
    const pairRef = useRef(pair);

    // Keep pair ref updated
    useEffect(() => {
        pairRef.current = pair;
        // Send pair update when it changes (if connected)
        if (wsRef.current?.isConnected()) {
            wsRef.current.send({ pair });
        }
    }, [pair]);

    useEffect(() => {
        try {
            wsRef.current = fastApi.webSocket.connect(
                (data) => {
                    setSignal(data);
                },
                (err) => {
                    setError(new Error("WebSocket error"));
                    setIsConnected(false);
                },
                () => {
                    // onConnect callback
                    setIsConnected(true);
                    // Send initial subscription
                    if (pairRef.current) {
                        wsRef.current?.send({ pair: pairRef.current });
                    }
                }
            );

            return () => {
                wsRef.current?.close();
                setIsConnected(false);
            };
        } catch (e) {
            setError(e instanceof Error ? e : new Error("WebSocket connection failed"));
        }
    }, []); // Empty deps - only connect once

    return { signal, isConnected, error };
}

// ═══ Combined Dashboard Hook ═══════════════════════════════════

export function useDashboardData(pair: string) {
    const signal = useSignal(pair);
    const forecast = useForecast(pair);
    const patterns = usePatterns(pair);
    const cot = useCOTSignal(pair);
    const prices = usePrices(pair);
    const agentStatus = useAgentStatus();
    const { signal: wsSignal, isConnected: wsConnected } = useWebSocketSignals(pair);

    const isLoading = signal.isLoading || forecast.isLoading || patterns.isLoading || 
                      cot.isLoading || prices.isLoading;
    
    const error = signal.error || forecast.error || patterns.error || 
                  cot.error || prices.error;

    return {
        signal: signal.data,
        forecast: forecast.data,
        patterns: patterns.data,
        cot: cot.data,
        prices: prices.data,
        agentStatus: agentStatus.data,
        wsSignal,
        wsConnected,
        isLoading,
        error,
        refetch: () => {
            signal.refetch();
            forecast.refetch();
            patterns.refetch();
            cot.refetch();
            prices.refetch();
        },
    };
}

// ═══ Optimistic Updates Helper ═════════════════════════════════

export function useOptimisticSignalUpdate() {
    const queryClient = useQueryClient();

    const updateSignal = useCallback((pair: string, newSignal: SignalResponse) => {
        queryClient.setQueryData(["signal", pair], newSignal);
    }, [queryClient]);

    return { updateSignal };
}

// ═══ Regime Classification Hooks ════════════════════════════

export function useRegimeClassification(pair: string, periods: number = 50) {
    return useQuery({
        queryKey: ["regime", pair, periods],
        queryFn: () => fastApi.regime.classify(pair, periods),
        refetchInterval: 300000, // Refetch every 5 minutes
        staleTime: 120000, // 2 minutes
    });
}

export function useCurrentRegime(pair: string) {
    return useQuery({
        queryKey: ["regime-current", pair],
        queryFn: () => fastApi.regime.getCurrent(pair),
        refetchInterval: 60000, // Refetch every minute
    });
}

export function useRegimeMutation() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ pair, periods }: { pair: string; periods: number }) =>
            fastApi.regime.classify(pair, periods),
        onSuccess: (data, variables) => {
            queryClient.setQueryData(["regime", variables.pair, variables.periods], data);
            queryClient.setQueryData(["regime-current", variables.pair], data);
        },
    });
}

// ═══ New ML Agent Hooks ═══════════════════════════════════

export function useLSTMSignal(pair: string) {
    return useQuery({
        queryKey: ["lstm", pair],
        queryFn: () => fastApi.lstm.getSignal(pair),
        refetchInterval: 300000, // 5 minutes
        staleTime: 120000,
    });
}

export function useXGBoostMacroSignal(pair: string) {
    return useQuery({
        queryKey: ["xgboost-macro", pair],
        queryFn: () => fastApi.xgboostMacro.getSignal(pair),
        refetchInterval: 300000,
        staleTime: 120000,
    });
}

export function useXGBoostFusion(pair: string) {
    return useQuery({
        queryKey: ["xgboost-fusion", pair],
        queryFn: () => fastApi.xgboostFusion.fuse(pair),
        refetchInterval: 300000,
        staleTime: 120000,
    });
}

export function useRiskMetrics(pair: string) {
    return useQuery({
        queryKey: ["risk", pair],
        queryFn: () => fastApi.risk.getMetrics(pair),
        refetchInterval: 60000, // 1 minute
        staleTime: 30000,
    });
}
