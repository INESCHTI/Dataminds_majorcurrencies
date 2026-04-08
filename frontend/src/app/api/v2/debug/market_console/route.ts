import { NextResponse } from "next/server";
import { buildSignalResponse } from "@/lib/server/agent-signals";
import { getInfluxLatestQuotes, getPostgresPreview, getSourceFreshness } from "@/lib/server/source-freshness";

const PAIRS = ["EURUSD", "USDJPY", "GBPUSD", "USDCHF"];

export async function GET() {
    const [quotes, pgPreview] = await Promise.all([
        getInfluxLatestQuotes(PAIRS),
        getPostgresPreview(25),
    ]);

    const latency = [] as Array<Record<string, unknown>>;
    for (const pair of PAIRS) {
        const [signal, freshness] = await Promise.all([
            buildSignalResponse(pair),
            getSourceFreshness(pair),
        ]);

        const dataLatency = (signal as any)?.metadata?.data_latency ?? null;
        const sourceImpact = (signal as any)?.metadata?.data_source_freshness?.impact ?? null;
        latency.push({
            pair,
            decision: signal.signal.direction,
            confidence: signal.signal.confidence,
            latency_impact: dataLatency?.impact ?? null,
            source_impact: sourceImpact,
            source_freshness: freshness,
            reasoning: signal.signal.reasoning,
        });
    }

    return NextResponse.json({
        generated_at: new Date().toISOString(),
        pairs: PAIRS,
        influx_quotes_1h: quotes,
        postgres: pgPreview,
        latency_and_decision_impact: latency,
    });
}
