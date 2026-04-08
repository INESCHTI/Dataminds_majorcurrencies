import { NextResponse } from "next/server";
import { summarizePerformance } from "@/lib/server/agent-signals";

export async function GET() {
    const [technical, macro, sentiment, orchestrator] = await Promise.all([
        summarizePerformance("technical"),
        summarizePerformance("macro"),
        summarizePerformance("sentiment"),
        summarizePerformance("orchestrator"),
    ]);

    return NextResponse.json({
        technical,
        macro,
        sentiment,
        orchestrator,
    });
}
