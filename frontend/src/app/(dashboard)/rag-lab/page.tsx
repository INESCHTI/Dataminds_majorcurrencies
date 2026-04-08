"use client";

import { useMemo, useState } from "react";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Bot, FlaskConical, Loader2, MessageSquare, Search, Sparkles } from "lucide-react";

const STRATEGIES = ["tfidf", "bm25", "hybrid", "semantic"] as const;
type Strategy = (typeof STRATEGIES)[number];

type ChatContext = {
    doc_id: string;
    title: string;
    symbol: string;
    score: number;
};

type ChatPayload = {
    success?: boolean;
    strategy?: string;
    documents_indexed?: number;
    execution_time_ms?: number;
    result?: {
        answer?: string;
        contexts?: ChatContext[];
    };
    error?: string;
};

type RetrievalMetric = {
    avg_top1_score: number;
    top3_symbol_hit_rate: number;
};

type SentimentSummary = {
    avg_positive: number;
    avg_negative: number;
    avg_compound: number;
    size: number;
};

type ClusterMethod = {
    metrics: {
        silhouette: number;
        davies_bouldin: number;
    };
    topic_terms: Record<string, string[]>;
    sentiment_summary: Record<string, SentimentSummary>;
};

type BenchmarkPayload = {
    success?: boolean;
    documents?: number;
    execution_time_ms?: number;
    retrieval_experiments?: Record<string, RetrievalMetric>;
    clustering_experiments?: Record<string, ClusterMethod>;
    error?: string;
};

function pct(value: number): string {
    return `${Math.round(value * 100)}%`;
}

