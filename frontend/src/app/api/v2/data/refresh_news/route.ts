import { NextResponse } from "next/server";

export async function POST() {
    return NextResponse.json(
        { status: "accepted", message: "Frontend-only mode: no external refresh worker configured." },
        { status: 202 }
    );
}
