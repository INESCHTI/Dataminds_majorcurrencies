# FX Alpha Platform — Complete Project Documentation

<div align="center">

![FX Alpha](https://img.shields.io/badge/FX%20Alpha-V2%20Production-blue)
![Python](https://img.shields.io/badge/python-3.13-blue.svg)
![Django](https://img.shields.io/badge/django-6.0-green.svg)
![Next.js](https://img.shields.io/badge/next.js-16-black.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)
![HuggingFace](https://img.shields.io/badge/HuggingFace-flan--t5--base-yellow.svg)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)]()

**AI-Powered Multi-Agent Forex Trading Platform with Real-Time Risk Management**

[Architecture](#architecture) • [Features](#features) • [ML Agents](#ml-agents) • [Installation](#installation) • [API](#api-reference) • [Contributors](#contributors)

</div>

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [ML Agents System](#ml-agents-system)
5. [Risk Management](#risk-management)
6. [Frontend Features](#frontend-features)
7. [Installation Guide](#installation-guide)
8. [API Reference](#api-reference)
9. [Database Schema](#database-schema)
10. [Project Structure](#project-structure)
11. [Contributors](#contributors)
12. [License](#license)

---

## 🎯 Project Overview

**FX Alpha Platform** is a production-grade forex trading intelligence system developed by **Team DATAMINDS** (Esprit PI 4DS11 2025-2026). The platform combines deterministic trading algorithms with LLM-powered explainability to generate actionable trading signals.

### Key Achievements

| Feature | Status | Description |
|---------|--------|-------------|
| **Multi-Agent System** | ✅ Complete | 4 specialized agents with weighted voting |
| **ML Agents Integration** | ✅ Complete | LSTM, XGBoost, HMM, VaR models |
| **Real-Time Risk Margins** | ✅ Complete | Dynamic SL/TP based on volatility |
| **FastAPI Backend** | ✅ Complete | High-performance async API |
| **Next.js Frontend** | ✅ Complete | Modern React dashboard |
| **Real Data Pipeline** | ✅ Complete | FRED, MT5, News integration |
| **Cross-Pair Analysis** | ✅ Complete | 6 major currency correlations |
| **Backtesting Engine** | ✅ Complete | Walk-forward + Kelly Criterion |

### Supported Currency Pairs

- **EURUSD** (Major)
- **GBPUSD** (Major)
- **USDJPY** (Major)
- **USDCHF** (Major)
- **EURGBP** (Cross)
- **EURJPY** (Cross)

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND LAYER (Next.js 16)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │   Landing    │  │   Dashboard  │  │   ML Agents  │  │    Reports      │  │
│  │    Page      │  │   (Trading)  │  │    (NEW)     │  │   (Analytics)   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────────┘  │
│                                                                             │
│  Stack: React 19 · TypeScript · TanStack Query · Tailwind · shadcn/ui      │
│  Port: 3000                                                                 │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │ REST API + WebSocket
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY (Dual Stack)                          │
│                                                                             │
│  ┌─────────────────────┐    ┌─────────────────────┐                        │
│  │   Django REST API   │    │   FastAPI (Async)   │                        │
│  │   Port: 8000        │    │   Port: 8001        │                        │
│  │   /api/v2/...       │    │   /agents/...       │                        │
│  └─────────────────────┘    └─────────────────────┘                        │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SIGNAL LAYER (Multi-Agent)                          │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    CoordinatorAgentV2 (Meta-Coordinator)              │   │
│  │                         Weighted Voting System                        │   │
│  └───────────┬──────────────┬──────────────┬──────────────┬────────────┘   │
│              │              │              │              │              │
│  ┌───────────▼──┐  ┌────────▼────┐  ┌──────▼───────┐  ┌────▼─────────┐     │
│  │  Technical   │  │   Macro     │  │  Sentiment   │  │ Geopolitical │     │
│  │   Agent V2   │  │  Agent V2   │  │  Agent V2    │  │   Agent V2   │     │
│  │     40%      │  │    35%      │  │    25%       │  │     NEW      │     │
│  └──────────────┘  └─────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ML/AI LAYER (Advanced Models)                       │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │    LSTM      │  │   XGBoost    │  │     HMM      │  │     VaR      │  │
│  │  Technical   │  │    Macro     │  │   Regime     │  │     Risk     │  │
│  │   Agent      │  │   Agent      │  │  Classifier  │  │  Management  │  │
│  │  (Deep NN)   │  │(Grad Boost)  │  │ (Markov)     │  │  (Risk Mgmt) │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                      │
│  │   Prophet    │  │    Kats      │  │   Ensemble   │                      │
│  │  Forecast    │  │   Forecast   │  │   Forecast   │                      │
│  └──────────────┘  └──────────────┘  └──────────────┘                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER (Multi-Source)                           │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │    MT5       │  │    FRED      │  │    News      │  │    CFTC      │  │
│  │   OHLCV      │  │   Macro      │  │  Sentiment   │  │    COT       │  │
│  │  (via MCP)   │  │    Data      │  │    NLP       │  │  Reports     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                                             │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
            ┌──────────┐  ┌──────────┐  ┌──────────┐
            │InfluxDB  │  │PostgreSQL│  │  Redis   │
            │  2.7     │  │   15     │  │   7      │
            │(OHLCV)   │  │(Macro)   │  │(Cache)   │
            └──────────┘  └──────────┘  └──────────┘
```

---

## 🛠️ Technology Stack

### Backend

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Core API** | Django + DRF | 6.0 | Main REST API |
| **Async API** | FastAPI | 0.104+ | ML agent endpoints |
| **ML Framework** | TensorFlow/Keras | 2.13+ | LSTM models |
| **ML Framework** | XGBoost | 2.0+ | Gradient boosting |
| **ML Framework** | scikit-learn | 1.3+ | HMM, preprocessing |
| **NLP** | HuggingFace Transformers | 4.35+ | FinBERT sentiment |
| **Time Series** | Prophet | 1.1+ | Forecasting |
| **Database** | PostgreSQL | 15 | Relational data |
| **Time Series DB** | InfluxDB | 2.7 | OHLCV candles |
| **Cache** | Redis | 7 | Session + cache |
| **WebSocket** | Django Channels | 4.0+ | Real-time updates |

### Frontend

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Framework** | Next.js | 16 | React framework |
| **UI Library** | React | 19 | Component library |
| **Styling** | Tailwind CSS | 3.4+ | Utility CSS |
| **Components** | shadcn/ui | latest | UI components |
| **State Management** | TanStack Query | 5.0+ | Server state |
| **Charts** | Recharts | 2.10+ | Data visualization |
| **Icons** | Lucide React | 0.294+ | Icon library |
| **Auth** | NextAuth.js | 4.24+ | Authentication |
| **Types** | TypeScript | 5.3+ | Type safety |

---

## 🤖 ML Agents System

### 1. LSTM Technical Agent (`ai_layer/lstm_technical_agent.py`)

**Purpose**: Deep learning predictions from OHLCV price data

**Features**:
- Multi-layer LSTM with attention mechanism
- Technical indicator features (RSI, MACD, Bollinger)
- Sequence prediction (60-period lookback)
- Confidence-based uncertainty estimation

**API Endpoint**:
```bash
POST /agents/lstm/signal?pair=EURUSD
```

**Response**:
```json
{
  "success": true,
  "direction": "BUY",
  "confidence": 0.78,
  "predicted_return": 0.012,
  "probability_up": 0.65,
  "probability_down": 0.35,
  "model_uncertainty": 0.15,
  "risk_margins": {
    "margin_pct": 1.85,
    "stop_loss_pct": 1.85,
    "take_profit_pct": 3.70,
    "risk_reward": 2.0,
    "position_size_pct": 89,
    "recommended_leverage": 5.4
  }
}
```

### 2. XGBoost Macro Agent (`ai_layer/xgboost_macro_agent.py`)

**Purpose**: Gradient boosting on macroeconomic indicators

**Features**:
- Interest rate differential analysis
- Inflation differential (CPI)
- GDP surprise indices
- PMI and employment data
- SHAP feature importance

**API Endpoint**:
```bash
POST /agents/xgboost-macro/signal?pair=EURUSD
POST /agents/xgboost-macro/train?pair=EURUSD
```

**Response**:
```json
{
  "success": true,
  "direction": "BUY",
  "confidence": 0.82,
  "expected_return": 0.015,
  "macro_factors": {
    "rate_differential": 0.75,
    "inflation_diff": -0.4,
    "gdp_surprise": 0.1
  },
  "feature_importance": {
    "rate_differential": 0.45,
    "inflation_diff": 0.30
  }
}
```

### 3. XGBoost Fusion / Coordinator (`ai_layer/xgboost_coordinator.py`)

**Purpose**: Meta-learner that fuses all agent signals

**Features**:
- Weighted ensemble of agent predictions
- Agent contribution tracking
- Disagreement detection
- Regime-adjusted weighting

**API Endpoint**:
```bash
POST /fusion/xgboost?pair=EURUSD
```

### 4. HMM Regime Classifier (`ai_layer/regime_classifier.py`)

**Purpose**: Hidden Markov Model for market regime detection

**Features**:
- 3-state HMM (Bull, Bear, Sideways)
- Volatility regime identification
- Adaptive agent weighting per regime
- Confidence scoring

**API Endpoint**:
```bash
GET /agents/regime/current?pair=EURUSD
POST /agents/regime/train?pair=EURUSD
```

### 5. VaR Risk Management (`ai_layer/risk_management.py`)

**Purpose**: Portfolio risk calculation and position sizing

**Features**:
- Value at Risk (95% and 99% confidence)
- Conditional VaR (Expected Shortfall)
- Realized vs EWMA volatility
- Drawdown tracking
- Kelly Criterion position sizing

**API Endpoint**:
```bash
GET /risk/metrics?pair=EURUSD
```

**Response**:
```json
{
  "success": true,
  "var_95": 1250.50,
  "cvar_95": 1420.30,
  "realized_vol": 0.1523,
  "ewma_vol": 0.1489,
  "current_drawdown": -0.023,
  "risk_level": "MODERATE",
  "recommendation": "Normal trading conditions"
}
```

---

## 📊 Risk Management

### Real Risk Margin Calculation

Risk margins are **dynamically calculated** in real-time based on:

#### Formula Parameters

| Parameter | BUY Signal | SELL Signal | NEUTRAL |
|-----------|------------|-------------|---------|
| Base Stop Loss | 1.5% | 2.0% | 1.0% |
| Base Take Profit | 3.0% | 3.5% | 2.0% |
| Max Position Size | 100% | 80% | 50% |

#### Adjustments

```python
# Confidence adjustment (higher confidence = tighter stops)
confidence_factor = max(0.5, confidence)

# Volatility adjustment (higher vol = wider stops)
vol_adjustment = 1 + (volatility - 0.15) * 2

# Final calculations
stop_loss = base_stop * vol_adjustment / confidence_factor
take_profit = base_target * confidence_factor / vol_adjustment
risk_reward = take_profit / stop_loss
leverage = min(10, 1 / stop_loss)
```

### Risk Display

Every signal card shows:
```
┌─────────────────────────────────────────────────────────────┐
│  🛡️ Risk Margin (BUY)                                       │
│  ┌───────┬─────────┬──────────┬─────┬────────┐           │
│  │Margin │Stop Loss│Take Profit│ R:R │Leverage│           │
│  │ 1.85% │  -1.85% │   +3.70%  │ 1:2 │  5.4x  │           │
│  └───────┴─────────┴──────────┴─────┴────────┘           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎨 Frontend Features

### Pages

| Page | Route | Description |
|------|-------|-------------|
| **Landing** | `/` | Animated homepage with effects |
| **Login** | `/login` | Authentication |
| **Register** | `/register` | User registration |
| **Dashboard** | `/dashboard` | Main trading dashboard |
| **Trading** | `/trading` | Trading interface |
| **Analytics** | `/analytics` | Performance analytics |
| **Monitoring** | `/monitoring` | System health |
| **Reports** | `/reports` | Tactical reports |
| **Agents** | `/agents` | Agent status |
| **ML Agents** | `/ml-agents` | **NEW: ML predictions** |
| **Settings** | `/settings` | User settings |

### ML Agents UI (`/ml-agents`)

**Features**:
- Tabbed interface (Fusion, LSTM, Macro, Risk)
- Real-time signal cards
- Risk margin display per signal
- Dark theme (slate-800/900 backgrounds)
- Loading skeletons
- Error states with retry

**Components**:
- `EnsembleForecastPanel` - Prophet + Kats forecasts
- `TacticalReport` - Trading recommendations
- `AgentStatus` - Agent health monitoring

---

## 📦 Installation Guide

### Prerequisites

- Python 3.13+
- Node.js 18+
- Docker & Docker Compose
- Git

### 1. Clone Repository

```bash
git clone https://github.com/INESCHTI/Esprit-PI-4DS11-2526-MajorCurrencies.git
cd Esprit-PI-4DS11-2526-MajorCurrencies
git checkout mariemfersi
```

### 2. Infrastructure (Docker)

```bash
docker-compose up -d
```

Services started:
- PostgreSQL 15 (port 5432)
- InfluxDB 2.7 (port 8086)
- Redis 7 (port 6379)

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Seed initial data
python seed_all_data.py

# Start Django server (port 8000)
python manage.py runserver 0.0.0.0:8000
```

### 4. FastAPI Setup (Async API)

```bash
# In a new terminal
cd backend
python api/fastapi_app.py
```

FastAPI runs on port 8001

### 5. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend runs on http://localhost:3000

### 6. Verify Installation

```bash
# Test backend
curl http://localhost:8000/api/agents/status/

# Test FastAPI
curl http://localhost:8001/agents/status

# Test ML agents
curl -X POST "http://localhost:8001/agents/lstm/signal?pair=EURUSD"
```

---

## 📡 API Reference

### Django REST API (Port 8000)

#### Signal Generation
```bash
# Generate full signal (all agents)
POST /api/v2/signals/generate_signal/
Body: {"pair": "EURUSD"}

# Generate orchestrated signal (LLM routing)
POST /api/v2-signals/generate_orchestrated_signal/
Body: {"pair": "EURUSD", "query": "EURUSD broke resistance"}
```

#### Data Endpoints
```bash
GET /api/data/economic-calendar/
GET /api/data/technical-indicators/?pair=EURUSD
GET /api/kpis/
GET /api/analytics/performance/
```

#### Backtesting
```bash
POST /api/v2/backtesting/run_backtest/
Body: {"pair": "EURUSD", "days": 60}

POST /api/v2/backtesting/position_sizing/
Body: {"pair": "EURUSD"}
```

### FastAPI (Port 8001) — ML Agents

#### ML Agent Endpoints
```bash
# LSTM Technical Agent
POST /agents/lstm/signal?pair=EURUSD

# XGBoost Macro Agent
POST /agents/xgboost-macro/signal?pair=EURUSD

# XGBoost Fusion (Meta-learner)
POST /fusion/xgboost?pair=EURUSD

# Risk Metrics
GET /risk/metrics?pair=EURUSD

# Regime Detection
GET /agents/regime/current?pair=EURUSD

# Agent Status
GET /agents/status
```

#### Training Endpoints
```bash
# Train XGBoost Macro
POST /agents/xgboost-macro/train?pair=EURUSD

# Train XGBoost Coordinator
POST /agents/xgboost-coordinator/train?pair=EURUSD

# Train HMM Regime
POST /agents/regime/train?pair=EURUSD
```

---

## 🗄️ Database Schema

### PostgreSQL Tables

| Table | Purpose |
|-------|---------|
| `economic_calendar` | Economic events (NFP, ECB, Fed) |
| `macro_indicators` | FRED data (rates, inflation, GDP) |
| `news_articles` | Financial news with sentiment |
| `sentiment_scores` | Aggregated sentiment per pair |
| `signals` | Generated trading signals |
| `signal_logs` | Signal history for backtesting |
| `agent_performances` | Agent accuracy tracking |
| `trades` | Executed trades |
| `performance_metrics` | KPI calculations |
| `cot_reports` | CFTC COT positioning data |

### InfluxDB Measurements

| Measurement | Fields | Tags |
|-------------|--------|------|
| `ohlcv` | open, high, low, close, volume | pair, timeframe |
| `technical_indicators` | rsi, macd, bb_upper, bb_lower | pair, indicator |
| `correlations` | correlation_value | pair1, pair2 |

---

## 📁 Project Structure

```
fx-alpha-platform/
├── backend/                          # Django + FastAPI Backend
│   ├── api/                          # REST API endpoints
│   │   ├── fastapi_app.py            # FastAPI async app (ML agents)
│   │   ├── views_v2.py               # Django REST views
│   │   └── urls.py                   # URL routing
│   ├── ai_layer/                     # ML/AI Models
│   │   ├── lstm_technical_agent.py   # LSTM predictions
│   │   ├── xgboost_macro_agent.py    # XGBoost macro
│   │   ├── xgboost_coordinator.py    # Fusion meta-learner
│   │   ├── regime_classifier.py      # HMM regime detection
│   │   ├── risk_management.py        # VaR calculations
│   │   ├── time_series_forecaster.py # Prophet + Kats
│   │   ├── financial_nlp.py          # FinBERT sentiment
│   │   └── advanced_pattern_recognition.py  # Pattern detection
│   ├── signal_layer/                 # Trading Agents
│   │   ├── coordinator_agent_v2.py     # Meta-coordinator
│   │   ├── technical_agent_v2.py     # Technical analysis
│   │   ├── macro_agent_v2.py         # Macro analysis
│   │   ├── sentiment_agent_v2.py     # Sentiment analysis
│   │   ├── geopolitical_agent_v2.py  # Geopolitical risk
│   │   └── orchestrator_agent.py     # LLM query router
│   ├── data_layer/                   # Data Acquisition
│   │   ├── timeseries_loader.py      # InfluxDB OHLCV
│   │   ├── macro_data_loader.py      # FRED macro data
│   │   ├── news_loader_fixed.py      # News + sentiment
│   │   └── cot_collector.py          # CFTC COT data
│   ├── feature_layer/                # Feature Engineering
│   │   ├── technical_features.py     # 60+ indicators
│   │   ├── sentiment_features.py     # NLP features
│   │   └── cross_pair_correlations.py  # Correlation matrix
│   ├── backtesting/                  # Backtesting Engine
│   │   └── walk_forward.py           # Walk-forward testing
│   ├── monitoring/                   # System Monitoring
│   │   ├── safety_monitor.py         # Safety checks
│   │   ├── drift_detector.py         # Model drift
│   │   └── performance_tracker.py    # Performance KPIs
│   ├── core/                         # Core Utilities
│   │   ├── llm_factory_lightweight.py  # LLM management
│   │   └── database_manager.py       # Database connection
│   ├── config/                       # Django Configuration
│   └── requirements.txt              # Python dependencies
│
├── frontend/                         # Next.js Frontend
│   ├── src/
│   │   ├── app/                      # Next.js App Router
│   │   │   ├── (dashboard)/          # Dashboard pages
│   │   │   │   ├── ml-agents/        # ML Agents page
│   │   │   │   ├── trading/          # Trading interface
│   │   │   │   ├── analytics/        # Analytics page
│   │   │   │   └── ...               # Other pages
│   │   │   ├── login/                # Auth pages
│   │   │   └── page.tsx              # Landing page
│   │   ├── components/               # React Components
│   │   │   ├── ui/                   # shadcn/ui components
│   │   │   ├── EnsembleForecastPanel.tsx
│   │   │   ├── TacticalReport.tsx
│   │   │   └── ...
│   │   ├── hooks/                    # React Hooks
│   │   │   ├── useFastAPI.ts         # FastAPI integration
│   │   │   └── useSignals.ts         # Signal fetching
│   │   ├── lib/                      # Utilities
│   │   │   ├── api.ts                # API client
│   │   │   └── fastapi.ts            # FastAPI client
│   │   └── types/                    # TypeScript Types
│   │       └── fastapi.ts            # API type definitions
│   ├── package.json                  # Node dependencies
│   └── next.config.ts                # Next.js config
│
├── docker-compose.yml                # Docker services
├── README.md                         # Main documentation
└── ARCHITECTURE.md                   # Detailed architecture
```

---

## 👥 Contributors

### Team DATAMINDS — Esprit PI 4DS11 2025-2026

| Name | Role | Contributions |
|------|------|---------------|
| **Mariem Fersi** | ML Engineer | ML Agents integration, Risk margins, UI/UX, FastAPI backend |
| **Team Members** | Data Scientists | Signal agents, Data pipeline, Feature engineering |
| **Team Members** | Full-Stack Developers | Frontend, Backend API, Database design |

---

## 📄 License

**Proprietary Software** — Esprit School of Engineering

This project is developed as part of the **Projet Intégrateur (PI)** for the **4DS11** class of **2025-2026**.

**Major Currencies Trading Platform** — All rights reserved.

---

## 🙏 Acknowledgments

- **Esprit School of Engineering** — For the educational framework
- **Professors** — For guidance and mentorship
- **Open Source Community** — For the amazing tools and libraries

---

## 📞 Contact

For questions or contributions, please contact the team through:
- GitHub: [INESCHTI/Esprit-PI-4DS11-2526-MajorCurrencies](https://github.com/INESCHTI/Esprit-PI-4DS11-2526-MajorCurrencies)
- Branch: `mariemfersi`

---

<div align="center">

**Made with ❤️ by Team DATAMINDS**

*Empowering traders with AI-driven intelligence*

</div>
