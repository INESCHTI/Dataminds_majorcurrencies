# FX Alpha Frontend — Next.js 16 Trading Dashboard

<div align="center">

![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-5.3-3178C6?logo=typescript)
![Tailwind](https://img.shields.io/badge/Tailwind-4-06B6D4?logo=tailwindcss)
![shadcn/ui](https://img.shields.io/badge/shadcn%2Fui-latest-000000)

**Modern React frontend for AI-powered forex trading platform**

</div>

---

## 🎯 Overview

The FX Alpha Frontend is a **production-grade Next.js 16** application that provides:

- 🎨 **Animated Landing Page** — Light pillar & fluid cursor effects
- 🔐 **Authentication** — NextAuth with credentials provider
- 📊 **35+ Dashboard Pages** — Trading, analytics, ML agents, monitoring
- 🤖 **ML Agents UI** — Real-time ML predictions with risk margins
- 🌙 **Dark Theme** — Professional trading aesthetic
- ⚡ **FastAPI Integration** — React Query for efficient data fetching

---

## 🛠️ Technology Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 16.1.6 | React framework with App Router |
| **React** | 19.2.3 | UI library |
| **TypeScript** | 5.x | Type safety |
| **Tailwind CSS** | 4.x | Utility-first styling |
| **shadcn/ui** | latest | Accessible UI components |
| **TanStack Query** | 5.90+ | Server state management |
| **Framer Motion** | 12.35+ | Animations |
| **Recharts** | 3.7+ | Data visualization |
| **Lucide React** | 0.575+ | Icons |
| **NextAuth.js** | 4.24+ | Authentication |
| **Prisma** | 5.22 | Database ORM |

---

## 📁 Project Structure

```
frontend/
├── src/
│   ├── app/                          # Next.js App Router
│   │   ├── (auth)/                   # Auth route group
│   │   │   ├── login/page.tsx        # Login page
│   │   │   └── register/page.tsx     # Registration page
│   │   │
│   │   ├── (dashboard)/              # Dashboard route group (protected)
│   │   │   ├── dashboard/page.tsx    # Main dashboard
│   │   │   ├── trading/page.tsx     # Trading interface
│   │   │   ├── analytics/page.tsx    # Performance analytics
│   │   │   ├── ml-agents/page.tsx    # 🤖 ML Agents (NEW)
│   │   │   ├── agents/page.tsx       # Agent status
│   │   │   ├── monitoring/page.tsx   # System health
│   │   │   ├── reports/page.tsx      # Tactical reports
│   │   │   ├── backtesting/page.tsx  # Backtesting UI
│   │   │   ├── settings/page.tsx     # User settings
│   │   │   ├── llm-analysis/page.tsx # LLM insights
│   │   │   ├── pattern-recognition/  # Pattern detection
│   │   │   ├── rl-optimization/      # RL optimization
│   │   │   ├── multi-timezone/       # Multi-timezone view
│   │   │   ├── mcp/page.tsx          # MCP integration
│   │   │   ├── features/page.tsx     # Feature showcase
│   │   │   ├── advanced-dashboard/   # Advanced charts
│   │   │   ├── advanced-features/    # Feature testing
│   │   │   ├── realtime-dashboard/   # Real-time data
│   │   │   └── test-page/page.tsx    # Development testing
│   │   │
│   │   ├── api/                      # Next.js API routes
│   │   │   ├── auth/[...nextauth]/   # NextAuth configuration
│   │   │   └── mcp/                  # MCP API routes
│   │   │
│   │   ├── page.tsx                  # 🏠 Landing page (animated)
│   │   ├── layout.tsx                # Root layout
│   │   └── globals.css               # Global styles
│   │
│   ├── components/                   # React Components
│   │   ├── ui/                       # shadcn/ui primitives
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── tabs.tsx
│   │   │   ├── skeleton.tsx
│   │   │   └── ... (50+ components)
│   │   │
│   │   ├── LightPillar.jsx           # ✨ Landing animation
│   │   ├── SplashCursor.jsx          # 🌊 Fluid cursor effect
│   │   ├── ParticleBackground.tsx    # Particle animation
│   │   ├── Navbar.tsx                # Navigation bar
│   │   ├── Sidebar.tsx               # Dashboard sidebar
│   │   ├── SignalCard.tsx            # Trading signal display
│   │   ├── EnsembleForecastPanel.tsx # Forecast visualization
│   │   ├── TacticalReport.tsx        # Report component
│   │   ├── AgentStatus.tsx           # Agent health monitor
│   │   ├── ChartComponent.tsx        # Recharts wrapper
│   │   └── ... (60+ components)
│   │
│   ├── hooks/                        # Custom React Hooks
│   │   ├── useFastAPI.ts             # FastAPI integration
│   │   ├── useSignals.ts             # Signal fetching
│   │   └── use-toast.ts              # Toast notifications
│   │
│   ├── lib/                          # Utilities
│   │   ├── api.ts                    # Django API client
│   │   ├── fastapi.ts                # FastAPI client
│   │   ├── auth.ts                   # Auth helpers
│   │   ├── prisma.ts                 # Prisma client
│   │   └── utils.ts                  # Utility functions
│   │
│   ├── types/                        # TypeScript Types
│   │   ├── index.ts                  # Shared types
│   │   └── fastapi.ts                # FastAPI API types
│   │
│   └── middleware.ts                 # Next.js middleware (auth)
│
├── public/                           # Static assets
│   ├── logo.png
│   └── ...
│
├── .env                              # Environment variables
├── .env.local                        # Local environment
├── next.config.ts                    # Next.js configuration
├── tailwind.config.ts                # Tailwind configuration
├── components.json                   # shadcn/ui config
├── package.json                      # Dependencies
└── tsconfig.json                     # TypeScript config
```

---

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ 
- npm 9+ or yarn/pnpm
- Backend running (Django on :8000, FastAPI on :8001)

### Installation

```bash
# Navigate to frontend directory
cd fx-alpha-platform/frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
```

### Environment Variables

Create `.env.local`:

```env
# Backend APIs
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_FASTAPI_URL=http://localhost:8001
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# NextAuth
NEXTAUTH_SECRET=your-secret-key-here
NEXTAUTH_URL=http://localhost:3000

# Database (Prisma)
DATABASE_URL="postgresql://user:pass@localhost:5432/fxalpha"
```

### Development Server

```bash
npm run dev
```

Open http://localhost:3000

### Production Build

```bash
npm run build
npm run start
```

---

## 📱 Page Reference

### Public Pages

| Route | Description | Features |
|-------|-------------|----------|
| `/` | **Landing Page** | Light pillar animation, splash cursor, CTA buttons |

### Authentication

| Route | Description |
|-------|-------------|
| `/login` | Email/password login with NextAuth |
| `/register` | User registration with validation |

### Dashboard Pages (Protected)

| Route | Description | Key Features |
|-------|-------------|--------------|
| `/dashboard` | **Main Dashboard** | Overview, KPIs, quick actions |
| `/trading` | **Trading Interface** | Signal display, order placement |
| `/ml-agents` | **🤖 ML Agents** | LSTM, XGBoost, Risk metrics with real margins |
| `/analytics` | **Performance Analytics** | Charts, win rate, P&L analysis |
| `/agents` | **Agent Status** | Health monitoring, agent metrics |
| `/monitoring` | **System Monitoring** | Drift detection, safety rules |
| `/reports` | **Tactical Reports** | LLM-generated trading insights |
| `/backtesting` | **Backtesting** | Walk-forward testing results |
| `/llm-analysis` | **LLM Insights** | Natural language explanations |
| `/pattern-recognition` | **Patterns** | Technical pattern detection |
| `/rl-optimization` | **RL Optimization** | Reinforcement learning results |
| `/multi-timezone` | **Multi-Timezone** | Trading sessions view |
| `/mcp` | **MCP Integration** | MT5 connector status |
| `/settings` | **Settings** | User preferences, account |
| `/advanced-dashboard` | **Advanced Charts** | Technical indicators display |
| `/features` | **Features** | Feature showcase/testing |

---

## 🤖 ML Agents Page (`/ml-agents`)

The crown jewel of the frontend — displays real-time ML predictions with dynamic risk margins.

### Features

- **Tabbed Interface** — 4 tabs: Fusion, LSTM, Macro, Risk
- **Real-Time Signals** — Fetched via TanStack Query
- **Risk Margin Cards** — Dynamic SL/TP calculations
- **Dark Theme** — Professional trading aesthetic
- **Error Handling** — Retry buttons, loading states

### Risk Margin Display

Every signal shows calculated risk parameters:

```
┌─────────────────────────────────────────────────────────────┐
│  🛡️ Risk Margin (BUY)                                       │
│  ┌───────┬─────────┬──────────┬─────┬────────┐             │
│  │Margin │Stop Loss│Take Profit│ R:R │Leverage│             │
│  │ 1.85% │  -1.85% │   +3.70%  │ 1:2 │  5.4x  │             │
│  └───────┴─────────┴──────────┴─────┴────────┘             │
└─────────────────────────────────────────────────────────────┘
```

### API Integration

```typescript
// hooks/useFastAPI.ts
export function useLSTMSignal(pair: string) {
  return useQuery({
    queryKey: ['lstm', pair],
    queryFn: () => fastAPI.getLSTMSignal(pair),
    refetchInterval: 30000, // 30 seconds
  });
}
```

---

## 🎨 Design System

### Colors (Dark Trading Theme)

```css
/* Primary Palette */
--slate-900: #0f172a;    /* Main background */
--slate-800: #1e293b;    /* Card backgrounds */
--slate-700: #334155;    /* Borders */
--slate-300: #cbd5e1;    /* Primary text */
--slate-100: #f1f5f9;    /* Headings */

/* Signal Colors */
--green-600: #16a34a;    /* BUY signals */
--red-600: #dc2626;      /* SELL signals */
--yellow-400: #facc15;   /* Margin/Risk */
--blue-400: #60a5fa;     /* Info/R:R */
--purple-400: #c084fc;   /* Leverage */
```

### Typography

- **Font**: System UI / Inter (sans-serif)
- **Headings**: `text-2xl font-bold text-slate-100`
- **Body**: `text-sm text-slate-300`
- **Monospace**: Tabular numbers for prices

### Components

| Component | Usage |
|-----------|-------|
| `Card` | Signal containers, metric boxes |
| `Badge` | Signal direction (BUY/SELL) |
| `Tabs` | ML Agents navigation |
| `Skeleton` | Loading states |
| `Button` | Actions, refresh, retry |
| `Separator` | Section dividers |

---

## 🔌 API Integration

### Dual Backend Setup

The frontend connects to **two backends**:

| Backend | URL | Purpose |
|---------|-----|---------|
| **Django** | `:8000` | Authentication, signals, analytics |
| **FastAPI** | `:8001` | ML agents, real-time data |

### React Query Configuration

```typescript
// hooks/useFastAPI.ts
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,    // 30 seconds
      refetchInterval: 60000,  // 1 minute
      retry: 3,
    },
  },
});
```

### Example: Fetching ML Signals

```typescript
// In a component
const { data: lstm, isLoading, error } = useLSTMSignal('EURUSD');

if (isLoading) return <LoadingSkeleton />;
if (error) return <ErrorState message={error.message} onRetry={refetch} />;

return (
  <Card>
    <div>Direction: {lstm.direction}</div>
    <div>Confidence: {(lstm.confidence * 100).toFixed(1)}%</div>
  </Card>
);
```

---

## 🔐 Authentication

### NextAuth Configuration

- **Provider**: Credentials (email/password)
- **Session**: JWT with 24h expiry
- **Callbacks**: Role-based access control
- **Pages**: Custom login/register UI

### Protected Routes

All `(dashboard)` routes are protected via middleware:

```typescript
// middleware.ts
export { default } from 'next-auth/middleware';
export const config = {
  matcher: ['/dashboard/:path*', '/trading', '/ml-agents', ...]
};
```

---

## 🧪 Development

### Available Scripts

```bash
npm run dev         # Development server (Turbopack)
npm run build       # Production build
npm run start       # Production server
npm run lint        # ESLint check
```

### Code Organization Rules

1. **Pages** → `src/app/(route-group)/page.tsx`
2. **Components** → `src/components/ComponentName.tsx`
3. **Hooks** → `src/hooks/useHookName.ts`
4. **Types** → `src/types/file.ts`
5. **API** → `src/lib/api.ts` or `src/lib/fastapi.ts`

### Adding a New Page

1. Create folder: `src/app/(dashboard)/new-page/`
2. Add `page.tsx` with default export
3. Update sidebar navigation
4. Add route to middleware matcher if protected

---

## 📦 Key Dependencies

### Core
- `next` — Framework
- `react` — UI library
- `typescript` — Type safety

### Styling
- `tailwindcss` — CSS framework
- `class-variance-authority` — Component variants
- `tailwind-merge` — Class merging

### Data Fetching
- `@tanstack/react-query` — Server state

### UI Components
- `lucide-react` — Icons
- `recharts` — Charts
- `framer-motion` — Animations

### Auth
- `next-auth` — Authentication
- `@auth/prisma-adapter` — Database adapter

### Database
- `@prisma/client` — ORM

---

## 🚀 Deployment

### Build Output

```bash
npm run build
```

Output: `.next/` folder with optimized assets.

### Environment Variables for Production

```env
NEXT_PUBLIC_API_URL=https://api.fxalpha.com
NEXT_PUBLIC_FASTAPI_URL=https://ml.fxalpha.com
NEXTAUTH_SECRET=<strong-random-secret>
NEXTAUTH_URL=https://fxalpha.com
```

### Recommended Platforms

- **Vercel** — Optimal for Next.js
- **Netlify** — Static + SSR support
- **Self-hosted** — Docker container

---

## 📝 Notes

### Text Language
All user-facing text is in **English** for consistency.

### Performance
- Uses Next.js 16 Turbopack for fast HMR
- React Query for efficient caching
- Lazy loading for heavy components

### Accessibility
- shadcn/ui primitives are accessible
- Keyboard navigation supported
- ARIA labels where needed

---

## 👥 Team

**Frontend Development** — Team DATAMINDS
- Next.js 16 + React 19 implementation
- ML Agents UI integration
- Real-time data visualization

---

## 📄 License

Proprietary — Esprit PI 4DS11 2025-2026

---

<div align="center">

**Made with ⚡ Next.js 16 + React 19**

*Team DATAMINDS — Major Currencies Trading Platform*

</div>
