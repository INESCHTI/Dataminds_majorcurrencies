"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";
import styles from "./page.module.css";

type Dict = Record<string, unknown>;

interface ReportingOverview {
    performance?: Dict;
    agents?: Dict;
    status?: Dict;
    recent_alerts?: Dict[];
    news_preview?: Dict[];
}

interface ReportingHistory {
    items?: Dict[];
    count?: number;
    raw_count?: number;
    compress?: boolean;
}

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

function fmtPct(value: unknown, digits = 2): string {
    return `${(toNumber(value) * 100).toFixed(digits)}%`;
}

function fmtNum(value: unknown, digits = 2): string {
    return toNumber(value).toFixed(digits);
}

function fmtDate(value: unknown): string {
    if (!value) return "N/A";
    const dt = new Date(String(value));
    if (Number.isNaN(dt.getTime())) return String(value);
    return dt.toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
    });
}

function alertClass(level: unknown): string {
    const normalized = String(level || "na").toLowerCase();
    if (normalized === "critical") return styles.critical;
    if (normalized === "warning") return styles.warn;
    if (normalized === "normal") return styles.ok;
    return styles.na;
}

function getObject(value: unknown): Dict {
    return value && typeof value === "object" ? (value as Dict) : {};
}

export default function ReportsPage() {
    const [symbol, setSymbol] = useState("EURUSD");
    const [timeframe, setTimeframe] = useState("1H");
    const [model, setModel] = useState("");
    const [trendHorizon, setTrendHorizon] = useState("medium");
    const [windowSize, setWindowSize] = useState("200");
    const [historyMode, setHistoryMode] = useState("compressed");
    const [overview, setOverview] = useState<ReportingOverview>({});
    const [history, setHistory] = useState<ReportingHistory>({ items: [], count: 0, raw_count: 0, compress: true });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [hoverTip, setHoverTip] = useState<{ visible: boolean; text: string; x: number; y: number }>({
        visible: false,
        text: "",
        x: 0,
        y: 0,
    });

    const trendCanvasRef = useRef<HTMLCanvasElement | null>(null);

    const performance = getObject(overview.performance);
    const drift = getObject(performance.drift);
    const alert = getObject(drift.alert);
    const historyItems = Array.isArray(history.items) ? history.items : [];
    const historyCount = toNumber(history.count);
    const historyRawCount = toNumber(history.raw_count || historyCount);

    const kpiHelpText = useMemo(() => {
        const fallbackRate = toNumber(performance.fallback_rate);
        const latencyMs = toNumber(performance.avg_latency_ms);
        const conf = toNumber(performance.avg_confidence);
        const dis = toNumber(drift.disagreement_rate);
        const level = String(alert.level || "no_data").toUpperCase();

        return {
            kpiFallbackTip: `Fallback Rate: share of decisions that did not use model output. Current ${fmtPct(fallbackRate, 2)}. Low is usually healthy.`,
            kpiLatencyTip: `Avg Latency: mean time to generate one decision. Current ${latencyMs.toFixed(1)} ms. Spikes can indicate data/model slowdown.`,
            kpiConfidenceTip: `Avg Confidence: average confidence score of final decisions. Current ${fmtPct(conf, 2)}. Interpret with disagreement and fallback together.`,
            kpiDriftTip: `Disagreement: how often main and shadow models disagree. Current ${fmtPct(dis, 2)}. Near 0% can be normal in stable markets.`,
            kpiAlertTip: `Alert level is derived from disagreement thresholds. Current ${level}. NORMAL means disagreement stays below warning threshold.`,
            kpiHistoryTip:
                "History Rows is the number of displayed rows in selected mode. State changes merge repeated identical decisions.",
        };
    }, [performance, drift, alert]);

    const fetchOverview = useCallback(async (): Promise<ReportingOverview> => {
        const params = new URLSearchParams({
            symbol,
            timeframe,
            window: windowSize,
            trend_horizon: trendHorizon,
        });
        if (model) {
            params.set("model", model);
        }

        const response = await fetch(`${BACKEND_API_BASE}/reporting/overview?${params.toString()}`, {
            cache: "no-store",
        });
        if (!response.ok) {
            throw new Error(`Overview API HTTP ${response.status}`);
        }
        return (await response.json()) as ReportingOverview;
    }, [symbol, timeframe, windowSize, trendHorizon, model]);

    const fetchHistory = useCallback(async (): Promise<ReportingHistory> => {
        const compress = historyMode !== "raw";
        const params = new URLSearchParams({
            symbol,
            timeframe,
            limit: "500",
            compress: String(compress),
        });
        if (model) {
            params.set("model", model);
        }

        const response = await fetch(`${BACKEND_API_BASE}/reporting/history?${params.toString()}`, {
            cache: "no-store",
        });
        if (!response.ok) {
            throw new Error(`History API HTTP ${response.status}`);
        }
        return (await response.json()) as ReportingHistory;
    }, [symbol, timeframe, historyMode, model]);

    const refreshDashboard = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [nextOverview, nextHistory] = await Promise.all([fetchOverview(), fetchHistory()]);
            setOverview(nextOverview);
            setHistory(nextHistory);
        } catch (refreshError) {
            const message = refreshError instanceof Error ? refreshError.message : String(refreshError);
            setError(`Error: ${message}`);
        } finally {
            setLoading(false);
        }
    }, [fetchOverview, fetchHistory]);

    useEffect(() => {
        void refreshDashboard();
    }, [refreshDashboard]);

    useEffect(() => {
        const id = window.setInterval(() => {
            void refreshDashboard();
        }, 30000);
        return () => window.clearInterval(id);
    }, [refreshDashboard]);

    useEffect(() => {
        const canvas = trendCanvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        const trend = getObject(performance.drift).trend;
        const points = Array.isArray(trend) ? trend : [];
        const w = canvas.width;
        const h = canvas.height;
        const pad = 18;
        ctx.clearRect(0, 0, w, h);

        if (points.length < 2) {
            ctx.fillStyle = "rgba(255,255,255,0.55)";
            ctx.font = "12px system-ui";
            ctx.fillText("Not enough trend points yet.", pad, h / 2);
            return;
        }

        const a = points.map((p) => toNumber(getObject(p).disagreement_rate));
        const b = points.map((p) => toNumber(getObject(p).avg_confidence_delta));
        const aMin = Math.min(...a);
        const aMax = Math.max(...a);
        const bMin = Math.min(...b);
        const bMax = Math.max(...b);
        const aRange = Math.max(0.0001, aMax - aMin);
        const bRange = Math.max(0.0001, bMax - bMin);

        ctx.strokeStyle = "rgba(255,255,255,0.2)";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(pad, h - pad);
        ctx.lineTo(w - pad, h - pad);
        ctx.moveTo(pad, pad);
        ctx.lineTo(pad, h - pad);
        ctx.stroke();

        const step = (w - pad * 2) / (a.length - 1);

        ctx.strokeStyle = "#ff8a3d";
        ctx.lineWidth = 2;
        ctx.beginPath();
        a.forEach((v, i) => {
            const x = pad + i * step;
            const y = h - pad - ((v - aMin) / aRange) * (h - pad * 2);
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });
        ctx.stroke();

        ctx.strokeStyle = "#4dd0ff";
        ctx.lineWidth = 1.7;
        ctx.beginPath();
        b.forEach((v, i) => {
            const x = pad + i * step;
            const y = h - pad - ((v - bMin) / bRange) * (h - pad * 2);
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });
        ctx.stroke();

        ctx.fillStyle = "#ff8a3d";
        ctx.fillRect(w - 220, 10, 10, 2);
        ctx.fillStyle = "rgba(255,255,255,0.72)";
        ctx.font = "11px system-ui";
        ctx.fillText("Disagreement rate", w - 206, 13);

        ctx.fillStyle = "#4dd0ff";
        ctx.fillRect(w - 110, 10, 10, 2);
        ctx.fillStyle = "rgba(255,255,255,0.72)";
        ctx.fillText("Conf delta", w - 96, 13);

        ctx.fillStyle = "rgba(255,255,255,0.58)";
        ctx.font = "10px system-ui";
        ctx.fillText(`drift ${fmtPct(aMin, 1)} to ${fmtPct(aMax, 1)}`, pad + 4, 14);
        ctx.fillText(`delta ${fmtPct(bMin, 1)} to ${fmtPct(bMax, 1)}`, pad + 4, 27);
    }, [performance]);

    const showTip = (key: keyof typeof kpiHelpText, event: React.MouseEvent) => {
        const x = Math.min(window.innerWidth - 340, event.clientX + 14);
        const y = Math.min(window.innerHeight - 120, event.clientY + 14);
        setHoverTip({ visible: true, text: kpiHelpText[key], x, y });
    };

    const moveTip = (event: React.MouseEvent) => {
        setHoverTip((current) => {
            if (!current.visible) return current;
            const x = Math.min(window.innerWidth - 340, event.clientX + 14);
            const y = Math.min(window.innerHeight - 120, event.clientY + 14);
            return { ...current, x, y };
        });
    };

    const hideTip = () => {
        setHoverTip((current) => ({ ...current, visible: false }));
    };

    const exportCsv = () => {
        if (!historyItems.length) return;

        const header = [
            "start_timestamp",
            "last_timestamp",
            "symbol",
            "timeframe",
            "final_signal",
            "global_confidence",
            "model_type",
            "fallback_used",
            "risk_flags",
            "event_count",
            "duration_seconds",
        ];

        const rows = historyItems.map((item) => {
            const row = getObject(item);
            const riskFlags = Array.isArray(row.risk_flags) ? row.risk_flags.join("|") : "";
            return [
                row.start_timestamp || row.timestamp || row.decision_timestamp || "",
                row.last_timestamp || row.timestamp || row.decision_timestamp || "",
                row.symbol || "",
                row.timeframe || "",
                row.final_signal || "",
                row.global_confidence ?? "",
                row.model_type || "",
                row.fallback_used ? "true" : "false",
                riskFlags,
                row.event_count ?? 1,
                row.duration_seconds ?? "",
            ];
        });

        const csv = [header, ...rows]
            .map((row) =>
                row
                    .map((value) => {
                        const text = String(value ?? "");
                        return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
                    })
                    .join(",")
            )
            .join("\n");

        const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
        const link = document.createElement("a");
        const ts = new Date().toISOString().replaceAll(":", "-");
        link.href = URL.createObjectURL(blob);
        link.download = `reporting_history_${symbol}_${timeframe}_${ts}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const exportPdf = async () => {
        const { jsPDF } = await import("jspdf");
        const doc = new jsPDF({ unit: "pt", format: "a4" });
        const pageW = doc.internal.pageSize.getWidth();
        const pageH = doc.internal.pageSize.getHeight();
        const trim = (text: string, max: number) => (text.length > max ? `${text.slice(0, max - 1)}...` : text);

        let y = 34;
        doc.setFont("helvetica", "bold");
        doc.setFontSize(17);
        doc.text("Trady - Reporting Dashboard", 30, y);

        doc.setFont("helvetica", "normal");
        doc.setFontSize(10);
        y += 16;
        doc.text(`Generated: ${new Date().toLocaleString()}`, 30, y);
        y += 14;
        doc.text(
            `Filters: symbol=${symbol}, timeframe=${timeframe}, model=${model || "all"}, horizon=${trendHorizon}, window=${windowSize}`,
            30,
            y
        );

        y += 18;
        doc.setFont("helvetica", "bold");
        doc.setFontSize(11);
        doc.text("KPI Summary", 30, y);

        doc.setFont("helvetica", "normal");
        doc.setFontSize(10);
        y += 13;

        const kpis: Array<[string, string]> = [
            ["Fallback Rate", fmtPct(performance.fallback_rate, 2)],
            ["Avg Latency", `${fmtNum(performance.avg_latency_ms, 1)} ms`],
            ["Avg Confidence", fmtPct(performance.avg_confidence, 2)],
            ["Disagreement", fmtPct(drift.disagreement_rate, 2)],
            ["Alert Level", String(alert.level || "no_data").toUpperCase()],
            ["History Rows", String(historyCount)],
        ];

        kpis.forEach(([k, v], i) => {
            const col = i % 2;
            const row = Math.floor(i / 2);
            doc.text(`${k}: ${v}`, 30 + col * 260, y + row * 13);
        });

        y += 46;
        doc.setFont("helvetica", "bold");
        doc.text("Drift and Confidence Trend", 30, y);
        y += 8;

        const canvas = trendCanvasRef.current;
        if (canvas) {
            const chartImg = canvas.toDataURL("image/png");
            const chartW = pageW - 60;
            const chartH = 180;
            doc.addImage(chartImg, "PNG", 30, y, chartW, chartH);
            y += chartH + 16;
        }

        doc.setFont("helvetica", "bold");
        const historyModeLabel = historyMode === "raw" ? "Raw Events" : "State Changes";
        doc.text(`Decision History (${historyModeLabel})`, 30, y);
        y += 12;

        doc.setFont("helvetica", "normal");
        doc.setFontSize(9);
        if (historyMode === "raw") {
            doc.text("Mode note: each row is a single decision event (no merge).", 30, y);
        } else {
            doc.text(
                `Mode note: identical consecutive events are merged (${historyCount} rows from ${historyRawCount} raw events).`,
                30,
                y
            );
        }
        y += 12;

        doc.text("Started", 30, y);
        doc.text("Last", 125, y);
        doc.text("Signal", 220, y);
        doc.text("Conf", 275, y);
        doc.text("Model", 320, y);
        doc.text("Events", 420, y);
        doc.text("Risk Flags", 470, y);
        y += 8;
        doc.line(30, y, pageW - 30, y);
        y += 10;

        historyItems.slice(0, 24).forEach((item) => {
            const row = getObject(item);
            if (y > pageH - 24) {
                doc.addPage();
                y = 34;
            }
            doc.text(trim(fmtDate(row.start_timestamp || row.timestamp || row.decision_timestamp), 20), 30, y);
            doc.text(trim(fmtDate(row.last_timestamp || row.timestamp || row.decision_timestamp), 20), 125, y);
            doc.text(trim(String(row.final_signal || "N/A").toUpperCase(), 8), 220, y);
            doc.text(trim(fmtPct(row.global_confidence || 0, 2), 10), 275, y);
            doc.text(trim(String(row.model_type || "unknown"), 16), 320, y);
            doc.text(trim(String(row.event_count ?? 1), 5), 420, y);
            const riskFlags = Array.isArray(row.risk_flags) ? row.risk_flags.join("|") : "none";
            doc.text(trim(riskFlags, 24), 470, y);
            y += 12;
        });

        const ts = new Date().toISOString().replaceAll(":", "-");
        doc.save(`reporting_dashboard_${symbol}_${timeframe}_${ts}.pdf`);
    };

    const agents = getObject(overview.agents);
    const technical = getObject(agents.technical);
    const macro = getObject(agents.macro);
    const sentiment = getObject(agents.sentiment);
    const decisionLast = getObject(agents.decision_last);

    const status = getObject(overview.status);
    const statusRows: Array<[string, unknown]> = [
        ["MT5", status.mt5],
        ["InfluxDB", status.influxdb],
        ["Postgres", status.postgres],
        ["Technical model", status.model],
        ["Macro model", status.macro_model],
        ["Sentiment model", status.sentiment_model],
        ["Decision model", status.decision_model],
        ["Tick count", status.tick_count],
        ["Last news refresh", status.last_news_refresh_ts],
    ];

    const recentAlerts = Array.isArray(overview.recent_alerts) ? [...overview.recent_alerts].reverse() : [];
    const newsPreview = Array.isArray(overview.news_preview) ? overview.news_preview : [];

    const renderMiniBars = (title: string, distValue: unknown, totalHint: unknown) => {
        const distribution = getObject(distValue);
        const entries = Object.entries(distribution);
        if (!entries.length) {
            return <div className={styles.listItem}><div className={styles.meta}>{title}: no data</div></div>;
        }

        const total =
            toNumber(totalHint) || entries.reduce((acc, [, value]) => acc + toNumber(value), 0);

        return (
            <>
                <div className={styles.listItem}>
                    <div className={styles.meta}>{title}</div>
                </div>
                {entries
                    .sort((a, b) => toNumber(b[1]) - toNumber(a[1]))
                    .slice(0, 5)
                    .map(([name, value]) => {
                        const count = toNumber(value);
                        const ratio = total > 0 ? count / total : 0;
                        return (
                            <div className={styles.miniRow} key={`${title}-${name}`}>
                                <div className={styles.name}>{name}</div>
                                <div className={styles.miniTrack}>
                                    <div className={styles.miniFill} style={{ width: `${(ratio * 100).toFixed(1)}%` }} />
                                </div>
                                <div className={styles.miniVal}>{fmtPct(ratio, 1)}</div>
                            </div>
                        );
                    })}
            </>
        );
    };

    return (
        <div className={styles.pageShell}>
            <header className="flex h-14 shrink-0 items-center gap-2 border-b px-6">
                <SidebarTrigger className="-ml-1" />
                <Separator orientation="vertical" className="mr-2 h-4" />
                <h1 className="text-lg font-semibold">Reporting</h1>
            </header>

            <main className={styles.page}>
                <section className={styles.pageHd}>
                    <h1>Reporting et Visualisation</h1>
                    <p>
                        Dashboard analyste en temps reel avec monitoring des agents, derive modele, alertes et
                        historique des decisions. Concu pour une lecture simple et rapide.
                    </p>
                </section>

                <section className={styles.controlRow}>
                    <div className={styles.ctrl}>
                        <label htmlFor="symbolSelect">Symbol</label>
                        <select id="symbolSelect" value={symbol} onChange={(e) => setSymbol(e.target.value)}>
                            <option>EURUSD</option>
                            <option>USDJPY</option>
                            <option>GBPUSD</option>
                            <option>USDCHF</option>
                        </select>
                    </div>
                    <div className={styles.ctrl}>
                        <label htmlFor="tfSelect">Timeframe</label>
                        <select id="tfSelect" value={timeframe} onChange={(e) => setTimeframe(e.target.value)}>
                            <option>1H</option>
                            <option>4H</option>
                            <option>1D</option>
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
                        <select id="horizonSelect" value={trendHorizon} onChange={(e) => setTrendHorizon(e.target.value)}>
                            <option value="short">short</option>
                            <option value="medium">medium</option>
                            <option value="long">long</option>
                        </select>
                    </div>
                    <div className={styles.ctrl}>
                        <label htmlFor="windowSelect">Window</label>
                        <select id="windowSelect" value={windowSize} onChange={(e) => setWindowSize(e.target.value)}>
                            <option>100</option>
                            <option>200</option>
                            <option>500</option>
                            <option>1000</option>
                        </select>
                    </div>
                    <div className={styles.ctrl}>
                        <label htmlFor="historyModeSelect">History Mode</label>
                        <select
                            id="historyModeSelect"
                            value={historyMode}
                            onChange={(e) => setHistoryMode(e.target.value)}
                        >
                            <option value="compressed">state changes</option>
                            <option value="raw">raw events</option>
                        </select>
                    </div>
                    <div className={styles.ctrl}>
                        <label>Actions</label>
                        <button type="button" onClick={() => void refreshDashboard()} disabled={loading}>
                            {loading ? "Refreshing..." : "Refresh"}
                        </button>
                    </div>
                    <div className={styles.ctrl}>
                        <label>Export</label>
                        <button type="button" onClick={exportCsv} disabled={!historyItems.length}>
                            Export CSV
                        </button>
                    </div>
                    <div className={styles.ctrl}>
                        <label>Report</label>
                        <button type="button" onClick={() => void exportPdf()} disabled={!historyItems.length}>
                            Export PDF
                        </button>
                    </div>
                </section>

                <section className={styles.kpiGrid}>
                    <article
                        className={styles.kpi}
                        onMouseEnter={(e) => showTip("kpiFallbackTip", e)}
                        onMouseMove={moveTip}
                        onMouseLeave={hideTip}
                    >
                        <span className={styles.kpiHelp}>?</span>
                        <div className={styles.k}>Fallback Rate</div>
                        <div className={styles.v}>{fmtPct(performance.fallback_rate, 2)}</div>
                        <div className={styles.sub}>{toNumber(performance.total)} events</div>
                    </article>
                    <article
                        className={styles.kpi}
                        onMouseEnter={(e) => showTip("kpiLatencyTip", e)}
                        onMouseMove={moveTip}
                        onMouseLeave={hideTip}
                    >
                        <span className={styles.kpiHelp}>?</span>
                        <div className={styles.k}>Avg Latency</div>
                        <div className={styles.v}>{fmtNum(performance.avg_latency_ms, 1)} ms</div>
                        <div className={styles.sub}>window {toNumber(performance.window)}</div>
                    </article>
                    <article
                        className={styles.kpi}
                        onMouseEnter={(e) => showTip("kpiConfidenceTip", e)}
                        onMouseMove={moveTip}
                        onMouseLeave={hideTip}
                    >
                        <span className={styles.kpiHelp}>?</span>
                        <div className={styles.k}>Avg Confidence</div>
                        <div className={styles.v}>{fmtPct(performance.avg_confidence, 2)}</div>
                        <div className={styles.sub}>conflict {fmtPct(performance.avg_conflict_index, 2)}</div>
                    </article>
                    <article
                        className={styles.kpi}
                        onMouseEnter={(e) => showTip("kpiDriftTip", e)}
                        onMouseMove={moveTip}
                        onMouseLeave={hideTip}
                    >
                        <span className={styles.kpiHelp}>?</span>
                        <div className={styles.k}>Disagreement</div>
                        <div className={styles.v}>{fmtPct(drift.disagreement_rate, 2)}</div>
                        <div className={styles.sub}>
                            {toNumber(drift.disagreement_count)}/{toNumber(drift.comparison_events)}
                        </div>
                    </article>
                    <article
                        className={styles.kpi}
                        onMouseEnter={(e) => showTip("kpiAlertTip", e)}
                        onMouseMove={moveTip}
                        onMouseLeave={hideTip}
                    >
                        <span className={styles.kpiHelp}>?</span>
                        <div className={styles.k}>Alert Level</div>
                        <div className={styles.v}>{String(alert.level || "no_data").toUpperCase()}</div>
                        <div className={styles.sub}>
                            warn {fmtPct(alert.threshold_warning, 0)} / crit {fmtPct(alert.threshold_critical, 0)}
                        </div>
                    </article>
                    <article
                        className={styles.kpi}
                        onMouseEnter={(e) => showTip("kpiHistoryTip", e)}
                        onMouseMove={moveTip}
                        onMouseLeave={hideTip}
                    >
                        <span className={styles.kpiHelp}>?</span>
                        <div className={styles.k}>History Rows</div>
                        <div className={styles.v}>{historyCount}</div>
                        <div className={styles.sub}>{historyRawCount} raw events</div>
                    </article>
                </section>

                <section className={styles.mainGrid}>
                    <div>
                        <article className={styles.card}>
                            <div className={styles.cardHd}>Agent Snapshot</div>
                            <div className={styles.cardBd}>
                                <div className={styles.agentsGrid}>
                                    <div className={styles.agentItem}>
                                        <div className={styles.agentName}>Technical</div>
                                        <div className={styles.agentSignal}>{String(technical.signal || "N/A").toUpperCase()}</div>
                                        <div className={styles.agentMeta}>
                                            conf {fmtPct(technical.confidence, 1)} - {technical.error ? "error" : "ok"}
                                        </div>
                                    </div>
                                    <div className={styles.agentItem}>
                                        <div className={styles.agentName}>Macro</div>
                                        <div className={styles.agentSignal}>{String(macro.signal || "N/A").toUpperCase()}</div>
                                        <div className={styles.agentMeta}>
                                            conf {fmtPct(macro.confidence, 1)} - {String(macro.last_macro_update || "no date")}
                                        </div>
                                    </div>
                                    <div className={styles.agentItem}>
                                        <div className={styles.agentName}>Sentiment</div>
                                        <div className={styles.agentSignal}>{String(sentiment.signal || "N/A").toUpperCase()}</div>
                                        <div className={styles.agentMeta}>
                                            conf {fmtPct(sentiment.confidence, 1)} - {String(sentiment.last_sentiment_update || "no date")}
                                        </div>
                                    </div>
                                    <div className={styles.agentItem}>
                                        <div className={styles.agentName}>Decision Last</div>
                                        <div className={styles.agentSignal}>{String(decisionLast.final_signal || "N/A").toUpperCase()}</div>
                                        <div className={styles.agentMeta}>
                                            conf {fmtPct(decisionLast.global_confidence, 1)} - {String(decisionLast.model_type || "unknown")}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </article>

                        <div className={styles.row2}>
                            <article className={styles.card}>
                                <div className={styles.cardHd}>Drift and Confidence Trend</div>
                                <div className={styles.cardBd}>
                                    <div className={styles.chartWrap}>
                                        <canvas ref={trendCanvasRef} width={960} height={220} />
                                    </div>
                                </div>
                            </article>

                            <article className={styles.card}>
                                <div className={styles.cardHd}>Decision History</div>
                                <div className={styles.cardBd}>
                                    <div className={styles.listItem} style={{ marginBottom: 8 }}>
                                        <div className={styles.meta}>
                                            {historyItems.length === 0
                                                ? "No history rows yet for these filters. Try a larger window, another model, or switch to raw events mode."
                                                : historyMode === "raw"
                                                    ? "Raw events mode: every recorded decision is shown, including repeated states."
                                                    : `State changes mode: repeated identical decisions are merged. Current top row represents ${String(getObject(historyItems[0]).event_count ?? 1)} event(s) over ${getObject(historyItems[0]).duration_seconds != null ? `${String(getObject(historyItems[0]).duration_seconds)}s` : "N/A"}.`}
                                        </div>
                                    </div>

                                    <div className={styles.tableWrap}>
                                        <table>
                                            <thead>
                                                <tr>
                                                    <th>Started</th>
                                                    <th>Last Update</th>
                                                    <th>Signal</th>
                                                    <th>Confidence</th>
                                                    <th>Model</th>
                                                    <th>Fallback</th>
                                                    <th>Risk Flags</th>
                                                    <th>Events</th>
                                                    <th>Duration</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {historyItems.length === 0 ? (
                                                    <tr>
                                                        <td colSpan={9}>No data</td>
                                                    </tr>
                                                ) : (
                                                    historyItems.map((item, index) => {
                                                        const row = getObject(item);
                                                        const riskFlags = Array.isArray(row.risk_flags)
                                                            ? row.risk_flags.join(", ")
                                                            : "none";
                                                        return (
                                                            <tr key={`history-${index}`}>
                                                                <td>{fmtDate(row.start_timestamp || row.timestamp || row.decision_timestamp)}</td>
                                                                <td>{fmtDate(row.last_timestamp || row.timestamp || row.decision_timestamp)}</td>
                                                                <td>{String(row.final_signal || "N/A").toUpperCase()}</td>
                                                                <td>{fmtPct(row.global_confidence, 2)}</td>
                                                                <td>{String(row.model_type || "unknown")}</td>
                                                                <td>{row.fallback_used ? "yes" : "no"}</td>
                                                                <td>{riskFlags || "none"}</td>
                                                                <td>{String(row.event_count ?? 1)}</td>
                                                                <td>
                                                                    {row.duration_seconds != null
                                                                        ? `${String(row.duration_seconds)}s`
                                                                        : "-"}
                                                                </td>
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
                    </div>

                    <div>
                        <article className={styles.card}>
                            <div className={styles.cardHd}>System Status</div>
                            <div className={styles.cardBd}>
                                <div className={styles.list}>
                                    {error ? (
                                        <div className={styles.listItem}>
                                            <div className={styles.meta}>{error}</div>
                                        </div>
                                    ) : (
                                        statusRows.map(([key, value]) => (
                                            <div className={styles.listItem} key={key}>
                                                <div className={styles.top}>
                                                    <strong>{key}</strong>
                                                    <span>
                                                        {typeof value === "boolean"
                                                            ? value
                                                                ? "online"
                                                                : "offline"
                                                            : String(value ?? "N/A")}
                                                    </span>
                                                </div>
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>
                        </article>

                        <article className={styles.card} style={{ marginTop: 10 }}>
                            <div className={styles.cardHd}>Recent Alert Transitions</div>
                            <div className={styles.cardBd}>
                                <div className={styles.list}>
                                    {recentAlerts.length === 0 ? (
                                        <div className={styles.listItem}>
                                            <div className={styles.meta}>No transitions yet</div>
                                        </div>
                                    ) : (
                                        recentAlerts.map((item, idx) => {
                                            const row = getObject(item);
                                            return (
                                                <div className={styles.listItem} key={`alert-${idx}`}>
                                                    <div className={styles.top}>
                                                        <span className={`${styles.flag} ${alertClass(row.level)}`}>
                                                            {String(row.level || "no_data")}
                                                        </span>
                                                        <span>{fmtPct(row.disagreement_rate, 2)}</span>
                                                    </div>
                                                    <div className={styles.meta}>{fmtDate(row.timestamp)}</div>
                                                </div>
                                            );
                                        })
                                    )}
                                </div>
                            </div>
                        </article>

                        <article className={styles.card} style={{ marginTop: 10 }}>
                            <div className={styles.cardHd}>News Preview</div>
                            <div className={styles.cardBd}>
                                <div className={styles.list}>
                                    {newsPreview.length === 0 ? (
                                        <div className={styles.listItem}>
                                            <div className={styles.meta}>No news available</div>
                                        </div>
                                    ) : (
                                        newsPreview.map((item, idx) => {
                                            const row = getObject(item);
                                            const title = String(row.title || "Untitled");
                                            return (
                                                <div className={styles.listItem} key={`news-${idx}`}>
                                                    <div className={styles.top}>
                                                        <strong>{title.slice(0, 70)}</strong>
                                                    </div>
                                                    <div className={styles.meta}>
                                                        {String(row.source || "Unknown")} - {fmtDate(row.published_at)}
                                                    </div>
                                                </div>
                                            );
                                        })
                                    )}
                                </div>
                            </div>
                        </article>

                        <article className={styles.card} style={{ marginTop: 10 }}>
                            <div className={styles.cardHd}>Decision Composition</div>
                            <div className={styles.cardBd}>
                                <div className={styles.listItem} style={{ marginBottom: 8 }}>
                                    <div className={styles.meta}>
                                        How to read: this section reveals what drives your decisions (model mix,
                                        signal mix, dominant risks).
                                    </div>
                                </div>

                                <div className={styles.miniBars}>
                                    {renderMiniBars(
                                        "Model distribution",
                                        performance.model_type_distribution,
                                        performance.total
                                    )}
                                </div>
                                <div className={styles.miniBars} style={{ marginTop: 10 }}>
                                    {renderMiniBars(
                                        "Signal distribution",
                                        performance.signal_distribution,
                                        performance.total
                                    )}
                                </div>
                                <div className={styles.miniBars} style={{ marginTop: 10 }}>
                                    {renderMiniBars(
                                        "Risk flag frequency",
                                        performance.risk_flag_frequency,
                                        performance.total
                                    )}
                                </div>
                            </div>
                        </article>
                    </div>
                </section>
            </main>

            {hoverTip.visible ? (
                <div className={styles.hoverTip} style={{ left: hoverTip.x, top: hoverTip.y, display: "block" }}>
                    {hoverTip.text}
                </div>
            ) : null}
        </div>
    );
}


