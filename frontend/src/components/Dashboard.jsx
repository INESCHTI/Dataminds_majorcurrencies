import React, { useEffect, useState } from 'react';
import { getHealth, getForexData, generateSignals } from '../services/api';
import SymbolTimeframeSelect from './SymbolTimeframeSelect';
import ConfidenceBar from './ConfidenceBar';
import MiniChart from './MiniChart';

export default function Dashboard({ symbol, timeframe, setSymbol, setTimeframe }) {
  const [health, setHealth]     = useState(null);
  const [ohlcv, setOhlcv]       = useState([]);
  const [signal, setSignal]     = useState(null);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState('');

  useEffect(() => {
    getHealth().then(r => setHealth(r.data)).catch(() => {});
  }, []);

  useEffect(() => {
    setError('');
    setLoading(true);
    Promise.all([
      getForexData({ symbol, timeframe, days_back: 7 }),
      generateSignals({ symbol, timeframe, days_back: 14, include_rl: true }),
    ])
      .then(([dataRes, sigRes]) => {
        setOhlcv(dataRes.data.data || []);
        setSignal(sigRes.data);
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [symbol, timeframe]);

  const latest = ohlcv.length ? ohlcv[ohlcv.length - 1] : null;
  const prev   = ohlcv.length > 1 ? ohlcv[ohlcv.length - 2] : null;
  const change = latest && prev
    ? ((latest.close - prev.close) / prev.close * 100).toFixed(4)
    : null;

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <div className="page-controls">
          <SymbolTimeframeSelect symbol={symbol} timeframe={timeframe} setSymbol={setSymbol} setTimeframe={setTimeframe} />
        </div>
      </div>

      {/* Status bar */}
      {health && (
        <div className="dashboard-status-bar">
          <StatusDot label="API"      ok={health.status === 'ok'} />
          <StatusDot label="Agents"   ok={health.agents_available} />
          <StatusDot label="InfluxDB" ok={health.influx_available} />
          <StatusDot label="Postgres" ok={health.psycopg2_available} />
        </div>
      )}

      {error && <div className="alert alert-error">{error}</div>}
      {loading && <div className="spinner" />}

      {!loading && (
        <>
          {/* KPI row */}
          <div className="kpi-row">
            <KPICard title="Symbol"    value={symbol} />
            <KPICard title="Last Ask"  value={latest ? latest.close.toFixed(5) : '—'} />
            <KPICard title="1-Bar Chg" value={change !== null ? `${change > 0 ? '+' : ''}${change}%` : '—'} colored={change} />
            <KPICard title="High"      value={latest ? latest.high.toFixed(5) : '—'} />
            <KPICard title="Low"       value={latest ? latest.low.toFixed(5) : '—'} />
            <KPICard title="Bars"      value={ohlcv.length} />
          </div>

          {/* Chart + Signal side-by-side */}
          <div className="dashboard-grid">
            <div className="card" style={{ gridColumn: 'span 2' }}>
              <p className="card-title">Price Chart — {symbol} {timeframe}</p>
              <MiniChart data={ohlcv} height={280} />
            </div>

            {signal && (
              <div className="card signal-summary-card">
                <p className="card-title">Live Signal</p>
                <SignalSummary signal={signal} />
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

/* ── sub-components ── */
function StatusDot({ label, ok }) {
  return (
    <span className={`status-dot ${ok ? 'ok' : 'fail'}`}>
      <span className="dot" />{label}
    </span>
  );
}

function KPICard({ title, value, colored }) {
  let cls = '';
  if (colored !== undefined && colored !== null) {
    cls = Number(colored) > 0 ? 'positive' : Number(colored) < 0 ? 'negative' : '';
  }
  return (
    <div className="card kpi-card">
      <p className="card-title">{title}</p>
      <p className={`kpi-value ${cls}`}>{value}</p>
    </div>
  );
}

function SignalSummary({ signal }) {
  const dir = signal.direction;
  const cls = dir === 'BUY' ? 'badge-buy' : dir === 'SELL' ? 'badge-sell' : 'badge-hold';
  const conf = signal.confidence || 0;

  return (
    <div className="signal-summary">
      <div className="signal-direction">
        <span className={`badge ${cls}`}>{dir}</span>
      </div>
      <div className="signal-conf">
        <span className="conf-label">Confidence</span>
        <ConfidenceBar confidence={conf} />
        <span className="conf-pct">{(conf * 100).toFixed(1)}%</span>
      </div>
      {signal.ensemble_signal && (
        <div className="signal-agent-row">
          <span className="agent-label">Ensemble</span>
          <span>{signal.ensemble_signal.direction}</span>
          <span>{(signal.ensemble_signal.confidence * 100).toFixed(1)}%</span>
        </div>
      )}
      {signal.rl_signal && (
        <div className="signal-agent-row rl">
          <span className="agent-label">RLM</span>
          <span>{signal.rl_signal.direction}</span>
          <span>{(signal.rl_signal.confidence * 100).toFixed(1)}%</span>
        </div>
      )}
      <p className="signal-reasoning">{signal.ensemble_signal?.reasoning || ''}</p>
    </div>
  );
}
