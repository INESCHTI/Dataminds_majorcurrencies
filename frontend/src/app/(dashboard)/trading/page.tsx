"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import {
    ArrowUpRight,
    ArrowDownRight,
    X,
    Loader2,
    CheckCircle2,
} from "lucide-react";
import { useState, useEffect, useCallback, useMemo } from "react";
import dynamic from "next/dynamic";

const TradingViewWidget = dynamic(
    () => import("@/components/tradingview-widget"),
    { ssr: false }
);

type PairKey = "EURUSD" | "USDJPY" | "USDCHF" | "GBPUSD";

interface Position {
    id: number;
    pair: string;
    side: string;
    size: number;
    entryPrice: number;
    currentPrice: number;
    stopLoss: number | null;
    takeProfit: number | null;
    pnl: number;
    pnlPct: number;
    status: string;
    openedAt: string;
}

interface Snapshot {
    signal: string;
    confidence: number;
    price: number;
    indicators: Record<string, number>;
}

const pairConfig: Record<PairKey, { price: number; isJpy: boolean; signal: string; indicators: Record<string, number> }> = {
    EURUSD: { price: 1.0852, isJpy: false, signal: "BUY", indicators: { RSI: 34.2, MACD: 0.00012, "BB Upper": 1.0891, "BB Lower": 1.0812, SMA50: 1.0845, SMA200: 1.0832, ATR: 0.0065 } },
    USDJPY: { price: 149.52, isJpy: true, signal: "SELL", indicators: { RSI: 72.1, MACD: -0.15, "BB Upper": 150.42, "BB Lower": 148.65, SMA50: 149.8, SMA200: 149.1, ATR: 0.85 } },
    USDCHF: { price: 0.8823, isJpy: false, signal: "NEUTRAL", indicators: { RSI: 48.5, MACD: 0.00003, "BB Upper": 0.8872, "BB Lower": 0.8771, SMA50: 0.882, SMA200: 0.8815, ATR: 0.0052 } },
    GBPUSD: { price: 1.2655, isJpy: false, signal: "BUY", indicators: { RSI: 38.7, MACD: 0.00025, "BB Upper": 1.271, "BB Lower": 1.2595, SMA50: 1.2645, SMA200: 1.262, ATR: 0.0078 } },
};

const PAIRS: PairKey[] = ["EURUSD", "GBPUSD", "USDCHF", "USDJPY"];
const MT5_SCRAPE_INTERVAL_MS = 60 * 60 * 1000;

const PAIR_INFO: Record<PairKey, { label: string; decimals: number }> = {
    EURUSD: { label: "Euro vs US Dollar", decimals: 5 },
    GBPUSD: { label: "British Pound vs US Dollar", decimals: 5 },
    USDCHF: { label: "US Dollar vs Swiss Franc", decimals: 5 },
    USDJPY: { label: "US Dollar vs Japanese Yen", decimals: 3 },
};

const signalMap: Record<string, string> = {
    BUY: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
    SELL: "bg-rose-500/20 text-rose-300 border-rose-500/40",
    NEUTRAL: "bg-slate-500/20 text-slate-300 border-slate-500/40",
    HOLD: "bg-slate-500/20 text-slate-300 border-slate-500/40",
};

function tfToTvInterval(tf: string): string {
    if (tf === "M1") return "1";
    if (tf === "M5") return "5";
    if (tf === "M15") return "15";
    if (tf === "M30") return "30";
    if (tf === "H1") return "60";
    if (tf === "H4") return "240";
    if (tf === "D1") return "D";
    return "60";
}

function formatMs(value: number | null): string {
    if (value === null) return "n/a";
    return `${Math.max(0, Math.round(value))} ms`;
}

