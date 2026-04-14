# FX Alpha Backend — Django + FastAPI Trading Engine

<div align="center">

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![Django](https://img.shields.io/badge/Django-5.2.12-green?logo=django)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql)
![InfluxDB](https://img.shields.io/badge/InfluxDB-2.7-22ADF6?logo=influxdb)

**High-performance multi-agent forex trading backend with ML integration**

</div>

---

## 🎯 Overview

The FX Alpha Backend is a **dual-stack Python backend** combining:

- **Django + DRF** (Port 8000) — Main REST API, authentication, analytics
- **FastAPI** (Port 8001) — Async ML agents, real-time data streaming

### Key Features

| Feature | Technology | Status |
|---------|------------|--------|
| **Multi-Agent System** | Deterministic Python | ✅ Production |
| **ML Agents** | TensorFlow, XGBoost, HMM | ✅ Complete |
| **Risk Management** | VaR, GARCH, Kelly Criterion | ✅ Complete |
| **Real-time Data** | WebSocket + InfluxDB | ✅ Complete |
| **Async API** | FastAPI + Uvicorn | ✅ Complete |
| **Authentication** | Django + JWT | ✅ Complete |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY (Dual Stack)                          │
│                                                                             │
│  ┌─────────────────────────┐      ┌─────────────────────────┐                │
│  │     Django REST API     │      │     FastAPI (Async)     │                │
│  │     Port: 8000          │      │     Port: 8001          │                │
│  │                         │      │                         │                │
│  │  • Authentication       │      │  • ML Agents            │                │
│  │  • Signals (V2)        │      │  • Real-time data       │                │
│  │  • Analytics           │      │  • WebSocket streams    │                │
│  │  • Backtesting         │      │  • Async predictions    │                │
│  │  • Agent Orchestration │      │  • Risk calculations    │                │
│  └───────────┬─────────────┘      └───────────┬─────────────┘                │
└──────────────┼──────────────────────────┼──────────────────────────────────────┘
               │                          │
               ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SIGNAL LAYER (Multi-Agent)                          │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    CoordinatorAgentV2 (Meta-Coordinator)              │   │
│  │                         Weighted Voting System                        │   │
│  └───────────┬──────────────┬──────────────┬──────────────┬────────────┘   │
│              │              │              │              │                │
│  ┌───────────▼──┐  ┌────────▼────┐  ┌──────▼───────┐  ┌────▼─────────┐   │
│  │  Technical   │  │   Macro     │  │  Sentiment   │  │ Geopolitical │   │
│  │   Agent V2   │  │  Agent V2   │  │  Agent V2    │  │   Agent V2   │   │
│  │   30-40%     │  │   25-35%    │  │   20-25%     │  │    25%       │   │
│  └──────────────┘  └─────────────┘  └──────────────┘  └──────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ML/AI LAYER (Advanced Models)                       │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │     LSTM     │  │   XGBoost    │  │     HMM      │  │     VaR      │   │
│  │  Technical   │  │    Macro     │  │   Regime     │  │     Risk     │   │
│  │   Agent      │  │   Agent      │  │  Classifier  │  │  Management  │   │
│  │  (Deep NN)   │  │(Grad Boost)  │  │  (Markov)    │  │  (GARCH)     │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                      │
│  │   Prophet    │  │    Kats      │  │   Ensemble   │                      │
│  │  Forecast    │  │   Forecast   │  │   Forecast   │                      │
│  └──────────────┘  └──────────────┘  └──────────────┘                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER (Multi-Source)                           │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │     MT5      │  │     FRED     │  │     News     │  │     CFTC     │   │
│  │    OHLCV     │  │    Macro     │  │  Sentiment   │  │     COT      │   │
│  │  (via MCP)   │  │    Data      │  │    NLP       │  │  Reports     │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
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

## 📁 Project Structure

```
backend/
├── api/                              # REST API Endpoints
│   ├── fastapi_app.py                # 🚀 FastAPI async application
│   ├── views_v2.py                   # Django REST views (V2)
│   ├── urls_v2.py                    # URL routing
│   ├── urls.py                       # Legacy URLs
│   ├── mcp_views.py                  # MCP connector views
│   └── serializers.py                # DRF serializers
│
├── ai_layer/                         # 🤖 ML/AI Models
│   ├── lstm_technical_agent.py       # LSTM deep learning predictions
│   ├── xgboost_macro_agent.py        # XGBoost gradient boosting
│   ├── xgboost_coordinator.py        # Meta-learner fusion
│   ├── regime_classifier.py          # HMM regime detection
│   ├── risk_management.py            # VaR & GARCH risk models
│   ├── time_series_forecaster.py     # Prophet + Kats forecasting
│   ├── financial_nlp.py              # FinBERT sentiment analysis
│   ├── advanced_pattern_recognition.py # CNN pattern detection
│   └── ensemble_forecaster.py        # Multi-model forecasting
│
├── signal_layer/                     # 🎯 Trading Agents (V2)
│   ├── coordinator_agent_v2.py       # Meta-coordinator with weighted voting
│   ├── technical_agent_v2.py         # RSI, MACD, Bollinger rules
│   ├── macro_agent_v2.py             # Rate differentials, inflation
│   ├── sentiment_agent_v2.py          # News sentiment aggregation
│   ├── geopolitical_agent_v2.py      # Political risk analysis
│   ├── orchestrator_agent.py          # LLM query routing
│   └── base_agent.py                  # Base agent class
│
├── data_layer/                       # 📊 Data Acquisition
│   ├── timeseries_loader.py          # InfluxDB OHLCV loader
│   ├── macro_data_loader.py          # FRED economic data
│   ├── news_loader_fixed.py          # News + FinBERT sentiment
│   ├── cot_collector.py              # CFTC COT positioning
│   ├── real_market_data.py           # Real-time market data
│   └── signal_recorder.py            # Signal persistence
│
├── feature_layer/                    # 🔧 Feature Engineering
│   ├── technical_features.py         # 60+ technical indicators
│   ├── sentiment_features.py         # NLP feature extraction
│   ├── macro_features.py             # Economic indicators
│   └── cross_pair_correlations.py    # Correlation matrix
│
├── backtesting/                      # 📈 Backtesting Engine
│   └── walk_forward.py               # Walk-forward analysis
│
├── monitoring/                       # 🔍 System Monitoring
│   ├── safety_monitor.py             # Safety rules & circuit breakers
│   ├── drift_detector.py             # Model drift detection
│   ├── performance_tracker.py        # Agent performance KPIs
│   └── enhanced_monitoring.py         # Advanced monitoring
│
├── core/                             # ⚙️ Core Utilities
│   ├── llm_factory_lightweight.py     # LLM management (Flan-T5)
│   └── database_manager.py            # Database connections
│
├── analytics/                        # 📊 Analytics & Reporting
│   └── tactical_report_generator.py   # LLM report generation
│
├── acquisition/                    # 🌐 Data Acquisition
│   ├── free_data_collector.py         # Free data sources
│   ├── mt5_mcp_connector.py          # MetaTrader 5 connector
│   └── cot_collector.py              # CFTC data
│
├── mcp/                              # 🔌 MCP (Model Context Protocol)
│   └── ...                           # MCP server integration
│
├── agents/                           # 🤖 Legacy Agents
│   └── ...                           # Backward compatibility
│
├── data/                             # 📂 Data Endpoints
│   └── ...                           # Calendar, indicators
│
├── signals/                          # 📡 Signal Endpoints
│   └── ...                           # Signal generation
│
├── validation/                       # ✅ Data Validation
│   └── ...                           # Quality checks
│
├── management/                       # 🛠️ Management Commands
│   └── commands/                      # Django management
│
├── preparation/                      # 📚 Data Preparation
│   └── ...                           # Preprocessing scripts
│
├── config/                           # ⚙️ Configuration
│   ├── settings.py                    # Django settings
│   ├── urls.py                        # Root URL config
│   └── asgi.py                        # ASGI config
│
├── requirements.txt                   # 📦 Python dependencies
├── manage.py                         # 🛠️ Django CLI
└── README.md                         # 📖 This file
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- PostgreSQL 15
- InfluxDB 2.7
- Redis 7
- Docker (recommended)

### 1. Infrastructure (Docker)

```bash
# From project root
docker-compose up -d
```

Services:
- PostgreSQL: `localhost:5432`
- InfluxDB: `localhost:8086`
- Redis: `localhost:6379`

### 2. Virtual Environment

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Variables

Create `.env`:

```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key-here
DJANGO_SETTINGS_MODULE=config.settings

# Databases
DATABASE_URL=postgresql://user:pass@localhost:5432/fxalpha
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your-token
INFLUXDB_ORG=fxalpha
INFLUXDB_BUCKET=ohlcv

# Redis
REDIS_URL=redis://localhost:6379/0

# APIs
FRED_API_KEY=your-fred-key
OPENAI_API_KEY=optional-for-llm
```

### 5. Database Setup

```bash
# Run migrations
python manage.py migrate

# Seed initial data
python seed_all_data.py

# Populate real performance data
python populate_real_performance.py
```

### 6. Start Servers

**Terminal 1 — Django:**
```bash
python manage.py runserver 0.0.0.0:8000
```

**Terminal 2 — FastAPI:**
```bash
python api/fastapi_app.py
```

FastAPI runs on port 8001.

---

## 🤖 ML Agents

### 1. LSTM Technical Agent

**File:** `ai_layer/lstm_technical_agent.py`

**Purpose:** Deep learning predictions from OHLCV data

**Features:**
- Multi-layer LSTM with attention
- 60-period lookback
- Technical indicator features
- Uncertainty estimation

**Endpoint:**
```bash
POST /agents/lstm/signal?pair=EURUSD
```

**Response:**
```json
{
  "success": true,
  "direction": "BUY",
  "confidence": 0.78,
  "predicted_return": 0.012,
  "probability_up": 0.65,
  "probability_down": 0.35,
  "risk_margins": {
    "margin_pct": 1.85,
    "stop_loss_pct": 1.85,
    "take_profit_pct": 3.70,
    "risk_reward": 2.0,
    "recommended_leverage": 5.4
  }
}
```

### 2. XGBoost Macro Agent

**File:** `ai_layer/xgboost_macro_agent.py`

**Purpose:** Gradient boosting on macroeconomic data

**Features:**
- Interest rate differential analysis
- Inflation differential
- GDP, PMI, employment surprises
- SHAP feature importance

**Endpoints:**
```bash
POST /agents/xgboost-macro/signal?pair=EURUSD
POST /agents/xgboost-macro/train?pair=EURUSD
```

### 3. XGBoost Fusion (Meta-Learner)

**File:** `ai_layer/xgboost_coordinator.py`

**Purpose:** Combine all agent signals

**Features:**
- Weighted ensemble voting
- Agent contribution tracking
- Regime-adjusted weights
- Disagreement detection

**Endpoint:**
```bash
POST /fusion/xgboost?pair=EURUSD
```

### 4. HMM Regime Classifier

**File:** `ai_layer/regime_classifier.py`

**Purpose:** Market regime detection

**Features:**
- 3-state Hidden Markov Model
- Bull/Bear/Sideways classification
- Adaptive agent weighting
- Volatility regime detection

**Endpoints:**
```bash
GET /agents/regime/current?pair=EURUSD
POST /agents/regime/train?pair=EURUSD
```

### 5. VaR Risk Management

**File:** `ai_layer/risk_management.py`

**Purpose:** Portfolio risk calculation

**Features:**
- Value at Risk (95%, 99%)
- Conditional VaR (Expected Shortfall)
- GARCH volatility modeling
- Kelly Criterion position sizing
- Drawdown tracking

**Endpoint:**
```bash
GET /risk/metrics?pair=EURUSD
```

---

## 📡 API Reference

### Django REST API (Port 8000)

#### Authentication
```bash
POST /api/auth/login/
POST /api/auth/register/
POST /api/auth/logout/
```

#### Signal Generation
```bash
# Generate signal (all agents)
POST /api/v2/signals/generate_signal/
Body: {"pair": "EURUSD"}

# Orchestrated signal (LLM routing)
POST /api/v2-signals/generate_orchestrated_signal/
Body: {"pair": "EURUSD", "query": "EURUSD broke resistance"}
```

#### Data
```bash
GET /api/data/economic-calendar/
GET /api/data/technical-indicators/?pair=EURUSD
GET /api/kpis/
GET /api/analytics/performance/
GET /api/agents/status/
```

#### Backtesting
```bash
POST /api/v2/backtesting/run_backtest/
POST /api/v2/backtesting/position_sizing/
GET /api/v2/correlations/correlation_matrix/
```

### FastAPI (Port 8001)

#### ML Agents
```bash
# LSTM Technical
POST /agents/lstm/signal?pair=EURUSD

# XGBoost Macro
POST /agents/xgboost-macro/signal?pair=EURUSD

# Fusion (Meta-learner)
POST /fusion/xgboost?pair=EURUSD

# Risk Metrics
GET /risk/metrics?pair=EURUSD

# Regime Detection
GET /agents/regime/current?pair=EURUSD

# Agent Status
GET /agents/status
```

#### Training
```bash
# Train XGBoost Macro
POST /agents/xgboost-macro/train?pair=EURUSD

# Train XGBoost Coordinator
POST /agents/xgboost-coordinator/train?pair=EURUSD

# Train HMM Regime
POST /agents/regime/train?pair=EURUSD
```

---

## 🔧 Key Components

### Signal Layer (V2)

| Agent | Weight | Method | Status |
|-------|--------|--------|--------|
| TechnicalAgentV2 | 30-40% | RSI/MACD/Bollinger | ✅ Production |
| MacroAgentV2 | 25-35% | Rate differentials | ✅ Production |
| SentimentAgentV2 | 20-25% | FinBERT sentiment | ✅ Production |
| GeopoliticalAgentV2 | 25% | Political risk | ✅ Production |
| CoordinatorAgentV2 | — | Weighted voting | ✅ Production |
| OrchestratorAgent | — | LLM routing | ✅ Production |

### Deterministic Rules

**Technical Agent:**
```python
RSI < 30 → BUY (weight: 0.25)
RSI > 70 → SELL (weight: 0.25)
MACD crossover → Direction (weight: 0.30)
Bollinger Bands position (weight: 0.20)
SMA alignment (weight: 0.25)
```

**Macro Agent:**
```python
rate_diff > 0.5% → Bullish
rate_diff < -0.5% → Bearish
carry_score = rate_diff / volatility
```

---

## 📊 Risk Margin Calculation

Risk margins are **dynamically calculated** per signal:

### Formula
```python
# Base parameters by direction
if direction == 'BUY':
    base_stop = 0.015      # 1.5%
    base_target = 0.03     # 3%
elif direction == 'SELL':
    base_stop = 0.020      # 2%
    base_target = 0.035    # 3.5%

# Adjustments
confidence_factor = max(0.5, confidence)
vol_adjustment = 1 + (volatility - 0.15) * 2

# Final calculations
stop_loss = base_stop * vol_adjustment / confidence_factor
take_profit = base_target * confidence_factor / vol_adjustment
risk_reward = take_profit / stop_loss
leverage = min(10, 1 / stop_loss)
```

---

## 🗄️ Database Schema

### PostgreSQL Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `economic_calendar` | Economic events | date, event_name, currency, impact |
| `macro_indicators` | FRED data | indicator_name, value, date |
| `news_articles` | Financial news | title, content, source, published_at |
| `sentiment_scores` | Aggregated sentiment | pair, sentiment_score, confidence |
| `signals` | Trading signals | pair, direction, confidence, timestamp |
| `signal_logs` | Signal history | signal_id, outcome, pnl |
| `agent_performances` | Agent metrics | agent_name, win_rate, sharpe_ratio |
| `trades` | Executed trades | entry_price, exit_price, pnl |
| `cot_reports` | CFTC data | pair, non_commertial_long, short |

### InfluxDB Measurements

| Measurement | Fields | Tags |
|-------------|--------|------|
| `ohlcv` | open, high, low, close, volume | pair, timeframe |
| `technical_indicators` | rsi, macd, bb_upper, bb_lower | pair, indicator |

---

## 🧪 Testing

### Run Tests

```bash
# All tests
pytest

# Specific module
pytest signal_layer/test_technical_agent.py

# With coverage
pytest --cov=. --cov-report=html
```

### Manual Testing

```bash
# Test signal generation
curl -X POST "http://localhost:8000/api/v2/signals/generate_signal/" \
  -H "Content-Type: application/json" \
  -d '{"pair": "EURUSD"}'

# Test ML agent
curl -X POST "http://localhost:8001/agents/lstm/signal?pair=EURUSD"

# Test risk metrics
curl "http://localhost:8001/risk/metrics?pair=EURUSD"
```

---

## 🚀 Deployment

### Production Environment Variables

```env
DEBUG=False
SECRET_KEY=<strong-random-key>
ALLOWED_HOSTS=api.fxalpha.com,localhost

# SSL
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Production Database
DATABASE_URL=postgresql://user:pass@prod-db:5432/fxalpha

# Production Cache
REDIS_URL=redis://prod-redis:6379/0
```

### Docker Deployment

```bash
# Build image
docker build -t fxalpha-backend .

# Run container
docker run -d \
  -p 8000:8000 \
  -p 8001:8001 \
  --env-file .env \
  fxalpha-backend
```

### Gunicorn (Django)

```bash
gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --threads 2 \
  --max-requests 1000 \
  --max-requests-jitter 50
```

### Uvicorn (FastAPI)

```bash
uvicorn api.fastapi_app:app \
  --host 0.0.0.0 \
  --port 8001 \
  --workers 4 \
  --loop asyncio
```

---

## 📦 Dependencies

### Core
- `django==5.2.12` — Web framework
- `djangorestframework==3.15.2` — REST API
- `fastapi>=0.115.0` — Async API
- `uvicorn[standard]>=0.30.0` — ASGI server

### ML/AI
- `tensorflow>=2.16.0` — Deep learning
- `xgboost>=2.0.0` — Gradient boosting
- `hmmlearn>=0.3.0` — Hidden Markov Models
- `transformers==4.40.1` — HuggingFace models
- `torch==2.3.0` — PyTorch

### Data
- `pandas>=2.2` — Data manipulation
- `numpy>=1.26` — Numerical computing
- `influxdb-client==1.40.0` — Time-series DB
- `psycopg2-binary==2.9.9` — PostgreSQL

### Analysis
- `prophet>=1.1.5` — Time series forecasting
- `arch>=6.3.0` — GARCH volatility
- `shap>=0.44.0` — Model explainability
- `scikit-learn>=1.4` — ML utilities

---

## 📝 Notes

### Key Principles

1. **Deterministic Decisions** — All trading logic is rule-based Python
2. **LLM Only For** — Sentiment classification, natural language explanations
3. **Never Use LLM For** — Indicator calculations, signal thresholds, trading logic

### Performance Tips

- Use Redis for caching frequent queries
- Enable InfluxDB retention policies
- Run heavy ML training in background (Celery)
- Use connection pooling for PostgreSQL

---

## 👥 Team

**Backend Development** — Team DATAMINDS
- ML Agents integration (LSTM, XGBoost, HMM)
- Risk management system
- FastAPI async endpoints
- Real-time data pipeline

---

## 📄 License

Proprietary — Esprit PI 4DS11 2025-2026

---

<div align="center">

**Made with 🐍 Python + 🤖 Machine Learning**

*Team DATAMINDS — Major Currencies Trading Platform*

</div>
