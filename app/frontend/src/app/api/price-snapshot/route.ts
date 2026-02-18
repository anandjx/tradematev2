import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET(req: NextRequest) {
    const { searchParams } = new URL(req.url);
    const ticker = searchParams.get("ticker");
    const timeframe = searchParams.get("timeframe") || "1D";

    if (!ticker) {
        return NextResponse.json({ error: "Missing 'ticker' parameter." }, { status: 400 });
    }

    try {
        const upstream = await fetch(
            `${BACKEND_URL}/api/price-snapshot?ticker=${encodeURIComponent(ticker)}&timeframe=${encodeURIComponent(timeframe)}`,
            { cache: "no-store" }
        );

        const data = await upstream.json();

        return NextResponse.json(data, { status: upstream.ok ? 200 : 400 });
    } catch (err) {
        return NextResponse.json(
            { error: `Backend unreachable: ${err instanceof Error ? err.message : "unknown"}` },
            { status: 502 }
        );
    }
}
