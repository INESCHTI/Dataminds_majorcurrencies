import React from 'react';

export default function ConfidenceBar({ confidence }) {
  const pct = Math.min(100, Math.max(0, (confidence || 0) * 100));
  const cls = pct >= 70 ? 'high' : pct >= 40 ? 'medium' : 'low';
  return (
    <div className="conf-bar-wrap" style={{ margin: '6px 0' }}>
      <div className={`conf-bar ${cls}`} style={{ width: `${pct}%` }} />
    </div>
  );
}
