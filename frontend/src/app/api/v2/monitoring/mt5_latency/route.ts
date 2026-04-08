import { NextRequest, NextResponse } from "next/server";
import { getSourceFreshness } from "@/lib/server/source-freshness";

const MT5_SCRAPE_INTERVAL_MS = 60 * 60 * 1000;

export async function GET(request: NextRequest) {
    const { searchParams } = new URL(request.url);
    const pairRaw = (searchParams.get("pair") || "EURUSD").toUpperCase();
    const pair = /^[A-Z]{6}$/.test(pairRaw) ? pairRaw : "EURUSD";

    const freshness = await getSourceFreshness(pair);
    const latestIso = freshness.ohlcv.latest_timestamp;
    const latestMs = latestIso ? new Date(latestIso).getTime() : null;
    const now = Date.now();

    const ageMs = latestMs !== null ? Math.max(0, now - latestMs) : null;
    const remainingMs = ageMs !== null ? Math.max(0, MT5_SCRAPE_INTERVAL_MS - ageMs) : null;

    return NextResponse.json({
        timestamp: new Date(now).toISOString(),
        pair,
        mt5: {
            available: freshness.ohlcv.available,
            latest_timestamp: latestIso,
            age_ms: ageMs,
            remaining_ms: remainingMs,
            scrape_interval_ms: MT5_SCRAPE_INTERVAL_MS,
            error: freshness.ohlcv.error || null,
        },
    });
}
