# FX Alpha Platform (Trading Signals — Agents + Data)

> **Ce dépôt** contient une plateforme de génération de signaux Forex multi-agents, structurée en couches (pipeline) et exposée via une API. Une partie du dépôt inclut également des expérimentations “géopolitique / causal” (agents dédiés, benchmarks).

---

## 1) Objectif

Générer un signal de trading **BUY / SELL / NEUTRAL** pour des paires Forex, en combinant :
- **Analyse technique** (TA / indicateurs, règles déterministes)
- **Contexte macroéconomique** (taux / inflation, règles déterministes)
- **Sentiment** (news, chemin “fast path” déterministe + chemin optionnel LLM local)
- **Géopolitique** (agent dédié : scoring par mots-clés / hybridité selon modules)

Le système intègre :
- un **CoordinatorAgentV2** qui agrège les votes des agents,
- une **Decision Layer** (scoring actuariel, gating LLM si activé, RiskManager),
- une **Monitoring** (safety, drift, performance),
- un **Frontend** (Next.js) pour l’interface et la visualisation.

---

## 2) Architecture (pattern TDSP)

Le projet suit un pipeline en couches :

```
Data Acquisition → Data Layer → Feature Layer → Signal Layer → API → Frontend
```

- Les **agents V2** calculent des signaux via **règles mathématiques / seuils** (auditable, reproductible).
- Le **LLM** n’est pas utilisé pour “décider” du trade : il sert au plus à **valider / annoter** et/ou à produire de la **text explanation**.

---

## 3) Stack

### Backend
- **Django 5+ / Django REST Framework (DRF)**
- **PostgreSQL 15** (macro, news, logs signaux, performance)
- **InfluxDB 2.7** (time-series OHLCV)
- **Redis 7** + **Celery** (cache / tâches async)
- NLP/LLM optionnel : **HuggingFace flan-t5-base** (et éventuellement Ollama)

### Frontend
- **Next.js 16 + React 19**
- **NextAuth** + **Prisma** (auth)
- **TanStack Query** (cache & data fetching)
- **shadcn/ui**, Tailwind, Recharts

---

## 4) Modules fonctionnels (vue d’ensemble)

### 4.1 Data Layer
- **TimeSeriesLoader** : lit OHLCV depuis InfluxDB
- **MacroDataLoader** : lit indicateurs macro depuis PostgreSQL
- **NewsLoader** : lit news depuis PostgreSQL (fenêtre de temps + filtrage par devises)

### 4.2 Feature Layer
- **TechnicalFeatureEngine** : indicateurs TA (RSI, MACD, Bollinger, ADX, ATR, etc.)
- **MacroFeatureEngine** : différentiels taux/inflation, carry, momentum macro
- **SentimentFeatureEngine** :
  - fast path : sentiment pré-calculé / heuristique
  - slow path : optionnel LLM local (classification)
- **CrossPairCorrelationEngine** : corrélations entre paires (log-returns) pour confirmer/réduire la confiance

### 4.3 Signal Layer (Agents)
- **TechnicalAgentV2** : règles déterministes (seuils pondérés)
- **MacroAgentV2** : logique macro (rate differential, momentum, carry)
- **SentimentAgentV2** : agrégation déterministe des news (avec option LLM)
- **GeopoliticalAgentV2** : scoring géopolitique par keywords / hybridité
- **CoordinatorAgentV2** : vote pondéré dynamique + détection régime + règles de sécurité (conflits, volatilité)

### 4.4 Decision Layer
- **ActuarialScorer** : EV (Expected Value), P(win), risk/reward, Kelly
- **LLM judges (optionnels)** : gate (APPROVE/REJECT/MODIFY) selon configuration
- **RiskManager** : veto absolu + validation (drawdown, RR, confidence, limites, sizing ATR)
- **XAIFormatter** : structuration de la sortie pour API/UI

### 4.5 Monitoring
- **SafetyMonitor** : cooldown + quotas + circuit breaker drawdown
- **DriftDetector** : détection de dérive statistique
- **PerformanceTracker** : Sharpe, win-rate, PnL & auto-disable

### 4.6 Backtesting
- Walk-forward backtesting (sans look-ahead bias)
- métriques : Sharpe, drawdown, win-rate, profit factor, etc.

---

## 5) Points d’entrée / API (niveau conceptuel)

Le frontend appelle des endpoints du backend (DRF) pour :
- générer un signal **(V2)**,
- consulter monitoring (health, drift, safety),
- récupérer KPIs / performance,
- consulter données techniques / news.

Les noms exacts des endpoints peuvent être consultés dans la documentation du repo (ex. ARCHITECTURE.md).

---

## 6) Démarrage local (haut niveau)

Depuis la racine :
- **Docker** : `docker-compose up -d`
- **Backend** : `python manage.py runserver` (port 8000)
- **Frontend** : `npm run dev` (port 3000)

Les variables requises (Postgres/Influx tokens, etc.) sont décrites dans **ARCHITECTURE.md**.

---

## 7) Ressources du dépôt

- **ARCHITECTURE.md** : architecture complète (couches, données, API, pipeline)
- **STACK.md** : stack & pipeline
- **AGENTS_AND_SIGNAL_PIPELINE.md** : pipeline agents + decision layer
- **DECISION_PIPELINE_README.md** : détails du decision pipeline (actuarial / judges / risk)
- **OLLAMA_SETUP.md** : configuration modèles locaux si besoin

---

## 8) Notes importantes

- Les décisions “hot path” sont conçues pour être **déterministes** (règles mathématiques).
- L’usage du LLM est **limité** : validation, enrichissement, explications (selon configuration), jamais moteur de décision principal.

---

## 9) Liens utiles

- Documentation : ARCHITECTURE.md, STACK.md, AGENTS_AND_SIGNAL_PIPELINE.md
- Causal / Géopolitique (expériences) : voir modules dans `backend/ai_layer/` et scripts de benchmarking dans `backend/benchmarking/`.

