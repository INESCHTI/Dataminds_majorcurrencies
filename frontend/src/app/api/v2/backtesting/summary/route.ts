import { NextResponse } from "next/server";
import { backtestingSummary } from "@/lib/server/agent-signals";

export async function GET() {
    const payload = await backtestingSummary();
    return NextResponse.json(payload);
}
