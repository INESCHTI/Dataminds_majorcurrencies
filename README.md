# FX Alpha Platform

> Plateforme de génération de **signaux Forex** via un système **multi-agents** (technique + macro + sentiment + géopolitique), exposé via une API.

---

## Ce que fait le projet

Le système génère un signal de trading pour des paires Forex :
- **BUY / SELL / NEUTRAL**
- avec un score de **confiance**
- accompagné d’explications structurées (XAI), et d’une couche de **sécurité** (veto RiskManager, SafetyMonitor, etc.).

L’architecture est conçue pour être majoritairement **déterministe** (règles mathématiques) afin de garantir reproductibilité et auditabilité. Le LLM est utilisé en option (validation / explications / sentiment selon configuration).

---

## Architecture (pattern TDSP)

Pipeline en couches :

```
Data Acquisition → Data Layer → Feature Layer → Signal Layer → API → Frontend
```

- **Data Acquisition** : collecte (MT5 OHLCV, macro, news)
- **Data Layer** : loaders InfluxDB (OHLCV) + PostgreSQL (macro/news)
- **Feature Layer** : calcul d’indicateurs techniques + features macro + sentiment
- **Signal Layer (agents)** : votes des agents (Technical/Macro/Sentiment/Geopolitical)
- **CoordinatorAgentV2** : agrégation pondérée dynamique + détection de régime + règles de sécurité
- **Decision Layer** : scoring actuariel (EV / Kelly) + validation LLM optionnelle + RiskManager (veto)
- **Monitoring** : drift, safety, performance
- **Frontend** : dashboard Next.js

---

## Stack

### Backend
- **Django + Django REST Framework**
- **PostgreSQL** (macro, news, logs)
- **InfluxDB 2.7** (OHLCV time-series)
- **Redis + Celery**

### Frontend
- **Next.js + React**
- **NextAuth + Prisma**
- UI : shadcn/ui + Tailwind

---

## Démarrage (local, haut niveau)

1) Démarrer les services de données

- `docker-compose up -d`

2) Lancer le backend

- `python manage.py runserver` (backend : **:8000**)

3) Lancer le frontend

- `npm run dev` (frontend : **:3000**)

---

## Documentation principale

- **ARCHITECTURE.md** : architecture complète (couches, données, endpoints, pipeline)
- **STACK.md** : stack technique & pipeline résumé
- **AGENTS_AND_SIGNAL_PIPELINE.md** : détails agents + decision layer
- **DECISION_PIPELINE_README.md** : détails actuariel / judges / risk

---

## Notes

- Les agents V2 utilisent des **règles déterministes** pour calculer le signal.
- Le LLM est **optionnel** et n’est pas censé générer la décision de trading : il sert à valider / enrichir / expliquer selon configuration.

