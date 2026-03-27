import React, { useState } from 'react';
import { generateSignals, getSignalHistory, trainRL } from '../services/api';
import SymbolTimeframeSelect from './SymbolTimeframeSelect';
import ConfidenceBar from './ConfidenceBar';
import ReactMarkdown from 'react-markdown';

export default function SignalsPage({ symbol, timeframe, setSymbol, setTimeframe }) {
  const [signal, setSignal]       = useState(null);
  const [history, setHistory]     = useState([]);
  const [loading, setLoading]     = useState(false);
  const [training, setTraining]   = useState(false);
  const [error, setError]         = useState('');
  const [showAI, setShowAI]       = useState(false);
  const [daysBack, setDays]       = useState(14);

  const fetchSignal = (withAI = false) => {
    setError('');
    setLoading(true);
    setShowAI(withAI);
    generateSignals({
      symbol, timeframe,
      days_back: daysBack,
      include_rl: true,
      include_langchain: withAI,
      session_id: `signals-${symbol}`,
    })
      .then(r => {
        setSignal(r.data);
        // also refresh history
        getSignalHistory({ symbol, limit: 20 }).then(h => setHistory(h.data.signals || []));
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  };

  const handleTrainRL = () => {
    setTraining(true);
    trainRL({ symbol, timeframe, days_back: 90, episodes: 50 })
      .then(r => alert(`RL trained: ${r.data.episodes} episodes on ${r.data.symbol}`))
      .catch(e => alert('Training error: ' + e.message))
      .finally(() => setTraining(false));
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Signals</h1>
        <div className="page-controls">
          <SymbolTimeframeSelect symbol={symbol} timeframe={timeframe} setSymbol={setSymbol} setTimeframe={setTimeframe} />
          <select value={daysBack} onChange={e => setDays(Number(e.target.value))}>
            {[7, 14, 30, 60].map(d => <option key={d} value={d}>{d}d data</option>)}
          </select>
          <button className="btn-primary" onClick={() => fetchSignal(false)} disabled={loading}>
            {loading ? 'Generating…' : '⚡ Generate Signal'}
          </button>
          <button className="btn-secondary" onClick={() => fetchSignal(true)} disabled={loading}>
            🤖 Generate + AI
          </button>
          <button className="btn-danger" onClick={handleTrainRL} disabled={training}>
            {training ? 'Training…' : '🎯 Train RLM'}
          </button>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {loading && <div className="spinner" />}

      {signal && !loading && (
        <div className="signals-grid">
          {/* Combined signal */}
          <div className="card">
            <p className="card-title">Combined Signal</p>
            <SignalCard signal={signal} />
          </div>

          {/* Ensemble */}
          {signal.ensemble_signal && (
            <div className="card">
              <p className="card-title">Ensemble (Technical + Fundamental + Sentiment)</p>
              <AgentSignal s={signal.ensemble_signal} />
            </div>
          )}

          {/* RLM */}
          {signal.rl_signal && (
            <div className="card rl-card">
              <p className="card-title">RLM — Reinforcement Learning Model</p>
              <RLSignalCard s={signal.rl_signal} />
            </div>
          )}

          {/* LangChain AI explanation */}
          {signal.ai_explanation && (
            <div className="card ai-explanation-card">
              <p className="card-title">🤖 ForexAlpha AI Explanation (LangChain)</p>
              <div className="ai-text">
                <ReactMarkdown>{signal.ai_explanation}</ReactMarkdown>
              </div>
            </div>
          )}

          {/* Individual agent signals */}
          {signal.ensemble_signal?.individual_signals?.length > 0 && (
            <div className="card">
              <p className="card-title">Individual Agent Signals</p>
              <table className="signal-table">
                <thead>
                  <tr><th>Agent</th><th>Direction</th><th>Confidence</th><th>Reasoning</th></tr>
                </thead>
                <tbody>
                  {signal.ensemble_signal.individual_signals.map((s, i) => (
                    <tr key={i}>
                      <td>{s.agent_name}</td>
                      <td><DirectionBadge dir={s.direction} /></td>
                      <td>
                        <ConfidenceBar confidence={s.confidence} />
                        <small>{(s.confidence * 100).toFixed(1)}%</small>
                      </td>
                      <td className="reasoning-cell">{s.reasoning}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Signal history */}
      {history.length > 0 && (
        <div className="card" style={{ marginTop: 20 }}>
          <p className="card-title">Signal History</p>
          <table className="signal-table">
            <thead>
              <tr><th>Time</th><th>Symbol</th><th>Direction</th><th>Confidence</th><th>Agent</th></tr>
            </thead>
            <tbody>
              {history.map(h => (
                <tr key={h.id}>
                  <td>{new Date(h.timestamp).toLocaleString()}</td>
                  <td>{h.symbol}</td>
                  <td><DirectionBadge dir={h.direction} /></td>
                  <td>{(h.confidence * 100).toFixed(1)}%</td>
                  <td><small>{h.agent_name}</small></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

/* ── sub-components ── */

function DirectionBadge({ dir }) {
  const cls = dir === 'BUY' ? 'badge-buy' : dir === 'SELL' ? 'badge-sell' : 'badge-hold';
  return <span className={`badge ${cls}`}>{dir}</span>;
}

function SignalCard({ signal }) {
  const conf = signal.confidence || 0;
  return (
    <div className="signal-summary">
      <DirectionBadge dir={signal.direction} />
      <div style={{ marginTop: 12 }}>
        <span className="conf-label">Combined confidence</span>
        <ConfidenceBar confidence={conf} />
        <span className="conf-pct">{(conf * 100).toFixed(1)}%</span>
      </div>
      <small className="text-muted">{signal.timestamp}</small>
    </div>
  );
}

function AgentSignal({ s }) {
  const conf = s.confidence || 0;
  return (
    <div>
      <DirectionBadge dir={s.direction} />
      <ConfidenceBar confidence={conf} />
      <p style={{ marginTop: 8, fontSize: 12, color: 'var(--text-muted)' }}>{s.reasoning}</p>
    </div>
  );
}

function RLSignalCard({ s }) {
  return (
    <div className="rl-signal-detail">
      <div className="rl-badge-row">
        <span className="badge badge-rl-model">RLM</span>
        <DirectionBadge dir={s.direction} />
        <span className="rl-algo">{s.agent_name}</span>
      </div>
      <ConfidenceBar confidence={s.confidence || 0} />
      <p style={{ marginTop: 8, fontSize: 12, color: 'var(--text-muted)' }}>{s.reasoning}</p>
    </div>
  );
}
