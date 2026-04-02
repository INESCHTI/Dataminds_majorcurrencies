import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const data = [
  { name: "Mon", price: 1.08 },
  { name: "Tue", price: 1.09 },
  { name: "Wed", price: 1.10 },
  { name: "Thu", price: 1.07 },
  { name: "Fri", price: 1.11 },
];

export default function Dashboard() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">
        📊 Trading Intelligence Dashboard
      </h1>

      <div className="grid grid-cols-3 gap-6 mb-8">
        <div className="bg-slate-800 p-6 rounded-xl">
          <p className="text-gray-400 text-sm">Win Rate</p>
          <h2 className="text-2xl font-bold text-green-400">68%</h2>
        </div>

        <div className="bg-slate-800 p-6 rounded-xl">
          <p className="text-gray-400 text-sm">Sharpe Ratio</p>
          <h2 className="text-2xl font-bold text-blue-400">1.42</h2>
        </div>

        <div className="bg-slate-800 p-6 rounded-xl">
          <p className="text-gray-400 text-sm">Active Signals</p>
          <h2 className="text-2xl font-bold text-yellow-400">12</h2>
        </div>
      </div>

      <div className="bg-slate-800 p-6 rounded-xl">
        <h3 className="mb-4 text-lg">EURUSD Price Trend</h3>

        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <XAxis dataKey="name" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" />
            <Tooltip />
            <Line
              type="monotone"
              dataKey="price"
              stroke="#22c55e"
              strokeWidth={3}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}