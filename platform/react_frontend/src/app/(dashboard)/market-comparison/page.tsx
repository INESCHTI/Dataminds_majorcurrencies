"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";
import styles from "./page.module.css";

interface MarketComparisonSymbol {
    symbol: string;
    timeframe: string;
    events: number;
    avg_confidence: number;
    fallback_rate: number;
    avg_latency_ms: number;
    disagreement_rate: number;
    alert_level: string;
    top_signal: string;
    top_model: string;
    top_risk_flag: string;
    stability_score: number | null;
}

interface MarketComparisonMarket {
    coverage_symbols: number;
    avg_stability_score: number;
    avg_confidence: number;
    avg_disagreement: number;
    avg_fallback_rate: number;
}

interface MarketComparisonResponse {
    generated_at: string;
    market: MarketComparisonMarket;
    symbols: MarketComparisonSymbol[];
    ranking: MarketComparisonSymbol[];
}

const EMPTY_MARKET: MarketComparisonMarket = {
    coverage_symbols: 0,
    avg_stability_score: 0,
    avg_confidence: 0,
    avg_disagreement: 0,
    avg_fallback_rate: 0,
};

function resolveBackendApiBase(): string {
    const configured = (process.env.NEXT_PUBLIC_API_URL || "").trim();
    if (!configured) {
        return "http://127.0.0.1:8000/api";
    }
    if (configured.startsWith("/")) {
        return configured;
    }
    if (configured.endsWith("/api") || configured.endsWith("/api/")) {
        return configured.replace(/\/$/, "");
    }
    return `${configured.replace(/\/$/, "")}/api`;
}

const BACKEND_API_BASE = resolveBackendApiBase();

function toNumber(value: unknown): number {
    const n = Number(value ?? 0);
    return Number.isFinite(n) ? n : 0;
}

function pct(value: unknown, digits = 2): string {
    return `${(toNumber(value) * 100).toFixed(digits)}%`;
}

function levelClass(level: string): string {
    const normalized = String(level || "na").toLowerCase();
    if (normalized === "normal") return styles.ok;
    if (normalized === "warning") return styles.warn;
    if (normalized === "critical") return styles.critical;
    return styles.na;
}