export default function TradingPage() {
    const [selectedPair, setSelectedPair] = useState<PairKey>("EURUSD");
    const [timeframe, setTimeframe] = useState("H1");
    const [lotSize, setLotSize] = useState(0.1);
    const [slPips, setSlPips] = useState(40);
    const [tpPips, setTpPips] = useState(80);
    const [positions, setPositions] = useState<Position[]>([]);
    const [snapshots, setSnapshots] = useState<Record<string, Snapshot>>({});
    const [loading, setLoading] = useState(false);
    const [toast, setToast] = useState<{ message: string; type: string } | null>(null);

    const [latestScrapeIso, setLatestScrapeIso] = useState<string | null>(null);
    const [mt5Error, setMt5Error] = useState<string | null>(null);
    const [nowMs, setNowMs] = useState(Date.now());

    useEffect(() => {
        const tick = setInterval(() => setNowMs(Date.now()), 1000);
        return () => clearInterval(tick);
    }, []);

    useEffect(() => {
        const loadSnapshots = async () => {
            try {
                const res = await fetch("/api/v2/trading/pair_snapshots", { cache: "no-store" });
                if (!res.ok) return;
                const payload = await res.json();
                if (payload?.snapshots && typeof payload.snapshots === "object") {
                    setSnapshots(payload.snapshots as Record<string, Snapshot>);
                }
            } catch {
                // Keep fallback static config.
            }
        };

        loadSnapshots();
        const t = setInterval(loadSnapshots, 30000);
        return () => clearInterval(t);
    }, []);

    useEffect(() => {
        const loadMt5Latency = async () => {
            try {
                const res = await fetch(`/api/v2/monitoring/mt5_latency?pair=${selectedPair}`, { cache: "no-store" });
                if (!res.ok) return;
                const payload = await res.json();
                setLatestScrapeIso(payload?.mt5?.latest_timestamp ?? null);
                setMt5Error(payload?.mt5?.error ?? null);
            } catch {
                setMt5Error("mt5_latency_fetch_failed");
            }
        };

        loadMt5Latency();
        const t = setInterval(loadMt5Latency, 30000);
        return () => clearInterval(t);
    }, [selectedPair]);

    const pairData = useMemo(() => {
        const out: Record<PairKey, { price: number; isJpy: boolean; signal: string; indicators: Record<string, number>; confidence: number; bid: number; ask: number }> = {
            EURUSD: { ...pairConfig.EURUSD, confidence: 0.5, bid: pairConfig.EURUSD.price, ask: pairConfig.EURUSD.price },
            GBPUSD: { ...pairConfig.GBPUSD, confidence: 0.5, bid: pairConfig.GBPUSD.price, ask: pairConfig.GBPUSD.price },
            USDCHF: { ...pairConfig.USDCHF, confidence: 0.5, bid: pairConfig.USDCHF.price, ask: pairConfig.USDCHF.price },
            USDJPY: { ...pairConfig.USDJPY, confidence: 0.5, bid: pairConfig.USDJPY.price, ask: pairConfig.USDJPY.price },
        };

        for (const pair of PAIRS) {
            const base = pairConfig[pair];
            const snap = snapshots[pair] || ({} as Snapshot);
            const price = Number.isFinite(Number(snap.price)) ? Number(snap.price) : base.price;
            const signal = String(snap.signal || base.signal || "NEUTRAL").toUpperCase();
            const confidence = Number.isFinite(Number(snap.confidence)) ? Number(snap.confidence) : 0.5;
            const spread = base.isJpy ? 0.01 : 0.0001;
            const bid = price - spread / 2;
            const ask = price + spread / 2;

            out[pair] = {
                ...base,
                ...(snap as Partial<typeof base>),
                price,
                signal,
                confidence,
                bid,
                ask,
                indicators: {
                    ...base.indicators,
                    ...((snap.indicators || {}) as Record<string, number>),
                },
            };
        }

        return out;
    }, [snapshots]);

    const data = pairData[selectedPair];
    const pipSize = data.isJpy ? 0.01 : 0.0001;

    const latestScrapeMs = latestScrapeIso ? new Date(latestScrapeIso).getTime() : null;
    const mt5LatencyMs = latestScrapeMs ? Math.max(0, nowMs - latestScrapeMs) : null;
    const mt5RemainingMs = mt5LatencyMs !== null ? Math.max(0, MT5_SCRAPE_INTERVAL_MS - mt5LatencyMs) : null;

    const fetchPositions = useCallback(async () => {
        try {
            const res = await fetch("/api/positions", { cache: "no-store" });
            if (!res.ok) return;
            const payload = await res.json();
            setPositions(Array.isArray(payload) ? payload : []);
        } catch {
            // keep current positions
        }
    }, []);

    useEffect(() => {
        fetchPositions();
    }, [fetchPositions]);

    const showToast = (message: string, type: string) => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 3000);
    };

    const openPosition = async (side: "BUY" | "SELL") => {
        setLoading(true);
        const price = data.price;
        const sl = side === "BUY" ? price - slPips * pipSize : price + slPips * pipSize;
        const tp = side === "BUY" ? price + tpPips * pipSize : price - tpPips * pipSize;

        try {
            const res = await fetch("/api/positions", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    pair: selectedPair,
                    side,
                    size: lotSize,
                    entryPrice: price,
                    stopLoss: +sl.toFixed(data.isJpy ? 2 : 5),
                    takeProfit: +tp.toFixed(data.isJpy ? 2 : 5),
                }),
            });

            if (!res.ok) {
                const err = await res.json();
                showToast(err.error || "Order failed", "error");
            } else {
                showToast(`${side} ${selectedPair} - ${lotSize} lot @ ${price}`, "success");
                fetchPositions();
            }
        } catch {
            showToast("Network error", "error");
        }

        setLoading(false);
    };

    const closePosition = async (id: number, currentPrice: number) => {
        try {
            const res = await fetch("/api/positions", {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id, currentPrice }),
            });

            if (res.ok) {
                showToast("Position closed", "success");
                fetchPositions();
            }
        } catch {
            showToast("Failed to close position", "error");
        }
    };

    return (
        <div className="flex h-full flex-col bg-[#11161d] text-slate-100">
            {toast && (
                <div className={`fixed right-4 top-4 z-50 flex items-center gap-2 rounded-xl px-4 py-3 text-sm font-medium text-white shadow-2xl ${toast.type === "success" ? "bg-emerald-600" : "bg-rose-600"}`}>
                    <CheckCircle2 className="size-4" />
                    {toast.message}
                </div>
            )}

            <header className="flex h-12 shrink-0 items-center gap-2 border-b border-slate-800 bg-[#1a1f27] px-4">
                <SidebarTrigger className="-ml-1" />
                <Separator orientation="vertical" className="mr-2 h-4" />
                <h1 className="text-sm font-semibold tracking-wide">Meta5 Trading Desk</h1>

                <div className="ml-4 flex items-center gap-1">
                    {["M1", "M5", "M15", "M30", "H1", "H4", "D1"].map((tf) => (
                        <button
                            key={tf}
                            onClick={() => setTimeframe(tf)}
                            className={`rounded border px-2.5 py-1 text-[11px] ${
                                timeframe === tf
                                    ? "border-cyan-500 bg-cyan-500/20 text-cyan-200"
                                    : "border-slate-700 bg-[#121722] text-slate-300 hover:bg-slate-800"
                            }`}
                        >
                            {tf}
                        </button>
                    ))}
                </div>

                <div className="ml-auto text-[11px] text-slate-400">Session: {new Date(nowMs).toLocaleTimeString()}</div>
            </header>

            <div className="flex-1 overflow-hidden p-2">
                <div className="grid h-full grid-cols-12 gap-2">
                    <aside className="col-span-12 flex flex-col gap-2 overflow-hidden lg:col-span-3 xl:col-span-2">
                        <Card className="border-slate-800 bg-[#171c24]">
                            <CardHeader className="px-3 py-2">
                                <CardTitle className="text-[12px] uppercase tracking-wide">Market Watch</CardTitle>
                            </CardHeader>
                            <CardContent className="p-0">
                                <div className="grid grid-cols-4 gap-0.5 border-y border-slate-800 bg-[#131821] px-3 py-1 text-[10px] text-slate-400">
                                    <div>Symbol</div>
                                    <div className="text-right">Bid</div>
                                    <div className="text-right">Ask</div>
                                    <div className="text-right">Chg%</div>
                                </div>
                                <div className="max-h-80 overflow-auto">
                                    {PAIRS.map((pair) => {
                                        const row = pairData[pair];
                                        const dec = PAIR_INFO[pair].decimals;
                                        const change = ((row.confidence - 0.5) * 10).toFixed(1);

                                        return (
                                            <button
                                                key={pair}
                                                onClick={() => setSelectedPair(pair)}
                                                className={`grid w-full grid-cols-4 gap-0.5 border-b border-slate-800 px-3 py-2 text-[11px] ${
                                                    selectedPair === pair ? "bg-cyan-500/10" : "hover:bg-slate-800/60"
                                                }`}
                                            >
                                                <div className="text-left font-mono text-slate-100">{pair.slice(0, 3)}/{pair.slice(3)}</div>
                                                <div className="text-right font-mono text-rose-300">{row.bid.toFixed(dec)}</div>
                                                <div className="text-right font-mono text-blue-300">{row.ask.toFixed(dec)}</div>
                                                <div className={`text-right font-mono ${Number(change) >= 0 ? "text-emerald-300" : "text-rose-300"}`}>{change}</div>
                                            </button>
                                        );
                                    })}
                                </div>
                            </CardContent>
                        </Card>

                        <Card className="border-slate-800 bg-[#171c24]">
                            <CardHeader className="px-3 py-2">
                                <CardTitle className="text-[12px] uppercase tracking-wide">Trade Ticket</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-2 px-3 pb-3">
                                <div className="text-[11px] text-slate-400">{selectedPair} | {PAIR_INFO[selectedPair].label}</div>
                                <div className="grid grid-cols-2 gap-1">
                                    <Button onClick={() => openPosition("SELL")} disabled={loading} className="h-9 bg-rose-700 font-bold hover:bg-rose-600">
                                        {loading ? <Loader2 className="size-4 animate-spin" /> : <ArrowDownRight className="mr-1 size-4" />} SELL
                                    </Button>
                                    <Button onClick={() => openPosition("BUY")} disabled={loading} className="h-9 bg-blue-700 font-bold hover:bg-blue-600">
                                        {loading ? <Loader2 className="size-4 animate-spin" /> : <ArrowUpRight className="mr-1 size-4" />} BUY
                                    </Button>
                                </div>

                                <div className="grid grid-cols-2 gap-2 text-[11px]">
                                    <div className="rounded border border-slate-700 bg-[#121722] px-2 py-1">
                                        <div className="text-slate-400">Lot</div>
                                        <select value={lotSize} onChange={(e) => setLotSize(+e.target.value)} className="w-full bg-transparent font-mono focus:outline-none">
                                            {[0.01, 0.05, 0.1, 0.2, 0.5, 1].map((v) => (
                                                <option key={v} value={v}>{v.toFixed(2)}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="rounded border border-slate-700 bg-[#121722] px-2 py-1">
                                        <div className="text-slate-400">R/R</div>
                                        <div className="font-mono text-cyan-300">1:{(tpPips / slPips).toFixed(1)}</div>
                                    </div>
                                    <div className="rounded border border-slate-700 bg-[#121722] px-2 py-1">
                                        <div className="text-slate-400">SL pips</div>
                                        <select value={slPips} onChange={(e) => setSlPips(+e.target.value)} className="w-full bg-transparent font-mono focus:outline-none">
                                            {[20, 30, 40, 50, 60, 80].map((v) => (
                                                <option key={v} value={v}>{v}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="rounded border border-slate-700 bg-[#121722] px-2 py-1">
                                        <div className="text-slate-400">TP pips</div>
                                        <select value={tpPips} onChange={(e) => setTpPips(+e.target.value)} className="w-full bg-transparent font-mono focus:outline-none">
                                            {[40, 60, 80, 100, 120, 160].map((v) => (
                                                <option key={v} value={v}>{v}</option>
                                            ))}
                                        </select>
                                    </div>
                                </div>

                                <div className="rounded border border-slate-700 bg-[#121722] px-2 py-1 text-[11px]">
                                    <div className="flex justify-between">
                                        <span className="text-slate-400">Signal</span>
                                        <span className="font-semibold">{data.signal}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-slate-400">Confidence</span>
                                        <span className="font-mono">{Math.round(data.confidence * 100)}%</span>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        <Card className="flex-1 overflow-auto border-slate-800 bg-[#171c24]">
                            <CardHeader className="px-3 py-2">
                                <CardTitle className="text-[12px] uppercase tracking-wide">Navigator</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-1 px-3 pb-3 text-[11px]">
                                <div className="text-slate-300">MetaTrader 5</div>
                                <div className="pl-3 text-slate-400">Comptes</div>
                                <div className="pl-3 text-slate-400">Indicateurs</div>
                                <div className="pl-3 text-slate-400">Experts Consultants</div>
                                <div className="pl-3 text-slate-400">Scripts</div>
                            </CardContent>
                        </Card>
                    </aside>

                    <main className="col-span-12 flex flex-col gap-2 overflow-hidden lg:col-span-9 xl:col-span-10">
                        <div className="grid grid-cols-1 gap-2 overflow-auto pr-1 xl:grid-cols-2">
                            {PAIRS.map((pair) => {
                                const row = pairData[pair];
                                const isSelected = pair === selectedPair;

                                return (
                                    <Card key={pair} className={`border ${isSelected ? "border-cyan-500/60" : "border-slate-800"} bg-[#171c24]`}>
                                        <CardHeader className="px-3 py-2">
                                            <div className="flex items-center justify-between">
                                                <button onClick={() => setSelectedPair(pair)} className="text-left">
                                                    <div className="font-mono text-sm text-white">{pair},{timeframe}</div>
                                                    <div className="text-[10px] text-slate-400">{PAIR_INFO[pair].label}</div>
                                                </button>
                                                <div className="flex items-center gap-2">
                                                    <Badge className={`${signalMap[row.signal] || signalMap.NEUTRAL} border text-[10px]`}>{row.signal}</Badge>
                                                    <div className="text-[11px] font-mono text-slate-200">{row.price.toFixed(PAIR_INFO[pair].decimals)}</div>
                                                </div>
                                            </div>
                                        </CardHeader>
                                        <CardContent className="p-2">
                                            <TradingViewWidget symbol={pair} interval={tfToTvInterval(timeframe)} theme="dark" height={280} />
                                        </CardContent>
                                    </Card>
                                );
                            })}
                        </div>

                        <Card className="border-slate-800 bg-[#171c24]">
                            <CardHeader className="px-3 py-2">
                                <div className="flex items-center justify-between">
                                    <CardTitle className="text-[12px] uppercase tracking-wide">Terminal - Open Positions</CardTitle>
                                    <Badge variant="outline" className="border-slate-700 text-[10px]">{positions.length} active</Badge>
                                </div>
                            </CardHeader>
                            <CardContent className="p-0">
                                {positions.length === 0 ? (
                                    <div className="py-6 text-center text-sm text-slate-400">No open positions. Use SELL/BUY in Trade Ticket.</div>
                                ) : (
                                    <Table>
                                        <TableHeader>
                                            <TableRow>
                                                <TableHead>Pair</TableHead>
                                                <TableHead>Side</TableHead>
                                                <TableHead>Size</TableHead>
                                                <TableHead>Entry</TableHead>
                                                <TableHead>SL</TableHead>
                                                <TableHead>TP</TableHead>
                                                <TableHead>Time</TableHead>
                                                <TableHead className="text-right">Action</TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {positions.map((pos) => (
                                                <TableRow key={pos.id}>
                                                    <TableCell className="font-medium">{pos.pair.slice(0, 3)}/{pos.pair.slice(3)}</TableCell>
                                                    <TableCell>
                                                        <Badge variant="outline" className={signalMap[pos.side] || signalMap.NEUTRAL}>{pos.side}</Badge>
                                                    </TableCell>
                                                    <TableCell className="font-mono text-xs">{pos.size}</TableCell>
                                                    <TableCell className="font-mono text-xs">{pos.entryPrice}</TableCell>
                                                    <TableCell className="font-mono text-xs text-rose-400">{pos.stopLoss || "-"}</TableCell>
                                                    <TableCell className="font-mono text-xs text-emerald-400">{pos.takeProfit || "-"}</TableCell>
                                                    <TableCell className="text-xs text-slate-400">{new Date(pos.openedAt).toLocaleTimeString()}</TableCell>
                                                    <TableCell className="text-right">
                                                        <Button
                                                            size="sm"
                                                            variant="destructive"
                                                            className="h-7 text-xs"
                                                            onClick={() => closePosition(pos.id, (snapshots[pos.pair]?.price || pairConfig[pos.pair as PairKey]?.price || pos.entryPrice))}
                                                        >
                                                            <X className="mr-1 size-3" /> Close
                                                        </Button>
                                                    </TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                )}
                            </CardContent>
                        </Card>

                        <div className="grid grid-cols-1 gap-2 rounded border border-slate-800 bg-[#151b23] px-3 py-2 text-[11px] text-slate-300 md:grid-cols-4">
                            <div className="flex items-center justify-between gap-2">
                                <span className="text-slate-400">Latence MT5</span>
                                <span className="font-mono text-cyan-300">{formatMs(mt5LatencyMs)}</span>
                            </div>
                            <div className="flex items-center justify-between gap-2">
                                <span className="text-slate-400">Prochain scrape dans</span>
                                <span className="font-mono text-amber-300">{formatMs(mt5RemainingMs)}</span>
                            </div>
                            <div className="flex items-center justify-between gap-2">
                                <span className="text-slate-400">Dernier scrape MT5</span>
                                <span className="font-mono">{latestScrapeIso ? new Date(latestScrapeIso).toLocaleTimeString() : "n/a"}</span>
                            </div>
                            <div className="flex items-center justify-between gap-2">
                                <span className="text-slate-400">Etat source</span>
                                <span className={`font-semibold ${mt5Error ? "text-rose-300" : "text-emerald-300"}`}>{mt5Error ? mt5Error : "OK"}</span>
                            </div>
                        </div>
                    </main>
                </div>
            </div>
        </div>
    );
}
