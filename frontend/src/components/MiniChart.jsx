import React, { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';

export default function MiniChart({ data = [], height = 180 }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current || !data.length) return;
    containerRef.current.innerHTML = '';

    const chart = createChart(containerRef.current, {
      layout: { background: { color: '#1e293b' }, textColor: '#94a3b8' },
      grid: { vertLines: { color: '#334155' }, horzLines: { color: '#334155' } },
      rightPriceScale: { borderColor: '#334155' },
      timeScale: { borderColor: '#334155', timeVisible: true },
      width: containerRef.current.clientWidth,
      height,
    });

    const series = chart.addLineSeries({ color: '#38bdf8', lineWidth: 2 });

    const lineData = data
      .map(b => ({ time: Math.floor(new Date(b.time).getTime() / 1000), value: b.close }))
      .sort((a, b) => a.time - b.time);

    series.setData(lineData);
    chart.timeScale().fitContent();

    const handleResize = () => chart.applyOptions({ width: containerRef.current.clientWidth });
    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [data, height]);

  return <div ref={containerRef} style={{ width: '100%' }} />;
}
