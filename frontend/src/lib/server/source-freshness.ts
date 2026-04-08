import { Client as PgClient } from "pg";
import { InfluxDB } from "@influxdata/influxdb-client";
import { promises as fs } from "fs";
import path from "path";

export interface SourceFreshness {
    ohlcv: {
        available: boolean;
        latest_timestamp: string | null;
        age_minutes: number | null;
        error?: string;
    };
    macro: {
        available: boolean;
        latest_timestamp: string | null;
        age_minutes: number | null;
        error?: string;
    };
    news: {
        available: boolean;
        latest_timestamp: string | null;
        age_minutes: number | null;
        error?: string;
    };
}

export interface InfluxQuoteRow {
    symbol: string;
    timeframe: string;
    time: string | null;
    open: number | null;
    high: number | null;
    low: number | null;
    close: number | null;
    volume: number | null;
}

function parseDate(value: unknown): Date | null {
    if (!value) return null;
    const d = new Date(String(value));
    return Number.isNaN(d.getTime()) ? null : d;
}

let envLoaded = false;
let envLoadingPromise: Promise<void> | null = null;

function parseDotenvContent(content: string) {
    const out: Record<string, string> = {};
    for (const rawLine of content.split(/\r?\n/)) {
        const line = rawLine.trim();
        if (!line || line.startsWith("#")) continue;
        const idx = line.indexOf("=");
        if (idx <= 0) continue;
        const key = line.slice(0, idx).trim();
        let value = line.slice(idx + 1).trim();
        if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
            value = value.slice(1, -1);
        }
        out[key] = value;
    }
    return out;
}

async function tryReadEnvFile(filePath: string): Promise<Record<string, string>> {
    try {
        const data = await fs.readFile(filePath);
        const utf8 = data.toString("utf8");
        if (utf8.includes("=")) {
            return parseDotenvContent(utf8);
        }
        const utf16 = data.toString("utf16le");
        if (utf16.includes("=")) {
            return parseDotenvContent(utf16);
        }
        return {};
    } catch {
        return {};
    }
}

async function ensureSourceEnvLoaded() {
    if (envLoaded) return;

    if (!envLoadingPromise) {
        envLoadingPromise = (async () => {
            const cwd = process.cwd();
            const candidates = [
                path.resolve(cwd, ".env"),
                path.resolve(cwd, "../.env"),
                path.resolve(cwd, "../agents/.env"),
                path.resolve(cwd, "agents/.env"),
            ];

            for (const p of candidates) {
                const kv = await tryReadEnvFile(p);
                for (const [k, v] of Object.entries(kv)) {
                    if (!process.env[k] || process.env[k] === "") {
                        process.env[k] = v;
                    }
                }
            }
            envLoaded = true;
        })();
    }

    await envLoadingPromise;
}

export async function getInfluxLatestQuotes(symbols: string[] = ["EURUSD", "USDJPY", "GBPUSD", "USDCHF"]): Promise<InfluxQuoteRow[]> {
    await ensureSourceEnvLoaded();
    const url = process.env.INFLUXDB_URL;
    const token = process.env.INFLUXDB_TOKEN;
    const org = process.env.INFLUXDB_ORG;
    const bucket = process.env.INFLUXDB_BUCKET;

    if (!url || !token || !org || !bucket) {
        return [];
    }

    const influx = new InfluxDB({ url, token });
    const queryApi = influx.getQueryApi(org);
    const rows: InfluxQuoteRow[] = [];

    for (const symbol of symbols) {
        try {
            const flux = `
from(bucket: "${bucket}")
  |> range(start: -30d)
  |> filter(fn: (r) => r["_measurement"] == "forex_prices")
  |> filter(fn: (r) => r["symbol"] == "${symbol}")
  |> filter(fn: (r) => r["timeframe"] == "1H")
  |> filter(fn: (r) => r["_field"] == "open" or r["_field"] == "high" or r["_field"] == "low" or r["_field"] == "close" or r["_field"] == "volume")
  |> pivot(rowKey:["_time"], columnKey:["_field"], valueColumn:"_value")
  |> sort(columns:["_time"], desc:true)
  |> limit(n:1)
`;
            const result = await queryApi.collectRows(flux);
            const r = (result[0] as Record<string, unknown>) || {};
            rows.push({
                symbol,
                timeframe: "1H",
                time: r._time ? new Date(String(r._time)).toISOString() : null,
                open: Number.isFinite(Number(r.open)) ? Number(r.open) : null,
                high: Number.isFinite(Number(r.high)) ? Number(r.high) : null,
                low: Number.isFinite(Number(r.low)) ? Number(r.low) : null,
                close: Number.isFinite(Number(r.close)) ? Number(r.close) : null,
                volume: Number.isFinite(Number(r.volume)) ? Number(r.volume) : null,
            });
        } catch {
            rows.push({ symbol, timeframe: "1H", time: null, open: null, high: null, low: null, close: null, volume: null });
        }
    }

    return rows;
}

