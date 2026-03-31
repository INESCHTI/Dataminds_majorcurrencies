"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import * as LightweightCharts from "lightweight-charts";
import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";
import styles from "./page.module.css";

const PAIRS = ["EURUSD", "USDJPY", "GBPUSD", "USDCHF"] as const;
type Pair = (typeof PAIRS)[number];

const LABELS: Record<Pair, string> = {
    EURUSD: "EUR/USD",
    USDJPY: "USD/JPY",
    GBPUSD: "GBP/USD",
    USDCHF: "USD/CHF",
};

const DECIMALS: Record<Pair, number> = {
    EURUSD: 5,
    USDJPY: 3,
    GBPUSD: 5,
    USDCHF: 5,
};

const TF_SEC: Record<string, number> = {
    LIVE: 1,
    "1S": 1,
    "1H": 3600,
    "4H": 14400,
    "1D": 86400,
};

interface Tick {
    bid?: number;
    spread?: number;
    time?: number;
    [key: string]: unknown;
}

interface Candle {
    time: number;
    open: number;
    high: number;
    low: number;
    close: number;
}

interface NewsArticle {
    title?: string;
    description?: string;
    source?: string;
    url?: string;
    published_at?: string;
}

interface TechnicalSignalState {
    signal: "BUY" | "SELL" | "HOLD" | "NA";
    confidence: number;
    error: string;
}

