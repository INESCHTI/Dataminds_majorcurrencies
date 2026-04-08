import { NextRequest, NextResponse } from "next/server";
import { listSignalHistory } from "@/lib/server/agent-signals";

export async function GET(request: NextRequest) {
    const { searchParams } = new URL(request.url);
    const pair = searchParams.get("pair");
    const limitRaw = Number(searchParams.get("limit") ?? 120);
    const limit = Number.isFinite(limitRaw) ? Math.max(20, Math.min(400, limitRaw)) : 120;

    const rows = await listSignalHistory(limit);
    const filtered = pair && pair !== "All"
        ? rows.filter((r) => String(r.pair) === pair || String(r.pairSymbol) === pair)
        : rows;

    return NextResponse.json({ results: filtered, count: filtered.length });
}
