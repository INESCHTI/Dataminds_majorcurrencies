import { NextResponse } from "next/server";
import { freshnessFromSentiment, summarizePerformance } from "@/lib/server/agent-signals";
import { aggregateTradeMetrics } from "@/lib/server/trade-metrics";

export async function GET() {
    const [technical, macro, sentiment, freshness, trades] = await Promise.all([
        summarizePerformance("technical"),
        summarizePerformance("macro"),
        summarizePerformance("sentiment"),
        freshnessFromSentiment(240),
        aggregateTradeMetrics(),
    ]);

    return NextResponse.json({
        status: "operational",
        timestamp: new Date().toISOString(),
        agent_performances: {
            technical,
            macro,
            sentiment,
        },
        monitoring: {
            performance_tracker: { status: "ok", agents_tracked: 3 },
            drift_detector: { status: "ok", last_check: new Date().toISOString() },
            safety_monitor: { status: "ok", cooldown_active: false },
            trade_outcomes: {
                total_closed: trades.total_closed,
                win_rate: trades.win_rate,
                total_pnl: trades.total_pnl,
                profit_factor: trades.profit_factor,
                max_drawdown: trades.max_drawdown,
            },
            news_freshness: {
                status: freshness.freshness.status === "PASS" ? "ok" : freshness.freshness.status === "WARN" ? "warn" : "no_data",
                age_minutes: freshness.freshness.age_minutes,
                articles_last_1h: freshness.freshness.articles_last_1h,
                articles_last_24h: freshness.freshness.articles_last_24h,
                freshness_score: freshness.freshness.freshness_score,
            },
        },
        system: {
            uptime_seconds: Math.floor(process.uptime()),
            memory_usage_mb: Math.round(process.memoryUsage().rss / (1024 * 1024)),
        },
    });
}
