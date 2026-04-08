import { NextResponse } from "next/server";
import { getLatestSignal, resolveSignalsDir } from "@/lib/server/agent-signals";
import { aggregateTradeMetrics } from "@/lib/server/trade-metrics";
import { getSourceFreshness } from "@/lib/server/source-freshness";

const PAIRS = ["EURUSD", "USDJPY", "GBPUSD", "USDCHF"];
const AGENTS = ["technical", "macro", "sentiment", "orchestrator"] as const;

export async function GET() {
    const signalsDir = await resolveSignalsDir();
    const tradeMetrics = await aggregateTradeMetrics();
    const sourceFreshnessByPair: Record<string, unknown> = {};

    const matrix: Record<string, Record<string, unknown>> = {};
    for (const pair of PAIRS) {
        matrix[pair] = {};
        sourceFreshnessByPair[pair] = await getSourceFreshness(pair);
        for (const agent of AGENTS) {
            const payload = await getLatestSignal(agent, pair);
            matrix[pair][agent] = payload
                ? {
                    signal: payload.signal ?? null,
                    confidence: payload.confidence ?? null,
                    timestamp: payload.timestamp ?? null,
                    file: payload._filePath ?? null,
                }
                : null;
        }
    }

    return NextResponse.json({
        generated_at: new Date().toISOString(),
        sources: {
            signals_directory: signalsDir,
            pairs: PAIRS,
            agents: AGENTS,
        },
        latest_signals: matrix,
        source_freshness: sourceFreshnessByPair,
        trade_metrics: {
            total_closed: tradeMetrics.total_closed,
            win_rate: tradeMetrics.win_rate,
            total_pnl: tradeMetrics.total_pnl,
            profit_factor: tradeMetrics.profit_factor,
            max_drawdown: tradeMetrics.max_drawdown,
            by_pair: tradeMetrics.by_pair,
        },
    });
}
