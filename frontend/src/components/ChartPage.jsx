import React, { useEffect, useState, useRef } from 'react';
import { createChart } from 'lightweight-charts';
import { getForexData } from '../services/api';
import SymbolTimeframeSelect from './SymbolTimeframeSelect';

export default function ChartPage({ symbol, timeframe, setSymbol, setTimeframe }) {
  const [ohlcv, setOhlcv]     = useState([]);
  const [daysBack, setDays]   = useState(30);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState('');
  const chartRef              = useRef(null);
  const containerRef          = useRef(null);

  useEffect(() => {
    setError('');
    setLoading(true);
    getForexData({ symbol, timeframe, days_back: daysBack })
      .then(r => setOhlcv(r.data.data || []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [symbol, timeframe, daysBack]);

  useEffect(() => {
    if (!containerRef.current || !ohlcv.length) return;
    containerRef.current.innerHTML = '';

    const chart = createChart(containerRef.current, {
      layout: { background: { color: '#1e293b' }, textColor: '#94a3b8' },
      grid: { vertLines: { color: '#334155' }, horzLines: { color: '#334155' } },
      crosshair: { mode: 1 },
      rightPriceScale: { borderColor: '#334155' },
      timeScale: { borderColor: '#334155', timeVisible: true },
      width: containerRef.current.clientWidth,
      height: 420,
    });

    chartRef.current = chart;

    // Candles
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#22c55e', downColor: '#ef4444',
      borderUpColor: '#22c55e', borderDownColor: '#ef4444',
      wickUpColor: '#22c55e', wickDownColor: '#ef4444',
    });

    const candleData = ohlcv.map(b => ({
      time: Math.floor(new Date(b.time).getTime() / 1000),
      open: b.open, high: b.high, low: b.low, close: b.close,
    })).sort((a, b) => a.time - b.time);

    candleSeries.setData(candleData);

    // Volume
    const volSeries = chart.addHistogramSeries({
      color: '#38bdf8',
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
    });
    chart.priceScale('volume').applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } });

    const volData = ohlcv.map(b => ({
      time: Math.floor(new Date(b.time).getTime() / 1000),
      value: b.volume,
      color: b.close >= b.open ? 'rgba(34,197,94,.4)' : 'rgba(239,68,68,.4)',
    })).sort((a, b) => a.time - b.time);
    volSeries.setData(volData);

    chart.timeScale().fitContent();

    const handleResize = () => chart.applyOptions({ width: containerRef.current.clientWidth });
    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [ohlcv]);

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Charts</h1>
        <div className="page-controls">
          <SymbolTimeframeSelect symbol={symbol} timeframe={timeframe} setSymbol={setSymbol} setTimeframe={setTimeframe} />
          <select value={daysBack} onChange={e => setDays(Number(e.target.value))}>
            {[7, 14, 30, 60, 90].map(d => <option key={d} value={d}>{d}d</option>)}
          </select>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {loading && <div className="spinner" />}

      <div className="card">
        <p className="card-title">{symbol} / {timeframe} — Candlestick + Volume</p>
        {!loading && <div ref={containerRef} style={{ width: '100%' }} />}
      </div>
    </div>
  );
}
