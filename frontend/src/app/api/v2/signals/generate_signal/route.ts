import { NextRequest, NextResponse } from "next/server";
import { buildSignalResponse } from "@/lib/server/agent-signals";

export async function POST(request: NextRequest) {
    try {
        const body = await request.json().catch(() => ({}));
        const pair = String(body?.pair ?? "EURUSD").toUpperCase();
        const started = Date.now();

        const payload = await buildSignalResponse(pair);
        payload.metadata.execution_time_ms = Date.now() - started;

        return NextResponse.json(payload);
    } catch (error) {
        return NextResponse.json(
            { error: error instanceof Error ? error.message : "Signal generation failed" },
            { status: 400 }
        );
    }
}
