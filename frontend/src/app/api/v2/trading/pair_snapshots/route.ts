import { NextResponse } from "next/server";
import { tradingPairSnapshots } from "@/lib/server/agent-signals";

export async function GET() {
    const snapshots = await tradingPairSnapshots();
    return NextResponse.json({ snapshots });
}