export default function RagLabPage() {
    const [question, setQuestion] = useState("Pourquoi USDJPY est en vente ?");
    const [strategy, setStrategy] = useState<Strategy>("semantic");
    const [topK, setTopK] = useState(4);

    const [chatLoading, setChatLoading] = useState(false);
    const [chatResult, setChatResult] = useState<ChatPayload | null>(null);
    const [compareLoading, setCompareLoading] = useState(false);
    const [compareResults, setCompareResults] = useState<Record<string, ChatPayload>>({});

    const [benchLoading, setBenchLoading] = useState(false);
    const [benchResult, setBenchResult] = useState<BenchmarkPayload | null>(null);

    const chatError = useMemo(() => chatResult?.error ?? null, [chatResult]);
    const benchError = useMemo(() => benchResult?.error ?? null, [benchResult]);

    async function runChat() {
        setChatLoading(true);
        setChatResult(null);
        setCompareResults({});
        try {
            const res = await fetch("/api/v2/rag/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    question,
                    strategy,
                    top_k: topK,
                    max_docs: 500,
                }),
            });
            const payload = (await res.json()) as ChatPayload;
            setChatResult(payload);
        } catch {
            setChatResult({ error: "rag_chat_request_failed" });
        } finally {
            setChatLoading(false);
        }
    }

    async function runCompareAll() {
        setCompareLoading(true);
        setChatResult(null);
        setCompareResults({});

        try {
            const calls = STRATEGIES.map(async (s) => {
                try {
                    const res = await fetch("/api/v2/rag/chat", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            question,
                            strategy: s,
                            top_k: topK,
                            max_docs: 500,
                        }),
                    });
                    const payload = (await res.json()) as ChatPayload;
                    return [s, payload] as const;
                } catch {
                    return [s, { error: "rag_chat_request_failed" } as ChatPayload] as const;
                }
            });

            const entries = await Promise.all(calls);
            const next: Record<string, ChatPayload> = {};
            for (const [s, payload] of entries) {
                next[s] = payload;
            }
            setCompareResults(next);
        } finally {
            setCompareLoading(false);
        }
    }

    async function runBenchmark() {
        setBenchLoading(true);
        setBenchResult(null);
        try {
            const res = await fetch("/api/v2/rag/benchmark?clusters=4&max_docs=300", { cache: "no-store" });
            const payload = (await res.json()) as BenchmarkPayload;
            setBenchResult(payload);
        } catch {
            setBenchResult({ error: "rag_benchmark_request_failed" });
        } finally {
            setBenchLoading(false);
        }
    }

    return (
        <div className="flex h-full flex-col bg-[#090f1a] text-slate-100">
            <header className="flex h-14 shrink-0 items-center gap-3 border-b border-slate-800 bg-[#0f1726] px-6">
                <SidebarTrigger className="-ml-1" />
                <Separator orientation="vertical" className="h-5" />
                <FlaskConical className="size-4 text-cyan-400" />
                <h1 className="text-sm font-semibold tracking-wide">RAG Lab</h1>
                <Badge variant="outline" className="border-slate-700 text-xs">Frontend-only</Badge>
            </header>

            <div className="flex-1 overflow-auto p-6 space-y-6">
                <Card className="border-slate-800 bg-[#121b2d]">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-sm">
                            <MessageSquare className="size-4 text-cyan-400" />
                            Chat RAG
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        <div className="grid grid-cols-1 lg:grid-cols-12 gap-3">
                            <div className="lg:col-span-7">
                                <label className="text-xs text-slate-400">Question</label>
                                <input
                                    value={question}
                                    onChange={(e) => setQuestion(e.target.value)}
                                    className="mt-1 w-full rounded border border-slate-700 bg-[#0d1422] px-3 py-2 text-sm outline-none focus:border-cyan-500"
                                    placeholder="Pose ta question sur EURUSD, macro, sentiment..."
                                />
                            </div>
                            <div className="lg:col-span-2">
                                <label className="text-xs text-slate-400">Strategie</label>
                                <select
                                    value={strategy}
                                    onChange={(e) => setStrategy(e.target.value as Strategy)}
                                    className="mt-1 w-full rounded border border-slate-700 bg-[#0d1422] px-3 py-2 text-sm outline-none focus:border-cyan-500"
                                >
                                    {STRATEGIES.map((s) => (
                                        <option key={s} value={s}>{s}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="lg:col-span-1">
                                <label className="text-xs text-slate-400">Top K</label>
                                <input
                                    type="number"
                                    value={topK}
                                    min={1}
                                    max={10}
                                    onChange={(e) => setTopK(Math.max(1, Math.min(10, Number(e.target.value) || 4)))}
                                    className="mt-1 w-full rounded border border-slate-700 bg-[#0d1422] px-3 py-2 text-sm outline-none focus:border-cyan-500"
                                />
                            </div>
                            <div className="lg:col-span-2 flex items-end">
                                <Button onClick={runChat} disabled={chatLoading || compareLoading || !question.trim()} className="w-full bg-cyan-700 hover:bg-cyan-600">
                                    {chatLoading ? <Loader2 className="size-4 animate-spin" /> : <Search className="size-4 mr-1" />} Interroger
                                </Button>
                            </div>
                        </div>

                        <div className="flex justify-end">
                            <Button onClick={runCompareAll} disabled={chatLoading || compareLoading || !question.trim()} variant="outline" className="border-slate-600 bg-[#0d1422] text-slate-200 hover:bg-slate-800">
                                {compareLoading ? <Loader2 className="size-4 animate-spin" /> : <Sparkles className="size-4 mr-1" />} Comparer les 4 strategies
                            </Button>
                        </div>

                        {chatError && (
                            <div className="rounded border border-rose-700 bg-rose-900/20 px-3 py-2 text-sm text-rose-300">
                                Erreur chat: {chatError}
                            </div>
                        )}

                        {chatResult?.result && (
                            <div className="space-y-3">
                                <div className="rounded border border-slate-700 bg-[#0d1422] p-3">
                                    <div className="flex items-center gap-2 text-xs text-slate-400 mb-2">
                                        <Bot className="size-3.5" />
                                        <span>strategie={chatResult.strategy}</span>
                                        <span>docs={chatResult.documents_indexed ?? 0}</span>
                                        <span>latence={chatResult.execution_time_ms ?? 0} ms</span>
                                    </div>
                                    <p className="text-sm text-slate-100 leading-relaxed">{chatResult.result.answer}</p>
                                </div>

                                <div className="rounded border border-slate-700 bg-[#0d1422] p-3">
                                    <p className="text-xs text-slate-400 mb-2">Contexte retenu</p>
                                    <div className="grid gap-2">
                                        {(chatResult.result.contexts || []).map((c) => (
                                            <div key={c.doc_id} className="rounded border border-slate-800 bg-[#0a101b] px-2 py-2 text-xs">
                                                <div className="flex items-center gap-2">
                                                    <span className="font-mono text-cyan-300">{c.doc_id}</span>
                                                    <Badge variant="outline" className="border-slate-700 text-[10px]">{c.symbol}</Badge>
                                                    <span className="ml-auto text-slate-400">score={c.score}</span>
                                                </div>
                                                <div className="text-slate-300 mt-1">{c.title}</div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}

                        {Object.keys(compareResults).length > 0 && (
                            <div className="space-y-2">
                                <p className="text-xs text-slate-400">Comparaison cote a cote (meme question)</p>
                                <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
                                    {STRATEGIES.map((s) => {
                                        const payload = compareResults[s];
                                        const error = payload?.error;
                                        return (
                                            <div key={s} className="rounded border border-slate-700 bg-[#0d1422] p-3">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <Badge variant="outline" className="border-slate-700 text-[10px] uppercase">{s}</Badge>
                                                    <span className="text-xs text-slate-400">latence={payload?.execution_time_ms ?? 0} ms</span>
                                                    <span className="text-xs text-slate-400">docs={payload?.documents_indexed ?? 0}</span>
                                                </div>
                                                {error ? (
                                                    <p className="text-xs text-rose-300">Erreur: {error}</p>
                                                ) : (
                                                    <>
                                                        <p className="text-sm text-slate-100 leading-relaxed">{payload?.result?.answer || "Aucune reponse"}</p>
                                                        <div className="mt-2 space-y-1">
                                                            {(payload?.result?.contexts || []).slice(0, 2).map((c) => (
                                                                <div key={`${s}-${c.doc_id}`} className="text-xs rounded border border-slate-800 px-2 py-1 text-slate-300">
                                                                    <span className="text-cyan-300 font-mono">{c.doc_id}</span>
                                                                    <span className="ml-2">{c.symbol}</span>
                                                                    <span className="ml-2 text-slate-400">score={c.score}</span>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </>
                                                )}
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        )}
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-[#121b2d]">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-sm">
                            <Sparkles className="size-4 text-amber-400" />
                            Comparatif Multi-Approches
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        <div className="flex justify-end">
                            <Button onClick={runBenchmark} disabled={benchLoading} className="bg-amber-700 hover:bg-amber-600">
                                {benchLoading ? <Loader2 className="size-4 animate-spin" /> : <FlaskConical className="size-4 mr-1" />} Lancer benchmark
                            </Button>
                        </div>

                        {benchError && (
                            <div className="rounded border border-rose-700 bg-rose-900/20 px-3 py-2 text-sm text-rose-300">
                                Erreur benchmark: {benchError}
                            </div>
                        )}

                        {benchResult?.retrieval_experiments && (
                            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
                                {Object.entries(benchResult.retrieval_experiments).map(([name, v]) => (
                                    <div key={name} className="rounded border border-slate-700 bg-[#0d1422] p-3">
                                        <div className="flex items-center justify-between">
                                            <p className="text-sm font-semibold text-slate-100 uppercase">{name}</p>
                                            <Badge variant="outline" className="border-slate-700 text-[10px]">retrieval</Badge>
                                        </div>
                                        <p className="mt-2 text-xs text-slate-400">avg_top1_score</p>
                                        <p className="text-lg font-bold text-cyan-300">{v.avg_top1_score.toFixed(4)}</p>
                                        <p className="mt-2 text-xs text-slate-400">top3_symbol_hit_rate</p>
                                        <p className="text-sm font-semibold text-emerald-300">{pct(v.top3_symbol_hit_rate)}</p>
                                    </div>
                                ))}
                            </div>
                        )}

                        {benchResult?.clustering_experiments && (
                            <div className="grid grid-cols-1 xl:grid-cols-3 gap-3">
                                {Object.entries(benchResult.clustering_experiments).map(([name, method]) => (
                                    <div key={name} className="rounded border border-slate-700 bg-[#0d1422] p-3 space-y-3">
                                        <div className="flex items-center justify-between">
                                            <p className="text-sm font-semibold text-slate-100">{name}</p>
                                            <Badge variant="outline" className="border-slate-700 text-[10px]">clustering</Badge>
                                        </div>

                                        <div className="grid grid-cols-2 gap-2 text-xs">
                                            <div className="rounded border border-slate-800 px-2 py-1">
                                                <p className="text-slate-400">silhouette</p>
                                                <p className="text-cyan-300 font-mono">{method.metrics.silhouette.toFixed(4)}</p>
                                            </div>
                                            <div className="rounded border border-slate-800 px-2 py-1">
                                                <p className="text-slate-400">davies_bouldin</p>
                                                <p className="text-amber-300 font-mono">{method.metrics.davies_bouldin.toFixed(4)}</p>
                                            </div>
                                        </div>

                                        <div>
                                            <p className="text-xs text-slate-400 mb-1">Topics par cluster</p>
                                            <div className="space-y-1">
                                                {Object.entries(method.topic_terms).slice(0, 3).map(([k, terms]) => (
                                                    <p key={k} className="text-xs text-slate-200">
                                                        <span className="text-slate-400">cluster {k}:</span> {terms.slice(0, 5).join(", ")}
                                                    </p>
                                                ))}
                                            </div>
                                        </div>

                                        <div>
                                            <p className="text-xs text-slate-400 mb-1">Sentiment moyen</p>
                                            <div className="space-y-1 text-xs">
                                                {Object.entries(method.sentiment_summary).slice(0, 3).map(([k, s]) => (
                                                    <div key={k} className="rounded border border-slate-800 px-2 py-1">
                                                        <span className="text-slate-400">cluster {k}</span>
                                                        <span className="ml-2 text-emerald-300">pos={s.avg_positive.toFixed(3)}</span>
                                                        <span className="ml-2 text-rose-300">neg={s.avg_negative.toFixed(3)}</span>
                                                        <span className="ml-2 text-cyan-300">cmp={s.avg_compound.toFixed(3)}</span>
                                                        <span className="ml-2 text-slate-400">n={s.size}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
