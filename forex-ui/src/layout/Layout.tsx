import { Link } from "react-router-dom";
import { BarChart3, Newspaper, Globe, CalendarDays } from "lucide-react";

export default function Layout({ children }: any) {
  return (
    <div className="flex min-h-screen bg-[#0f172a] text-white">

      {/* Sidebar */}
      <aside className="w-64 bg-[#111827] p-6 border-r border-slate-800">
        <h2 className="text-xl font-bold mb-8">🔥 ALPHAVAULT</h2>

        <nav className="flex flex-col gap-4 text-sm">
          <Link to="/" className="flex items-center gap-2 hover:text-green-400">
            <BarChart3 size={16} /> Dashboard
          </Link>

          <Link to="/macro" className="flex items-center gap-2 hover:text-green-400">
            <Globe size={16} /> Macro
          </Link>

          <Link to="/news" className="flex items-center gap-2 hover:text-green-400">
            <Newspaper size={16} /> News
          </Link>

          <Link to="/calendar" className="flex items-center gap-2 hover:text-green-400">
            <CalendarDays size={16} /> Calendar
          </Link>
        </nav>
      </aside>

      {/* Content */}
      <main className="flex-1 p-10">
        {children}
      </main>
    </div>
  );
}