export async function getPostgresPreview(limit = 20) {
    await ensureSourceEnvLoaded();
    const cfg = buildPgConfig();
    if (!cfg) {
        return { macro: [], news: [], events: [], error: "postgres_env_missing" };
    }

    const client = new PgClient(cfg);
    try {
        await client.connect();

        const macroRes = await client.query(
            "SELECT date, series_id, indicator_name, value FROM economic_indicators ORDER BY date DESC LIMIT $1",
            [limit]
        );
        const newsRes = await client.query(
            "SELECT published_at, source, title FROM news_articles ORDER BY published_at DESC LIMIT $1",
            [limit]
        );
        const eventsRes = await client.query(
            "SELECT event_date, currency, event_name, importance, forecast, actual FROM economic_events ORDER BY event_date DESC LIMIT $1",
            [limit]
        );

        return {
            macro: macroRes.rows,
            news: newsRes.rows,
            events: eventsRes.rows,
            error: null,
        };
    } catch (error) {
        return {
            macro: [],
            news: [],
            events: [],
            error: error instanceof Error ? error.message : "postgres_query_failed",
        };
    } finally {
        try {
            await client.end();
        } catch {
            // no-op
        }
    }
}

function ageMinutes(value: Date | null): number | null {
    if (!value) return null;
    return Number(((Date.now() - value.getTime()) / 60000).toFixed(2));
}

function buildPgConfig() {
    const host = process.env.POSTGRES_HOST;
    const port = Number(process.env.POSTGRES_PORT || "5432");
    const database = process.env.POSTGRES_DB;
    const user = process.env.POSTGRES_USER;
    const password = process.env.POSTGRES_PASSWORD;

    if (!host || !database || !user) {
        return null;
    }

    return { host, port, database, user, password };
}

async function queryPostgresLatest() {
    const cfg = buildPgConfig();
    if (!cfg) {
        return {
            macro: { available: false, latest_timestamp: null, age_minutes: null, error: "postgres_env_missing" },
            news: { available: false, latest_timestamp: null, age_minutes: null, error: "postgres_env_missing" },
        };
    }

    const client = new PgClient(cfg);
    try {
        await client.connect();

        const macroRes = await client.query("SELECT MAX(date) AS latest FROM economic_indicators");
        const newsRes = await client.query("SELECT MAX(published_at) AS latest FROM news_articles");

        const macroDate = parseDate(macroRes.rows?.[0]?.latest ?? null);
        const newsDate = parseDate(newsRes.rows?.[0]?.latest ?? null);

        return {
            macro: {
                available: true,
                latest_timestamp: macroDate ? macroDate.toISOString() : null,
                age_minutes: ageMinutes(macroDate),
            },
            news: {
                available: true,
                latest_timestamp: newsDate ? newsDate.toISOString() : null,
                age_minutes: ageMinutes(newsDate),
            },
        };
    } catch (error) {
        const msg = error instanceof Error ? error.message : "postgres_query_failed";
        return {
            macro: { available: false, latest_timestamp: null, age_minutes: null, error: msg },
            news: { available: false, latest_timestamp: null, age_minutes: null, error: msg },
        };
    } finally {
        try {
            await client.end();
        } catch {
            // no-op
        }
    }
}

async function queryInfluxLatest(pair: string) {
    const url = process.env.INFLUXDB_URL;
    const token = process.env.INFLUXDB_TOKEN;
    const org = process.env.INFLUXDB_ORG;
    const bucket = process.env.INFLUXDB_BUCKET;

    if (!url || !token || !org || !bucket) {
        return { available: false, latest_timestamp: null, age_minutes: null, error: "influx_env_missing" };
    }

    try {
        const influx = new InfluxDB({ url, token });
        const queryApi = influx.getQueryApi(org);
        const symbol = pair.toUpperCase();

        const flux = `
from(bucket: "${bucket}")
  |> range(start: -30d)
  |> filter(fn: (r) => r["_measurement"] == "forex_prices")
  |> filter(fn: (r) => r["symbol"] == "${symbol}")
  |> keep(columns: ["_time"])
  |> sort(columns: ["_time"], desc: true)
  |> limit(n: 1)
`;

        const rows = await queryApi.collectRows(flux);
        const latest = rows.length > 0 ? parseDate((rows[0] as Record<string, unknown>)._time ?? null) : null;

        return {
            available: true,
            latest_timestamp: latest ? latest.toISOString() : null,
            age_minutes: ageMinutes(latest),
        };
    } catch (error) {
        const msg = error instanceof Error ? error.message : "influx_query_failed";
        return { available: false, latest_timestamp: null, age_minutes: null, error: msg };
    }
}

export async function getSourceFreshness(pair: string): Promise<SourceFreshness> {
    await ensureSourceEnvLoaded();
    const [pg, influx] = await Promise.all([
        queryPostgresLatest(),
        queryInfluxLatest(pair),
    ]);

    return {
        ohlcv: influx,
        macro: pg.macro,
        news: pg.news,
    };
}
