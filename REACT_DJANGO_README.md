# Forex Alpha — React + Django + RLM + LangChain

> **Replaces the Streamlit app** with a professional React.js frontend + Django REST API backend.

---

## Architecture

```
┌─────────────────────┐        HTTP/REST        ┌──────────────────────────────┐
│   React Frontend    │ ──────────────────────► │     Django Backend (DRF)     │
│   localhost:3000    │                          │     localhost:8000           │
│                     │                          │                              │
│  • Dashboard        │ ◄── JSON responses ───  │  /api/signals/    (POST)     │
│  • Candlestick chart│                          │  /api/forex-data/ (GET)      │
│  • Signals page     │                          │  /api/chat/       (POST)     │
│  • AI Chat          │                          │  /api/signals/    train-rl/  │
└─────────────────────┘                          └──────────┬───────────────────┘
                                                            │
                        ┌───────────────────────────────────┤
                        │           │               │       │
                   InfluxDB    PostgreSQL    RLM Agent   LangChain
                   (OHLCV)    (Indicators)  (RL signals)  (AI chat)
```

### Key Components

| Component | Technology | Description |
|-----------|-----------|-------------|
| Frontend | React.js 18 + lightweight-charts | Trading dashboard, candlestick charts |
| Backend | Django 4.2 + DRF | REST API, business logic |
| RLM | Q-table / SB3 PPO | Reinforcement Learning signal agent |
| AI Chat | LangChain + GPT-4o-mini | Signal explanations, market analysis |
| OHLCV DB | InfluxDB 2.7 | Time-series forex prices |
| Metadata DB | PostgreSQL 15 | Economic indicators, signal logs |

---

## Quick Start (Local Development)

### 1. Start databases

```powershell
docker-compose up -d influxdb postgres
```

### 2. Start Django backend

```powershell
# In the project root
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
# → http://localhost:8000/api/
```

### 3. Start React frontend

```powershell
cd frontend
npm install
npm start
# → http://localhost:3000
```

---

## Full Docker Stack

```powershell
# Copy .env and set OPENAI_API_KEY
copy .env.example .env

docker-compose -f docker-compose.full.yml up --build
```

| Service | URL |
|---------|-----|
| React frontend | http://localhost:3000 |
| Django API | http://localhost:8000/api/ |
| InfluxDB UI | http://localhost:8086 |

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health/` | API health + service status |
| GET | `/api/symbols/` | Available currency pairs |
| GET | `/api/forex-data/` | OHLCV data `?symbol=EURUSD&timeframe=H1&days_back=30` |
| POST | `/api/signals/` | Generate multi-agent + RLM signal |
| POST | `/api/signals/train-rl/` | Train Q-table RL model |
| GET | `/api/signals/history/` | Past signals log |
| POST | `/api/chat/` | LangChain AI chat |
| POST | `/api/chat/explain/` | Explain a signal with AI |

### Generate Signal Example

```bash
curl -X POST http://localhost:8000/api/signals/ \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "EURUSD",
    "timeframe": "H1",
    "days_back": 14,
    "include_rl": true,
    "include_langchain": true,
    "session_id": "my-session"
  }'
```

Response includes:
- `ensemble_signal` — Technical + Fundamental + Sentiment agents
- `rl_signal` — Reinforcement Learning Model (Q-table or PPO)
- `ai_explanation` — LangChain/GPT explanation (if API key set)

---

## RLM (Reinforcement Learning Model)

The RLM agent lives in `backend/api/rl_agent.py`.

- **algorighm**: tabular Q-learning (default) or PPO via Stable-Baselines3
- **State space**: trend bucket × momentum × RSI bucket → 27 states
- **Actions**: 0=HOLD · 1=BUY · 2=SELL
- **Train via API**: `POST /api/signals/train-rl/` with `{symbol, episodes}`
- **Models stored** in `models_rl/<SYMBOL>_qtable.npy`

---

## LangChain AI Chat

Set `OPENAI_API_KEY` in `.env` to enable the full AI assistant.

Without an API key a **rule-based fallback** explanation is used automatically.

The AI:
- Explains why each signal was generated
- Identifies key risk factors
- Identifies relevant economic events
- Maintains multi-turn conversation memory per session

---

## Environment Variables

```env
OPENAI_API_KEY=sk-...           # For LangChain (optional)
POSTGRES_HOST=localhost
POSTGRES_DB=forex_metadata
POSTGRES_USER=forex_user
POSTGRES_PASSWORD=forex_pass_2026
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=my-super-secret-token
INFLUXDB_ORG=forexalpha
INFLUXDB_BUCKET=forex_data
DJANGO_SECRET_KEY=change-me-in-production
```