interface DecisionSignalState {
    signal: "BUY" | "SELL" | "HOLD" | "NA";
    confidence: number;
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

function resolveBackendOrigin(apiBase: string): string {
    if (!apiBase || apiBase.startsWith("/")) {
        return "";
    }
    return apiBase.replace(/\/api\/?$/, "");
}

function safeNumber(value: unknown, fallback = 0): number {
    const n = Number(value);
    return Number.isFinite(n) ? n : fallback;
}

function formatValue(value: unknown, digits = 2): string {
    const n = Number(value);
    if (!Number.isFinite(n)) return "-";
    return n.toFixed(digits);
}

function timeAgo(raw: unknown): string {
    if (!raw) return "";
    const delta = (Date.now() - new Date(String(raw)).getTime()) / 1000;
    if (!Number.isFinite(delta)) return "";
    if (delta < 60) return "just now";
    if (delta < 3600) return `${Math.floor(delta / 60)}m ago`;
    if (delta < 86400) return `${Math.floor(delta / 3600)}h ago`;
    return `${Math.floor(delta / 86400)}d ago`;
}

function classifyNewsImportance(article: NewsArticle): {
    label: string;
    cls: "impact-low" | "impact-medium" | "impact-high" | "impact-critical";
} {
    const text = `${article?.title || ""} ${article?.description || ""}`.toLowerCase();
    let score = 0;

    const hit = (words: string[], weight: number) => {
        if (words.some((word) => text.includes(word))) {
            score += weight;
        }
    };

    hit(["breaking", "war", "attack", "missile", "invasion", "sanction", "urgent"], 4);
    hit(["fed", "ecb", "boe", "boj", "interest rate", "rate hike", "rate cut", "fomc"], 4);
    hit(["cpi", "inflation", "nfp", "payroll", "unemployment", "gdp", "pmi"], 3);
    hit(["oil", "opec", "energy", "yield", "treasury"], 2);

    if (score >= 7) return { label: "Critical", cls: "impact-critical" };
    if (score >= 4) return { label: "High", cls: "impact-high" };
    if (score >= 2) return { label: "Moderate", cls: "impact-medium" };
    return { label: "Low", cls: "impact-low" };
}

export default function TradingPage() {
    const [sym, setSym] = useState<Pair>("EURUSD");
    const [tf, setTf] = useState("1H");
    const [wsOnline, setWsOnline] = useState(false);
    const [chartInitialized, setChartInitialized] = useState(false);
    const [chartLoading, setChartLoading] = useState(true);
    const [candleCount, setCandleCount] = useState(0);

    const [tickerData, setTickerData] = useState<Partial<Record<Pair, Tick>>>({});
    const [flashDirection, setFlashDirection] = useState<Partial<Record<Pair, "up" | "dn" | null>>>({});
    const [tickerSignals, setTickerSignals] = useState<Partial<Record<Pair, "BUY" | "SELL" | "HOLD" | "NA">>>({});

    const [technicalSignal, setTechnicalSignal] = useState<TechnicalSignalState>({
        signal: "NA",
        confidence: 0,
        error: "",
    });

    const [decisionSignal, setDecisionSignal] = useState<DecisionSignalState>({
        signal: "NA",
        confidence: 0,
    });

    const [news, setNews] = useState<NewsArticle[]>([]);
    const [newsLoading, setNewsLoading] = useState(true);

    const chartWrapRef = useRef<HTMLDivElement | null>(null);
    const chartRef = useRef<any>(null);
    const candleSeriesRef = useRef<any>(null);
    const areaSeriesRef = useRef<any>(null);
    const activeSeriesRef = useRef<any>(null);
    const tooltipRef = useRef<HTMLDivElement | null>(null);
    const resizeObserverRef = useRef<ResizeObserver | null>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimerRef = useRef<number | null>(null);

    const chartReadyRef = useRef(false);
    const symRef = useRef<Pair>("EURUSD");
    const tfRef = useRef("1H");
    const wsDelayRef = useRef(2000);
    const prevPxRef = useRef<Partial<Record<Pair, number>>>({});
    const flashTimeoutsRef = useRef<Partial<Record<Pair, number>>>({});
    const lastChartTickAtMsRef = useRef(0);
    const lastLiveFallbackReloadAtMsRef = useRef(0);
    const unmountedRef = useRef(false);

    const candleMapRef = useRef<Partial<Record<Pair, Record<string, Map<number, Candle>>>>>({});

    const BACKEND_API_BASE = useMemo(() => resolveBackendApiBase(), []);
    const BACKEND_ORIGIN = useMemo(() => resolveBackendOrigin(BACKEND_API_BASE), [BACKEND_API_BASE]);
    const chartTitle = `${LABELS[sym]} - ${tf}`;

    useEffect(() => {
        symRef.current = sym;
    }, [sym]);

    useEffect(() => {
        tfRef.current = tf;
    }, [tf]);

    const clearFlashTimeout = (pair: Pair) => {
        const id = flashTimeoutsRef.current[pair];
        if (id) {
            window.clearTimeout(id);
            delete flashTimeoutsRef.current[pair];
        }
    };

    const updateChartWithTick = useCallback((pair: Pair, tick: Tick) => {
        if (pair !== symRef.current) return;
        if (!chartReadyRef.current || !activeSeriesRef.current || !chartRef.current) return;

        const price = safeNumber(tick.bid, NaN);
        if (!Number.isFinite(price) || price <= 0) return;

        const tfNow = tfRef.current;
        const tfSec = TF_SEC[tfNow] || 3600;
        const rawTickTime = safeNumber(tick.time, NaN);
        const safeTickTime = Number.isFinite(rawTickTime) && rawTickTime > 0 ? rawTickTime : Math.floor(Date.now() / 1000);
        if (safeTickTime > 9_999_999_999) return;

        const candleTime = Math.floor(safeTickTime / tfSec) * tfSec;

        if (!candleMapRef.current[pair]) candleMapRef.current[pair] = {};
        if (!candleMapRef.current[pair]![tfNow]) candleMapRef.current[pair]![tfNow] = new Map<number, Candle>();

        const map = candleMapRef.current[pair]![tfNow]!;
        if (map.has(candleTime)) {
            const c = map.get(candleTime)!;
            c.close = price;
            if (price > c.high) c.high = price;
            if (price < c.low) c.low = price;
            if (tfNow === "LIVE") {
                activeSeriesRef.current.update({ time: candleTime, value: price });
            } else {
                activeSeriesRef.current.update(c);
            }
        } else {
            const keys = [...map.keys()];
            const lastTime = keys.length ? Math.max(...keys) : 0;
            if (candleTime >= lastTime) {
                const newCandle: Candle = { time: candleTime, open: price, high: price, low: price, close: price };
                map.set(candleTime, newCandle);
                if (tfNow === "LIVE") {
                    activeSeriesRef.current.update({ time: candleTime, value: price });
                } else {
                    activeSeriesRef.current.update(newCandle);
                }
            }
        }

        chartRef.current.timeScale().scrollToRealTime();
        setCandleCount(map.size);
        lastChartTickAtMsRef.current = Date.now();
    }, []);

    const updateTicker = useCallback((pair: Pair, tick: Tick) => {
        setTickerData((prev) => ({ ...prev, [pair]: tick }));

        const bid = safeNumber(tick.bid, NaN);
        const prevBid = prevPxRef.current[pair];
        if (Number.isFinite(bid)) {
            if (typeof prevBid === "number") {
                const dir: "up" | "dn" | null = bid > prevBid ? "up" : bid < prevBid ? "dn" : null;
                if (dir) {
                    setFlashDirection((prev) => ({ ...prev, [pair]: dir }));
                    clearFlashTimeout(pair);
                    flashTimeoutsRef.current[pair] = window.setTimeout(() => {
                        setFlashDirection((prev) => ({ ...prev, [pair]: null }));
                    }, 650);
                }
            }
            prevPxRef.current[pair] = bid;
        }

        updateChartWithTick(pair, tick);
    }, [updateChartWithTick]);

    const loadChart = useCallback(async () => {
        if (!chartInitialized || !chartRef.current || !candleSeriesRef.current || !areaSeriesRef.current) return;

        chartReadyRef.current = false;
        setChartLoading(true);
        setCandleCount(0);

        candleSeriesRef.current.setData([]);
        areaSeriesRef.current.setData([]);

        if (tf === "LIVE") {
            candleSeriesRef.current.applyOptions({ visible: false });
            areaSeriesRef.current.applyOptions({ visible: true });
            activeSeriesRef.current = areaSeriesRef.current;
        } else {
            candleSeriesRef.current.applyOptions({ visible: true });
            areaSeriesRef.current.applyOptions({ visible: false });
            activeSeriesRef.current = candleSeriesRef.current;
        }

        if (!candleMapRef.current[sym]) candleMapRef.current[sym] = {};
        candleMapRef.current[sym]![tf] = new Map<number, Candle>();

        try {
            const lookback = ({ LIVE: "1h", "1S": "6h", "1H": "30d", "4H": "365d", "1D": "365d" } as Record<string, string>)[tf] || "30d";
            const actualTf = tf === "LIVE" ? "1S" : tf;
            const url = `${BACKEND_API_BASE}/prices/${sym}?timeframe=${actualTf}&start_date=${lookback}&limit=1000`;
            const res = await fetch(url, { cache: "no-store" });
            if (!res.ok) {
                throw new Error(`HTTP ${res.status}`);
            }

            const payload = (await res.json()) as { candles?: Array<Record<string, unknown>> };
            const candles = Array.isArray(payload.candles) ? payload.candles : [];
            const map = candleMapRef.current[sym]![tf]!;

            candles.forEach((candle) => {
                const time = safeNumber(candle.time, NaN);
                const open = safeNumber(candle.open, NaN);
                const high = safeNumber(candle.high, NaN);
                const low = safeNumber(candle.low, NaN);
                const close = safeNumber(candle.close, NaN);
                if (!Number.isFinite(time) || !Number.isFinite(open) || !Number.isFinite(close)) return;
                map.set(time, { time, open, high, low, close });
            });

            const sorted = [...map.values()].sort((a, b) => a.time - b.time);
            if (tf === "LIVE") {
                activeSeriesRef.current.setData(sorted.map((c) => ({ time: c.time, value: c.close })));
            } else {
                activeSeriesRef.current.setData(sorted);
            }

            const total = sorted.length;
            const visibleByTf: Record<string, number> = { LIVE: 80, "1S": 100, "1H": 110, "4H": 90, "1D": 75 };
            const visibleCount = Math.min(visibleByTf[tf] || 120, total || 120);
            chartRef.current.timeScale().setVisibleLogicalRange({
                from: Math.max(0, total - visibleCount),
                to: Math.max(visibleCount, total),
            });

            setCandleCount(sorted.length);
            lastChartTickAtMsRef.current = Date.now();
        } catch {
            setCandleCount(0);
        } finally {
            window.setTimeout(() => {
                chartReadyRef.current = true;
                setChartLoading(false);
            }, 500);
        }
    }, [BACKEND_API_BASE, chartInitialized, sym, tf]);

    const loadSignal = useCallback(async () => {
        try {
            const response = await fetch(`${BACKEND_API_BASE}/signals/${sym}?timeframe=${tf}`, { cache: "no-store" });
            const data = (await response.json()) as Record<string, unknown>;
            const signal = String(data.signal || "NA").replace("/", "").toUpperCase() as TechnicalSignalState["signal"];
            setTechnicalSignal({
                signal: ["BUY", "SELL", "HOLD"].includes(signal) ? signal : "NA",
                confidence: safeNumber(data.confidence, 0),
                error: String(data.error || ""),
            });
        } catch {
            setTechnicalSignal({ signal: "NA", confidence: 0, error: "" });
        }
    }, [BACKEND_API_BASE, sym, tf]);

    const loadDecisionSummary = useCallback(async () => {
        try {
            const response = await fetch(`${BACKEND_API_BASE}/signals/decision/${sym}`, { cache: "no-store" });
            const data = (await response.json()) as Record<string, unknown>;
            const signal = String(data.final_signal || "NA").toUpperCase() as DecisionSignalState["signal"];
            const confidence = safeNumber(data.global_confidence ?? data.final_confidence, 0);
            setDecisionSignal({
                signal: ["BUY", "SELL", "HOLD"].includes(signal) ? signal : "NA",
                confidence,
            });
        } catch {
            setDecisionSignal({ signal: "NA", confidence: 0 });
        }
    }, [BACKEND_API_BASE, sym]);

    const loadTickerSignals = useCallback(async () => {
        const updates: Partial<Record<Pair, "BUY" | "SELL" | "HOLD" | "NA">> = {};
        await Promise.all(
            PAIRS.map(async (pair) => {
                try {
                    const response = await fetch(`${BACKEND_API_BASE}/signals/${pair}?timeframe=1H`, { cache: "no-store" });
                    const data = (await response.json()) as Record<string, unknown>;
                    const signal = String(data.signal || "NA").toUpperCase() as "BUY" | "SELL" | "HOLD" | "NA";
                    updates[pair] = ["BUY", "SELL", "HOLD"].includes(signal) ? signal : "NA";
                } catch {
                    updates[pair] = "NA";
                }
            })
        );
        setTickerSignals(updates);
    }, [BACKEND_API_BASE]);

    const loadNews = useCallback(async () => {
        setNewsLoading(true);
        try {
            const response = await fetch(`${BACKEND_API_BASE}/news?limit=15`, { cache: "no-store" });
            const data = (await response.json()) as { articles?: NewsArticle[] };
            setNews(Array.isArray(data.articles) ? data.articles : []);
        } catch {
            setNews([]);
        } finally {
            setNewsLoading(false);
        }
    }, [BACKEND_API_BASE]);

    const maybeRecoverLiveChart = useCallback(async () => {
        const currentTf = tfRef.current;
        if (currentTf !== "LIVE" && currentTf !== "1S") return;

        const now = Date.now();
        const staleByTickAge = now - lastChartTickAtMsRef.current > 12000;
        const cooldownPassed = now - lastLiveFallbackReloadAtMsRef.current > 30000;
        if (cooldownPassed && (!wsOnline || staleByTickAge)) {
            lastLiveFallbackReloadAtMsRef.current = now;
            await loadChart();
            await loadSignal();
        }
    }, [loadChart, loadSignal, wsOnline]);

    useEffect(() => {
        if (!chartWrapRef.current) return;

        const wrap = chartWrapRef.current;

        const chart = LightweightCharts.createChart(wrap, {
            layout: { background: { color: "#0d1117" }, textColor: "#8899b0" },
            grid: { vertLines: { color: "#161f2e" }, horzLines: { color: "#161f2e" } },
            crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
            rightPriceScale: { borderColor: "#161f2e" },
            timeScale: { borderColor: "#161f2e", timeVisible: true, secondsVisible: false },
            width: wrap.clientWidth,
            height: wrap.clientHeight,
        });

        const candleSeries = chart.addSeries(LightweightCharts.CandlestickSeries, {
            upColor: "#00d9a3",
            downColor: "#ff4466",
            borderUpColor: "#00d9a3",
            borderDownColor: "#ff4466",
            wickUpColor: "#00d9a3",
            wickDownColor: "#ff4466",
        });

        const areaSeries = chart.addSeries(LightweightCharts.AreaSeries, {
            lineColor: "#4488ff",
            topColor: "rgba(68,136,255,0.4)",
            bottomColor: "rgba(68,136,255,0.0)",
        });
        areaSeries.applyOptions({ visible: false });

        const tip = document.createElement("div");
        tip.className = "chart-tooltip";
        wrap.appendChild(tip);

        chart.subscribeCrosshairMove((param: any) => {
            if (!param?.time || !param?.point || param.point.x < 0 || param.point.y < 0) {
                tip.style.display = "none";
                return;
            }

            const seriesData = param.seriesData?.get(activeSeriesRef.current);
            if (!seriesData) {
                tip.style.display = "none";
                return;
            }

            const dec = DECIMALS[symRef.current] || 5;
            let html = `<strong>${LABELS[symRef.current]}</strong><br>`;

            if (tfRef.current === "LIVE") {
                const value = safeNumber((seriesData as Record<string, unknown>).value, NaN);
                html += `Price: <span style="color:var(--text)">${Number.isFinite(value) ? value.toFixed(dec) : "-"}</span>`;
            } else {
                const open = safeNumber((seriesData as Record<string, unknown>).open, NaN);
                const high = safeNumber((seriesData as Record<string, unknown>).high, NaN);
                const low = safeNumber((seriesData as Record<string, unknown>).low, NaN);
                const close = safeNumber((seriesData as Record<string, unknown>).close, NaN);
                const cColor = close >= open ? "var(--green)" : "var(--red)";
                html += `O: <span>${open.toFixed(dec)}</span>  H: <span>${high.toFixed(dec)}</span><br>`;
                html += `L: <span>${low.toFixed(dec)}</span>  C: <span style="color:${cColor}">${close.toFixed(dec)}</span>`;
            }

            tip.innerHTML = html;
            tip.style.display = "block";

            const x = param.point.x;
            const y = param.point.y;
            let left = x + 15;
            let top = y + 15;
            if (left > wrap.clientWidth - 150) left = x - 150;
            if (top > wrap.clientHeight - 80) top = y - 80;
            tip.style.left = `${left}px`;
            tip.style.top = `${top}px`;
        });

        const resizeObserver = new ResizeObserver(([entry]) => {
            const { width, height } = entry.contentRect;
            if (width > 0 && height > 0) {
                chart.resize(width, height);
            }
        });
        resizeObserver.observe(wrap);

        chartRef.current = chart;
        candleSeriesRef.current = candleSeries;
        areaSeriesRef.current = areaSeries;
        activeSeriesRef.current = candleSeries;
        tooltipRef.current = tip;
        resizeObserverRef.current = resizeObserver;
        chartReadyRef.current = true;
        setChartInitialized(true);

        return () => {
            resizeObserver.disconnect();
            chart.remove();
            if (tip.parentNode === wrap) {
                wrap.removeChild(tip);
            }
            tooltipRef.current = null;
            chartRef.current = null;
            candleSeriesRef.current = null;
            areaSeriesRef.current = null;
            activeSeriesRef.current = null;
        };
    }, []);

    useEffect(() => {
        if (!chartInitialized) return;
        void loadChart();
        void loadSignal();
        void loadDecisionSummary();
    }, [chartInitialized, loadChart, loadSignal, loadDecisionSummary]);

    useEffect(() => {
        if (!chartInitialized) return;
        void loadNews();
        void loadTickerSignals();

        const newsTimer = window.setInterval(() => {
            void loadNews();
        }, 30000);

        const tickerSignalTimer = window.setInterval(() => {
            void loadTickerSignals();
        }, 30000);

        return () => {
            window.clearInterval(newsTimer);
            window.clearInterval(tickerSignalTimer);
        };
    }, [chartInitialized, loadNews, loadTickerSignals]);

    useEffect(() => {
        if (!chartInitialized) return;
        const timer = window.setInterval(() => {
            void loadSignal();
            void loadDecisionSummary();
        }, 30000);

        return () => window.clearInterval(timer);
    }, [chartInitialized, loadSignal, loadDecisionSummary]);

    useEffect(() => {
        if (!chartInitialized) return;
        const timer = window.setInterval(() => {
            void maybeRecoverLiveChart();
        }, 6000);
        return () => window.clearInterval(timer);
    }, [chartInitialized, maybeRecoverLiveChart]);

    useEffect(() => {
        unmountedRef.current = false;

        const connectWs = () => {
            if (unmountedRef.current) return;

            const origin = BACKEND_ORIGIN || window.location.origin;
            const wsProtocol = origin.startsWith("https") ? "wss" : "ws";
            const host = origin.replace(/^https?:\/\//, "");
            const ws = new WebSocket(`${wsProtocol}://${host}/ws/prices`);
            wsRef.current = ws;

            ws.onopen = () => {
                wsDelayRef.current = 2000;
                setWsOnline(true);
            };

            ws.onmessage = (event) => {
                try {
                    const msg = JSON.parse(event.data) as { type?: string; data?: Record<string, Tick> };
                    if (msg.type !== "ticks" || !msg.data) return;

                    Object.entries(msg.data).forEach(([pair, tick]) => {
                        if (!PAIRS.includes(pair as Pair)) return;
                        updateTicker(pair as Pair, tick);
                    });
                } catch {
                    // Ignore parse errors for malformed frames
                }
            };

            ws.onclose = () => {
                setWsOnline(false);
                wsRef.current = null;
                if (unmountedRef.current) return;

                wsDelayRef.current = Math.min(wsDelayRef.current * 1.5, 30000);
                reconnectTimerRef.current = window.setTimeout(connectWs, wsDelayRef.current);
            };

            ws.onerror = () => {
                ws.close();
            };
        };

        connectWs();

        return () => {
            unmountedRef.current = true;
            if (reconnectTimerRef.current) {
                window.clearTimeout(reconnectTimerRef.current);
            }
            if (wsRef.current) {
                wsRef.current.close();
            }
            PAIRS.forEach((pair) => clearFlashTimeout(pair));
        };
    }, [BACKEND_ORIGIN, updateTicker]);

    const technicalFillColor = {
        BUY: "#00d9a3",
        SELL: "#ff4466",
        HOLD: "#f5b942",
        NA: "#3d5066",
    }[technicalSignal.signal];

    const decisionFillColor = {
        BUY: "#00d9a3",
        SELL: "#ff4466",
        HOLD: "#f5b942",
        NA: "#3d5066",
    }[decisionSignal.signal];

    const signalArrow = {
        BUY: "UP BUY",
        SELL: "DOWN SELL",
        HOLD: "DOT HOLD",
        NA: "N/A",
    }[technicalSignal.signal];

    const tfButtons = ["LIVE", "1S", "1H", "4H", "1D"];

    return (
        <div className="flex h-full flex-col bg-background">
            <header className="flex h-14 shrink-0 items-center gap-2 border-b px-6">
                <SidebarTrigger className="-ml-1" />
                <Separator orientation="vertical" className="mr-2 h-4" />
                <h1 className="text-lg font-semibold">Trading</h1>
            </header>

            <div className={`${styles.root} trady-trading-page`}>
                <div className="ticker-strip">
                    {PAIRS.map((pair) => {
                        const tick = tickerData[pair];
                        const bid = safeNumber(tick?.bid, NaN);
                        const spread = safeNumber(tick?.spread, NaN);
                        const directionClass = flashDirection[pair] ? `flash-${flashDirection[pair]}` : "";
                        const tickerSignal = tickerSignals[pair] || "NA";
                        const signalClass = tickerSignal === "BUY" ? "buy" : tickerSignal === "SELL" ? "sell" : tickerSignal === "HOLD" ? "hold" : "";

                        return (
                            <div
                                key={pair}
                                className={`ticker-card ${sym === pair ? "selected" : ""} ${directionClass}`.trim()}
                                onClick={() => setSym(pair)}
                                role="button"
                                tabIndex={0}
                                onKeyDown={(event) => {
                                    if (event.key === "Enter" || event.key === " ") {
                                        setSym(pair);
                                    }
                                }}
                            >
                                <div className={`ticker-signal ${signalClass}`}></div>
                                <div className="ticker-pair">{LABELS[pair]}</div>
                                <div className="ticker-bid">{Number.isFinite(bid) ? bid.toFixed(DECIMALS[pair]) : "--.--"}</div>
                                <div className="ticker-meta">{Number.isFinite(spread) ? `${spread.toFixed(1)} pips` : "-- pips"}</div>
                            </div>
                        );
                    })}
                </div>

                <div className="main">
                    <div className="chart-panel">
                        <div className="chart-toolbar">
                            <span className="chart-title">{chartTitle}</span>
                            <div className="candle-meta">
                                <span>{candleCount}</span> candles {wsOnline ? "" : "(offline)"}
                            </div>
                            <div className="tf-group">
                                {tfButtons.map((buttonTf) => (
                                    <button
                                        key={buttonTf}
                                        className={`tf-btn ${tf === buttonTf ? "active" : ""}`.trim()}
                                        onClick={() => setTf(buttonTf)}
                                        type="button"
                                    >
                                        {buttonTf}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="chart-wrap" ref={chartWrapRef}>
                            {chartLoading ? (
                                <div className="spin-wrap">
                                    <div className="spinner"></div>
                                </div>
                            ) : null}
                        </div>
                    </div>

                    <div className="sidebar">
                        <div className="card decision-summary-card">
                            <div className="card-hd">Decision Signal</div>
                            <div className="signal-body">
                                <div className={`sig-val ${decisionSignal.signal}`}>{decisionSignal.signal === "NA" ? "--" : decisionSignal.signal}</div>
                                <div className="sig-conf" style={{ fontSize: 14 }}>{`${(decisionSignal.confidence * 100).toFixed(1)}%`}</div>
                                <div className="conf-track">
                                    <div
                                        className="conf-fill"
                                        style={{ width: `${decisionSignal.confidence * 100}%`, background: decisionFillColor }}
                                    ></div>
                                </div>
                                <a href={`${BACKEND_ORIGIN || ""}/decision.html`} className="dec-link">
                                    VIEW DETAILS -&gt;
                                </a>
                            </div>
                        </div>

                        <div className="card">
                            <div className="card-hd">Technical Signal</div>
                            <div className="signal-body">
                                <div className="sig-dir">{signalArrow}</div>
                                <div className={`sig-val ${technicalSignal.signal}`}>{technicalSignal.signal === "NA" ? "N/A" : technicalSignal.signal}</div>
                                <div className="sig-conf">{`${(technicalSignal.confidence * 100).toFixed(1)}%`}</div>
                                <div className="conf-track">
                                    <div
                                        className="conf-fill"
                                        style={{ width: `${technicalSignal.confidence * 100}%`, background: technicalFillColor }}
                                    ></div>
                                </div>
                                <div className="sig-meta">{`${LABELS[sym]} - ${tf}`}</div>
                                {technicalSignal.error ? <div className="sig-err">{technicalSignal.error}</div> : null}
                            </div>
                        </div>

                        <div className="card news-card">
                            <div className="card-hd">Latest News</div>
                            <div className="news-list">
                                {newsLoading ? (
                                    <div className="news-empty">Loading...</div>
                                ) : news.length === 0 ? (
                                    <div className="news-empty">No news available</div>
                                ) : (
                                    news.map((article, idx) => {
                                        const importance = classifyNewsImportance(article);
                                        return (
                                            <a
                                                className="news-item"
                                                href={article.url || "#"}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                key={`${article.title || "untitled"}-${idx}`}
                                            >
                                                <div className="news-row">
                                                    <div className="news-title">{article.title || "Untitled"}</div>
                                                    <span className={`impact-badge ${importance.cls}`}>{importance.label}</span>
                                                </div>
                                                <div className="news-foot">
                                                    <span className="news-src">{article.source || "-"}</span>
                                                    <span>{timeAgo(article.published_at)}</span>
                                                </div>
                                            </a>
                                        );
                                    })
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
