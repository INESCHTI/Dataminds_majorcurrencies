import { NextResponse } from "next/server";
import { aggregateTradeMetrics } from "@/lib/server/trade-metrics";

export async function GET() {
    const metrics = await aggregateTradeMetrics();
    return NextResponse.json(metrics);
}
