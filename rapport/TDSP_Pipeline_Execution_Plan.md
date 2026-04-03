# TDSP Pipeline Execution Plan

Projet: Framework multi-modal multi-agent pour analyse FX et generation d alpha
Perimetre: 4 paires majeures (EURUSD, USDJPY, GBPUSD, USDCHF)
Horizon: 12-16 semaines
Methodologie: TDSP (Microsoft)

## 1. Executive Summary

Ce document transforme la vision TDSP en plan d execution concret, avec jalons, criteres de sortie, risques et livrables directement relies au repository actuel.

Objectif produit:
- Construire un systeme d aide a la decision (BUY/SELL/HOLD) explicable.
- Respecter le principe des 4 yeux (validation humaine).
- Prioriser la robustesse et la tracabilite avant l automatisation complete.

## 2. KPI Cibles (MVP)

Business/Trading:
- Win Rate > 55%
- Sharpe Ratio > 1.5
- Max Drawdown < 15%
- F1 signal BUY/SELL/HOLD > 0.65

Systeme:
- Latence de signal < 500 ms (objectif cible, hors batch lourd)
- Disponibilite > 99%
- Taux erreur API < 1%

Agents:
- Taux de consensus inter-agents > 70%
- Temps decision orchestrateur < 500 ms

## 3. Scope Fonctionnel

In:
- Ingestion MT5 OHLCV
- Ingestion macro (FRED + ECB)
- Ingestion texte (news + calendrier eco)
- 3 agents specialises + 1 orchestrateur
- API FastAPI + dashboard React
- Backtesting et reporting
- Observabilite minimale (metrics, logs, traces)

Out (MVP):
- Execution autonome live sans validation humaine
- Coverage de paires exotiques
- Optimisation HFT ultra basse latence

## 4. Architecture Cible (MVP)

Couche Donnees:
- Collecteurs: scripts Python dans forex-alpha-data et agents
- Stockage: PostgreSQL (structure), InfluxDB/Timeseries (prix)

Couche Features:
- Feature engineering multi-source (agents/feature_engineering.py)
- Feature selection (agents/feature_selection.py)

Couche Intelligence:
- Agent macro
- Agent technique
- Agent sentiment
- Agent orchestrateur

Couche Exposition:
- API FastAPI (agents/fx_alpha_backend_fastapi.py)
- Frontend React (forex-ui)

Couche Ops:
- docker-compose pour stack locale
- monitoring initial (logs + metriques de base)

## 5. Roadmap 12-16 Semaines

### Phase 1 - Business Understanding (S1-S3)
Sorties:
- objectifs SMART
- KPI valides
- RACI
- architecture haut niveau
- backlog priorise

Gate de sortie:
- Go/No-Go approuve par PO + Lead DS

### Phase 2 - Data Acquisition & Understanding (S4-S7)
Sorties:
- pipeline ingestion stable pour 4 paires
- schema data documente
- notebook EDA validant qualite et couverture

Gate de sortie:
- data quality pass sur checks critiques

### Phase 3 - Modeling (S8-S12)
Sorties:
- baseline par agent
- orchestrateur (regles + vote pondere)
- backtesting walk-forward

Gate de sortie:
- KPI minimaux atteints sur periode holdout

### Phase 4 - Deployment (S13-S15)
Sorties:
- API exposee
- dashboard operationnel
- runbooks

Gate de sortie:
- tests integration verts

### Phase 5/6 - MLOps & Iteration (continu)
Sorties:
- tracking experiments
- monitoring drift
- cadence de re-train

## 6. Mapping Repo -> Livrables

- agents/agent_scraping.py: ingestion multi-source
- agents/agent_technical.py: agent technique
- agents/feature_engineering.py: matrice features
- agents/feature_selection.py: reduction features
- agents/fx_alpha_backend_fastapi.py: backend inference
- forex-alpha-data/: collecteurs data sources
- forex-ui/: dashboard utilisateur
- notebooks/: EDA et analyses exploratoires

## 7. Risks & Mitigation

Risque: indisponibilite source externe
- Mitigation: source secondaire + retries + cache

Risque: couts LLM trop eleves
- Mitigation: fallback local, prompts courts, cache semantic

Risque: overfitting
- Mitigation: walk-forward, holdout strict, regularisation

Risque: latence depassee
- Mitigation: precompute features, async IO, profilage

## 8. Definition of Done (MVP)

Un increment est "done" si:
- code merge sur branche principale de dev
- tests unitaires et integration passent
- logs/metriques minimales disponibles
- documentation mise a jour
- demonstration reproductible en local via docker-compose
