import React, { useEffect, useState } from 'react';
import { getSymbols, getTimeframes } from '../services/api';

const DEFAULT_SYMBOLS = [
  'EURUSD','GBPUSD','USDJPY','USDCHF','AUDUSD',
  'USDCAD','NZDUSD','EURGBP','EURJPY','GBPJPY',
];
const DEFAULT_TFS = ['M1','M5','M15','M30','H1','H4','D1','W1'];

export default function SymbolTimeframeSelect({ symbol, timeframe, setSymbol, setTimeframe }) {
  const [symbols, setSymbols]     = useState(DEFAULT_SYMBOLS);
  const [timeframes, setTimeframes] = useState(DEFAULT_TFS);

  useEffect(() => {
    getSymbols().then(r    => setSymbols(r.data.map(s => s.symbol))).catch(() => {});
    getTimeframes().then(r => setTimeframes(r.data.map(t => t.value))).catch(() => {});
  }, []);

  return (
    <>
      <select value={symbol} onChange={e => setSymbol(e.target.value)}>
        {symbols.map(s => <option key={s} value={s}>{s}</option>)}
      </select>
      <select value={timeframe} onChange={e => setTimeframe(e.target.value)}>
        {timeframes.map(t => <option key={t} value={t}>{t}</option>)}
      </select>
    </>
  );
}
