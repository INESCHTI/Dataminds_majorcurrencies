"use client";

import { useEffect, useState } from "react";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import { Database, FileCode2 } from "lucide-react";

export default function DebugDataPage() {
    const [data, setData] = useState<any | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const load = async () => {
            try {
                const res = await fetch("/api/v2/debug/data_sources", { cache: "no-store" });
                if (!res.ok) throw new Error("debug api failed");
                setData(await res.json());
            } catch {
                setData(null);
            } finally {
                setLoading(false);
            }
        };
        load();
    }, []);

    return (
        <div className="flex flex-col h-full bg-[#080d18] text-slate-100">
            <header className="flex h-14 shrink-0 items-center gap-3 border-b border-white/5 bg-black/30 backdrop-blur-xl px-6">
                <SidebarTrigger className="-ml-1 text-slate-400" />
                <Separator orientation="vertical" className="h-5 bg-white/10" />
                <Database className="size-4 text-cyan-400" />
                <h1 className="text-sm font-bold text-white">Debug Data Sources</h1>
                <span className="text-[10px] font-mono text-slate-500 border border-slate-700 rounded px-1.5 py-0.5">frontend-only</span>
            </header>

            <div className="flex-1 overflow-auto p-6 space-y-4">
                {loading && <div className="text-sm text-slate-400">Loading debug snapshot...</div>}
                {!loading && !data && <div className="text-sm text-rose-400">No debug data available.</div>}

                {data && (
                    <>
                        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                            <div className="text-xs text-slate-400 mb-2">Signals directory</div>
                            <div className="font-mono text-sm text-cyan-300 break-all">{data?.sources?.signals_directory}</div>
                        </div>

                        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                            <div className="flex items-center gap-2 mb-3 text-sm font-semibold">
                                <FileCode2 className="size-4 text-indigo-400" />
                                Latest Signals Matrix
                            </div>
                            <pre className="text-xs text-slate-300 overflow-auto">{JSON.stringify(data?.latest_signals, null, 2)}</pre>
                        </div>

                        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                            <div className="text-sm font-semibold mb-3">Real Trade Metrics</div>
                            <pre className="text-xs text-slate-300 overflow-auto">{JSON.stringify(data?.trade_metrics, null, 2)}</pre>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
