import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import SignalsPage from './components/SignalsPage';
import ChartPage from './components/ChartPage';
import ChatPage from './components/ChatPage';
import './App.css';

export default function App() {
  const [symbol, setSymbol] = useState('EURUSD');
  const [timeframe, setTimeframe] = useState('H1');

  return (
    <Router>
      <div className="app-layout">
        <Sidebar />
        <main className="app-main">
          <Routes>
            <Route path="/"          element={<Dashboard symbol={symbol} timeframe={timeframe} setSymbol={setSymbol} setTimeframe={setTimeframe} />} />
            <Route path="/chart"     element={<ChartPage symbol={symbol} timeframe={timeframe} setSymbol={setSymbol} setTimeframe={setTimeframe} />} />
            <Route path="/signals"   element={<SignalsPage symbol={symbol} timeframe={timeframe} setSymbol={setSymbol} setTimeframe={setTimeframe} />} />
            <Route path="/chat"      element={<ChatPage symbol={symbol} />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

function Sidebar() {
  const links = [
    { to: '/',        icon: '📊', label: 'Dashboard' },
    { to: '/chart',   icon: '📈', label: 'Charts' },
    { to: '/signals', icon: '⚡', label: 'Signals' },
    { to: '/chat',    icon: '🤖', label: 'AI Chat' },
  ];
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <span className="logo-icon">₿</span>
        <span className="logo-text">ForexAlpha</span>
      </div>
      <nav className="sidebar-nav">
        {links.map(l => (
          <NavLink key={l.to} to={l.to} end={l.to === '/'} className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
            <span className="nav-icon">{l.icon}</span>
            <span>{l.label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-footer">
        <span className="badge-rl">RLM</span>
        <span className="badge-lc">LangChain</span>
      </div>
    </aside>
  );
}
