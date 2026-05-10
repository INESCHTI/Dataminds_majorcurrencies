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

## Scripts

- `npm run dev` Start development server
- `npm run build` Create production build
- `npm run start` Start production server
- `npm run lint` Run ESLint

## Backend Integration

The frontend expects the backend API to be available at `http://localhost:8000`.

Recommended startup order for local development:

1. Start infrastructure with Docker from repository root.
2. Start Django backend on port 8000.
3. Start frontend on port 3000.

## Notes

- This project uses App Router route groups for organization.
- Keep all user-facing text in English for consistency.
- Landing animation components are intentionally loaded only on the landing page.
