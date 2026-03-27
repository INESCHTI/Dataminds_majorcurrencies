import React, { useState, useRef, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { sendChat } from '../services/api';
import ReactMarkdown from 'react-markdown';

export default function ChatPage({ symbol }) {
  const [sessionId]             = useState(() => uuidv4());
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `Hello! I'm **ForexAlpha AI** powered by LangChain.\n\nI can explain trading signals, analyse market conditions, and answer questions about ${symbol}.\n\nType a message below to get started.`,
    }
  ]);
  const [input, setInput]       = useState('');
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState('');
  const bottomRef               = useRef(null);

  // quick-prompt suggestions
  const suggestions = [
    `Analyse ${symbol} current trend`,
    `What factors affect ${symbol}?`,
    `Explain RSI and MACD signals`,
    `What is the RLM agent doing?`,
    `Risk management tips for forex`,
  ];

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = (text = input) => {
    if (!text.trim()) return;
    const userMsg = { role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    setError('');

    sendChat({ session_id: sessionId, message: text, symbol })
      .then(r => {
        setMessages(prev => [...prev, { role: 'assistant', content: r.data.reply }]);
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  };

  const handleKeyDown = e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="page chat-page">
      <div className="page-header">
        <h1 className="page-title">🤖 ForexAlpha AI Chat</h1>
        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
          Powered by LangChain · Session: {sessionId.slice(0, 8)}…
        </span>
      </div>

      <div className="chat-container card">
        <div className="chat-messages">
          {messages.map((m, i) => (
            <div key={i} className={`chat-bubble ${m.role}`}>
              <div className="bubble-label">{m.role === 'user' ? 'You' : 'ForexAlpha AI'}</div>
              <div className="bubble-content">
                <ReactMarkdown>{m.content}</ReactMarkdown>
              </div>
            </div>
          ))}
          {loading && (
            <div className="chat-bubble assistant">
              <div className="bubble-label">ForexAlpha AI</div>
              <div className="bubble-content typing">
                <span /><span /><span />
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Suggestions */}
        <div className="chat-suggestions">
          {suggestions.map(s => (
            <button key={s} className="suggestion-chip" onClick={() => sendMessage(s)}>
              {s}
            </button>
          ))}
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        {/* Input */}
        <div className="chat-input-row">
          <textarea
            className="chat-input"
            rows={2}
            placeholder="Ask about signals, market conditions, strategies…"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
          />
          <button
            className="btn-primary send-btn"
            onClick={() => sendMessage()}
            disabled={loading || !input.trim()}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
