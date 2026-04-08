import { NextResponse } from "next/server";

export async function GET() {
    return NextResponse.json({
        sentiment_drift: {
            detected: false,
            ks_statistic: 0.08,
            p_value: 0.42,
            severity: "LOW",
        },
        volatility_drift: {
            current_regime: "NORMAL",
            shift_detected: false,
            z_score: 0.4,
            severity: "LOW",
        },
    });
}