export default function MarketComparisonPage() {
    const [timeframe, setTimeframe] = useState("1H");
    const [model, setModel] = useState("");
    const [trendHorizon, setTrendHorizon] = useState("medium");
    const [windowSize, setWindowSize] = useState("200");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [payload, setPayload] = useState<MarketComparisonResponse | null>(null);

    const refresh = useCallback(async () => {
        const params = new URLSearchParams({
            timeframe,
            trend_horizon: trendHorizon,
            window: windowSize,
        });
        if (model) {
            params.set("model", model);
        }

        setLoading(true);
        setError(null);

        try {
            const response = await fetch(`${BACKEND_API_BASE}/market/comparison?${params.toString()}`, {
                cache: "no-store",
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = (await response.json()) as MarketComparisonResponse;
            setPayload(data);
        } catch (fetchError) {
            const message = fetchError instanceof Error ? fetchError.message : "Unknown API error";
            setError(`Unable to load comparison data: ${message}`);
        } finally {
            setLoading(false);
        }
    }, [timeframe, model, trendHorizon, windowSize]);

    useEffect(() => {
        void refresh();
    }, [refresh]);

    useEffect(() => {
        const id = window.setInterval(() => {
            void refresh();
        }, 30000);

        return () => window.clearInterval(id);
    }, [refresh]);

    const symbols = useMemo(() => (Array.isArray(payload?.symbols) ? payload?.symbols : []), [payload]);
    const rankingRows = useMemo(() => {
        if (Array.isArray(payload?.ranking) && payload.ranking.length > 0) {
            return payload.ranking;
        }
        return symbols;
    }, [payload, symbols]);
    const market = payload?.market ?? EMPTY_MARKET;

    const activeSymbols = useMemo(() => symbols.filter((item) => toNumber(item.events) > 0), [symbols]);

    const insight = useMemo(() => {
        if (activeSymbols.length === 0) {
            return {
                alignment: "no_data",
                buys: 0,
                sells: 0,
                bestSymbol: "N/A",
                bestStability: "N/A",
                highRiskCount: 0,
            };
        }

        const aligned = activeSymbols
            .map((item) => String(item.top_signal || "").toUpperCase())
            .filter((signal) => signal === "BUY" || signal === "SELL");

        const buys = aligned.filter((signal) => signal === "BUY").length;
        const sells = aligned.filter((signal) => signal === "SELL").length;
        let alignment = "mixed";

        if (aligned.length > 0) {
            const ratio = Math.max(buys, sells) / aligned.length;
            if (ratio >= 0.75) {
                alignment = "strong";
            } else if (ratio >= 0.55) {
                alignment = "moderate";
            }
        }

        const highRiskCount = activeSymbols.filter(
            (item) => toNumber(item.disagreement_rate) >= 0.2 || toNumber(item.fallback_rate) >= 0.15
        ).length;

        const rankedByStability = [...activeSymbols].sort(
            (a, b) => toNumber(b.stability_score) - toNumber(a.stability_score)
        );

        const best = rankedByStability[0];

        return {
            alignment,
            buys,
            sells,
            bestSymbol: best?.symbol || "N/A",
            bestStability: best?.stability_score == null ? "N/A" : pct(best.stability_score, 1),
            highRiskCount,
        };
    }, [activeSymbols]);

    return (
        <div className={styles.pageShell}>
            <header className="flex h-14 shrink-0 items-center gap-2 border-b px-6">
                <SidebarTrigger className="-ml-1" />
                <Separator orientation="vertical" className="mr-2 h-4" />
                <h1 className="text-lg font-semibold">Market Comparison</h1>
            </header>

            <main className={styles.page}>
                <section className={styles.pageHd}>
                    <h2>Market Comparison</h2>
                    <p>
                        Single-screen market view to compare all symbols on the same timeframe: stability,
                        confidence, disagreement, fallback pressure, and dominant signal. This page is
                        optimized to show the whole picture before action.
                    </p>
                </section>

                <section className={styles.controlRow}>
                    <div className={styles.ctrl}>
                        <label htmlFor="tfSelect">Timeframe</label>
                        <select id="tfSelect" value={timeframe} onChange={(e) => setTimeframe(e.target.value)}>
                            <option value="1H">1H</option>
                            <option value="4H">4H</option>
                            <option value="1D">1D</option>
                        </select>
                    </div>

                    <div className={styles.ctrl}>
                        <label htmlFor="modelSelect">Model</label>
                        <select id="modelSelect" value={model} onChange={(e) => setModel(e.target.value)}>
                            <option value="">all</option>
                            <option value="random_forest">random_forest</option>
                            <option value="logistic_regression">logistic_regression</option>
                        </select>
                    </div>

                    <div className={styles.ctrl}>
                        <label htmlFor="horizonSelect">Trend Horizon</label>
                        <select
                            id="horizonSelect"
                            value={trendHorizon}
                            onChange={(e) => setTrendHorizon(e.target.value)}
                        >
                            <option value="short">short</option>
                            <option value="medium">medium</option>
                            <option value="long">long</option>
                        </select>
                    </div>

                    <div className={styles.ctrl}>
                        <label htmlFor="windowSelect">Window</label>
                        <select id="windowSelect" value={windowSize} onChange={(e) => setWindowSize(e.target.value)}>
                            <option value="100">100</option>
                            <option value="200">200</option>
                            <option value="500">500</option>
                            <option value="1000">1000</option>
                        </select>
                    </div>

                    <div className={styles.ctrl}>
                        <label>Actions</label>
                        <button type="button" onClick={() => void refresh()} disabled={loading}>
                            {loading ? "Refreshing..." : "Refresh"}
                        </button>
                    </div>
                </section>

                <section className={styles.kpiGrid}>
                    <article className={styles.kpi}>
                        <div className={styles.k}>Coverage</div>
                        <div className={styles.v}>{market.coverage_symbols}</div>
                        <div className={styles.sub}>symbols with events</div>
                    </article>
                    <article className={styles.kpi}>
                        <div className={styles.k}>Avg Stability</div>
                        <div className={styles.v}>{pct(market.avg_stability_score, 1)}</div>
                        <div className={styles.sub}>composite score</div>
                    </article>
                    <article className={styles.kpi}>
                        <div className={styles.k}>Avg Confidence</div>
                        <div className={styles.v}>{pct(market.avg_confidence, 2)}</div>
                        <div className={styles.sub}>all active symbols</div>
                    </article>
                    <article className={styles.kpi}>
                        <div className={styles.k}>Avg Disagreement</div>
                        <div className={styles.v}>{pct(market.avg_disagreement, 2)}</div>
                        <div className={styles.sub}>model mismatch rate</div>
                    </article>
                    <article className={styles.kpi}>
                        <div className={styles.k}>Avg Fallback</div>
                        <div className={styles.v}>{pct(market.avg_fallback_rate, 2)}</div>
                        <div className={styles.sub}>fallback pressure</div>
                    </article>
                </section>

                <section className={styles.grid}>
                    <div>
                        <article className={styles.card}>
                            <div className={styles.cardHd}>Relative Stability Ranking</div>
                            <div className={styles.cardBd}>
                                <div className={styles.metaNote}>
                                    How to read: higher bar means more stable decision environment (lower
                                    disagreement/fallback/conflict).
                                </div>

                                {rankingRows.length === 0 ? (
                                    <div className={styles.metaNote}>No comparison data for this filter yet.</div>
                                ) : (
                                    <div className={styles.scoreBars}>
                                        {rankingRows.map((row) => {
                                            const rawStability = row.stability_score;
                                            const hasScore = typeof rawStability === "number";
                                            const bounded = Math.max(0, Math.min(1, toNumber(rawStability)));

                                            return (
                                                <div className={styles.barRow} key={`${row.symbol}-${row.timeframe}`}>
                                                    <div className={styles.name}>{row.symbol}</div>
                                                    <div className={styles.track}>
                                                        <div
                                                            className={styles.fill}
                                                            style={{ width: `${(bounded * 100).toFixed(1)}%` }}
                                                        />
                                                    </div>
                                                    <div className={styles.val}>
                                                        {hasScore ? pct(bounded, 1) : "N/A"}
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                )}
                            </div>
                        </article>

                        <article className={styles.card}>
                            <div className={styles.cardHd}>Cross-Symbol Snapshot Table</div>
                            <div className={styles.cardBd}>
                                <div className={styles.tableWrap}>
                                    <table>
                                        <thead>
                                            <tr>
                                                <th>Symbol</th>
                                                <th>Signal</th>
                                                <th>Confidence</th>
                                                <th>Drift</th>
                                                <th>Fallback</th>
                                                <th>Latency</th>
                                                <th>Alert</th>
                                                <th>Risk</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {symbols.length === 0 ? (
                                                <tr>
                                                    <td colSpan={8}>No data</td>
                                                </tr>
                                            ) : (
                                                symbols.map((row) => {
                                                    const hasEvents = toNumber(row.events) > 0;
                                                    return (
                                                        <tr key={`${row.symbol}-${row.timeframe}-table`}>
                                                            <td>{row.symbol}</td>
                                                            <td>{String(row.top_signal || "N/A").toUpperCase()}</td>
                                                            <td>{hasEvents ? pct(row.avg_confidence, 2) : "N/A"}</td>
                                                            <td>{hasEvents ? pct(row.disagreement_rate, 2) : "N/A"}</td>
                                                            <td>{hasEvents ? pct(row.fallback_rate, 2) : "N/A"}</td>
                                                            <td>
                                                                {hasEvents
                                                                    ? `${toNumber(row.avg_latency_ms).toFixed(1)} ms`
                                                                    : "N/A"}
                                                            </td>
                                                            <td>
                                                                <span
                                                                    className={`${styles.chip} ${levelClass(
                                                                        row.alert_level
                                                                    )}`}
                                                                >
                                                                    {String(row.alert_level || "no_data").toUpperCase()}
                                                                </span>
                                                            </td>
                                                            <td>{row.top_risk_flag || "none"}</td>
                                                        </tr>
                                                    );
                                                })
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </article>
                    </div>

                    <div>
                        <article className={styles.card}>
                            <div className={styles.cardHd}>Signal Alignment Matrix</div>
                            <div className={styles.cardBd}>
                                <div className={styles.metaNote}>
                                    How to read: if most symbols show same direction, alignment is high. Mixed
                                    directions indicate cross-market divergence.
                                </div>

                                {activeSymbols.length === 0 ? (
                                    <div className={styles.metaNote}>No decisions yet.</div>
                                ) : (
                                    <div className={styles.matrix}>
                                        {activeSymbols.map((row) => (
                                            <div className={styles.matrixItem} key={`${row.symbol}-${row.timeframe}-matrix`}>
                                                <div className={styles.s}>
                                                    {row.symbol} · {row.timeframe}
                                                </div>
                                                <div className={styles.sig}>
                                                    {String(row.top_signal || "N/A").toUpperCase()}
                                                </div>
                                                <div className={styles.meta}>
                                                    conf {pct(row.avg_confidence, 1)} · model {row.top_model || "unknown"}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </article>

                        <article className={styles.card}>
                            <div className={styles.cardHd}>Quick Interpretation</div>
                            <div className={styles.cardBd}>
                                <div className={styles.metaNote}>
                                    {error ? (
                                        error
                                    ) : (
                                        <>
                                            Market alignment: <strong>{insight.alignment}</strong> ({insight.buys} BUY /
                                            {" "}
                                            {insight.sells} SELL).<br />
                                            Average market stability: <strong>{pct(market.avg_stability_score, 1)}</strong>.
                                            <br />
                                            Highest current stability: <strong>{insight.bestSymbol}</strong> at
                                            {" "}
                                            {insight.bestStability}.<br />
                                            Elevated-risk symbols: <strong>{insight.highRiskCount}</strong>.
                                        </>
                                    )}
                                </div>
                            </div>
                        </article>
                    </div>
                </section>
            </main>
        </div>
    );
}
