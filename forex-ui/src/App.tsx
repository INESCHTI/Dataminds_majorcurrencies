import { useEffect, useState } from "react";

type Signal = {
  pair: string;
  signal: string;
  confidence: number;
  reason: string;
};

function SignalCard({ pair, signal, confidence, reason }: Signal) {
  const signalColor =
    signal === "BUY"
      ? "text-accent"
      : signal === "SELL"
      ? "text-danger"
      : "text-yellow-400";

  return (
    <div className="bg-card p-6 rounded-2xl shadow-lg border border-slate-700">
      <h3 className="text-xl font-semibold mb-2">{pair}</h3>

      <p className="mb-2">
        <span className="font-semibold">Signal:</span>{" "}
        <span className={`font-bold ${signalColor}`}>
          {signal}
        </span>
      </p>

      <p className="mb-2 text-sm text-gray-400">
        Confidence: {confidence}%
      </p>

      <p className="text-sm text-gray-300">
        {reason}
      </p>
    </div>
  );
}

export default function App() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fake: Signal[] = [
      { pair: "EURUSD", signal: "BUY", confidence: 72, reason: "RSI oversold + macro support" },
      { pair: "USDJPY", signal: "HOLD", confidence: 55, reason: "Mixed momentum + event risk" },
      { pair: "GBPUSD", signal: "SELL", confidence: 66, reason: "Bear trend + negative sentiment" },
    ];

    setSignals(fake);
    setLoading(false);
  }, []);

  return (
    <div className="min-h-screen p-10">
      <h1 className="text-3xl font-bold mb-2">
        🔥 Dark Trading Dashboard
      </h1>

      <p className="text-gray-400 mb-8">
        Market + Macro + News + Calendar Signals
      </p>

      {loading ? (
        <p>Loading...</p>
      ) : (
        <div className="grid md:grid-cols-3 gap-6">
          {signals.map((s) => (
            <SignalCard key={s.pair} {...s} />
          ))}
        </div>
      )}
    </div>
  );
}