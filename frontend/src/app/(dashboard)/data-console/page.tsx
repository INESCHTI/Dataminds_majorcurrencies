"use client";

import { useEffect, useMemo, useState } from "react";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import { Database, RadioTower, AlertTriangle, CheckCircle2 } from "lucide-react";

export default function DataConsolePage() {
    const [payload, setPayload] = useState<any | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const load = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch("/api/v2/debug/market_console", { cache: "no-store" });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            setPayload(await res.json());
        } catch (e) {
            setError(e instanceof Error ? e.message : "failed");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        load();
        const t = setInterval(load, 30000);
        return () => clearInterval(t);
    }, []);

    const impactSummary = useMemo(() => {
        const rows = (payload?.latency_and_decision_impact || []) as any[];
        const high = rows.filter((r) => (r?.source_impact?.severity || "") === "HIGH").length;
        const medium = rows.filter((r) => (r?.source_impact?.severity || "") === "MEDIUM").length;
        const low = rows.filter((r) => (r?.source_impact?.severity || "") === "LOW").length;
        return { high, medium, low, total: rows.length };
    }, [payload]);

    return (
        <div className="flex flex-col h-full bg-[#080d18] text-slate-100 relative overflow-hidden">
            <header className="flex h-14 shrink-0 items-center gap-3 border-b border-white/5 bg-black/30 backdrop-blur-xl px-6">
                <SidebarTrigger className="-ml-1 text-slate-400" />
                <Separator orientation="vertical" className="h-5 bg-white/10" />
                <Database className="size-4 text-cyan-400" />
                <h1 className="text-sm font-bold text-white">Data Console (MT5/Influx/Postgres)</h1>
                <span className="text-[10px] font-mono text-slate-500 border border-slate-700 rounded px-1.5 py-0.5">Live Sources</span>
                <button onClick={load} className="ml-auto rounded-md border border-white/15 px-3 py-1 text-xs hover:bg-white/10">Refresh</button>
            </header>

            <div className="flex-1 overflow-auto p-6 space-y-5">
                {loading && <div className="text-sm text-slate-400">Loading live data...</div>}
                {error && <div className="text-sm text-rose-400">Error: {error}</div>}

                <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                    <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
                        <div className="text-[10px] text-slate-500 uppercase">Pairs Checked</div>
                        <div className="text-lg font-bold text-white">{impactSummary.total}</div>
                    </div>
                    <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-3">
                        <div className="text-[10px] text-rose-300 uppercase">Latency HIGH</div>
                        <div className="text-lg font-bold text-rose-200">{impactSummary.high}</div>
                    </div>
                    <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3">
                        <div className="text-[10px] text-amber-300 uppercase">Latency MEDIUM</div>
                        <div className="text-lg font-bold text-amber-200">{impactSummary.medium}</div>
                    </div>
                    <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3">
                        <div className="text-[10px] text-emerald-300 uppercase">Latency LOW</div>
                        <div className="text-lg font-bold text-emerald-200">{impactSummary.low}</div>
                    </div>
                </div>

                <section className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                    <div className="flex items-center gap-2 mb-3">
                        <RadioTower className="size-4 text-cyan-300" />
                        <h2 className="text-sm font-semibold">InfluxDB Quotes (1H)</h2>
                    </div>
                    <div className="overflow-auto">
                        <table className="w-full text-xs">
                            <thead className="text-slate-400 border-b border-white/10">
                                <tr>
                                    <th className="text-left py-2">Symbol</th>
                                    <th className="text-left py-2">Time</th>
                                    <th className="text-right py-2">Open</th>
                                    <th className="text-right py-2">High</th>
                                    <th className="text-right py-2">Low</th>
                                    <th className="text-right py-2">Close</th>
                                    <th className="text-right py-2">Volume</th>
                                </tr>
                            </thead>
                            <tbody>
                                {(payload?.influx_quotes_1h || []).map((q: any, i: number) => (
                                    <tr key={i} className="border-b border-white/[0.05]">
                                        <td className="py-2 font-mono text-white">{q.symbol}</td>
                                        <td className="py-2 text-slate-300">{q.time || "N/A"}</td>
                                        <td className="py-2 text-right">{q.open ?? "-"}</td>
                                        <td className="py-2 text-right">{q.high ?? "-"}</td>
                                        <td className="py-2 text-right">{q.low ?? "-"}</td>
                                        <td className="py-2 text-right text-cyan-300">{q.close ?? "-"}</td>
                                        <td className="py-2 text-right">{q.volume ?? "-"}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </section>

                <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                        <h2 className="text-sm font-semibold mb-3">Postgres: Economic Indicators</h2>
                        <pre className="text-xs text-slate-300 overflow-auto max-h-80">{JSON.stringify(payload?.postgres?.macro || [], null, 2)}</pre>
                    </div>
                    <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                        <h2 className="text-sm font-semibold mb-3">Postgres: News</h2>
                        <pre className="text-xs text-slate-300 overflow-auto max-h-80">{JSON.stringify(payload?.postgres?.news || [], null, 2)}</pre>
                    </div>
                </section>

                <section className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                    <h2 className="text-sm font-semibold mb-3">Latency Impact on Decision</h2>
                    <div className="space-y-3">
                        {(payload?.latency_and_decision_impact || []).map((row: any, i: number) => {
                            const severity = row?.source_impact?.severity || "LOW";
                            const cls = severity === "HIGH"
                                ? "border-rose-500/40 bg-rose-500/10"
                                : severity === "MEDIUM"
                                    ? "border-amber-500/40 bg-amber-500/10"
                                    : "border-emerald-500/40 bg-emerald-500/10";
                            return (
                                <div key={i} className={`rounded-lg border p-3 ${cls}`}>
                                    <div className="flex items-center justify-between mb-2">
                                        <div className="font-semibold text-white">{row.pair}</div>
                                        <div className="text-xs font-mono">Decision: {row.decision} ({Math.round((row.confidence || 0) * 100)}%)</div>
                                    </div>
                                    <div className="text-xs text-slate-200 mb-1">Source impact: {severity}</div>
                                    <div className="text-xs text-slate-300">{row.reasoning}</div>
                                    <div className="text-xs mt-2 text-slate-300">
                                        {(row?.source_impact?.warnings || []).length > 0 ? (
                                            <ul className="space-y-1">
                                                {(row.source_impact.warnings || []).map((w: string, wi: number) => (
                                                    <li key={wi}>- {w}</li>
                                                ))}
                                            </ul>
                                        ) : (
                                            <div className="flex items-center gap-1 text-emerald-300"><CheckCircle2 className="size-3" />No critical delay detected.</div>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                    <div className="mt-4 text-xs text-amber-200 flex items-start gap-2">
                        <AlertTriangle className="size-4 mt-0.5" />
                        <span>
                            Verifier la latence des donnees est critique: des retards API peuvent baisser la confiance, voire neutraliser la decision pour proteger le systeme.
                        </span>
                    </div>
                </section>
            </div>
        </div>
    );
}
