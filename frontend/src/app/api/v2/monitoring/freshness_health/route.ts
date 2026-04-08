import { NextRequest, NextResponse } from "next/server";
import { freshnessFromSentiment } from "@/lib/server/agent-signals";

export async function GET(request: NextRequest) {
    const { searchParams } = new URL(request.url);
    const targetRaw = searchParams.get("target_minutes");
    const targetMinutes = Number.isFinite(Number(targetRaw)) ? Number(targetRaw) : 240;

    const payload = await freshnessFromSentiment(targetMinutes);
    return NextResponse.json(payload);
}
