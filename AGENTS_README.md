# 🤖 Multi-Agent Forex Trading System

## Architecture Vue d'Ensemble

Système de décision multi-agents pour le trading forex basé sur trois types d'analyses complémentaires.

```
┌─────────────────────────────────────────────────────────────┐
│                    ENSEMBLE AGENT                           │
│              (Weighted Voting + Conflict Resolution)        │
└──────────────┬──────────────┬────────────────┬─────────────┘
               │              │                │
       ┌───────▼──────┐ ┌────▼────────┐ ┌────▼─────────┐
       │  Technical   │ │ Fundamental │ │  Sentiment   │
       │    Agent     │ │    Agent    │ │    Agent     │
       └──────────────┘ └─────────────┘ └──────────────┘
               │              │                │
       ┌───────▼──────┐ ┌────▼────────┐ ┌────▼─────────┐
       │  InfluxDB    │ │ PostgreSQL  │ │  PostgreSQL  │
       │ (Forex OHLC) │ │ (Economic)  │ │    (News)    │
       └──────────────┘ └─────────────┘ └──────────────┘
```

## 📦 Agents Implémentés

### 1. 🔵 Technical Agent (DSO1.2)
**Analyse technique basée sur les indicateurs de prix**

**Indicateurs:**
- RSI (Relative Strength Index) - 14 périodes
- MACD (Moving Average Convergence Divergence) - 12/26/9
- Bollinger Bands - 20 périodes, 2σ
- Moving Averages - SMA 20/50

**Signaux générés:**
- Surachat/survente RSI
- Crossovers MACD
- Cassures Bollinger Bands
- Golden/Death cross MA

**Poids par défaut:** 40% (0.4)

---

### 2. 🟢 Fundamental Agent (DSO1.1)
**Analyse fondamentale basée sur les indicateurs économiques**

**Indicateurs:**
- CPI (Consumer Price Index / Inflation)
- Fed Funds Rate (Taux d'intérêt)
- Unemployment Rate (Taux de chômage)
- GDP Growth (Croissance du PIB)

**Logique:**
- Inflation ↑ → Taux ↑ → Devise ↑ (Bullish)
- Taux ↑ → Capital étranger ↑ → Devise ↑ (Bullish)
- Chômage ↓ → Économie forte → Devise ↑ (Bullish)

**Poids par défaut:** 40% (0.4)

---

### 3. 🟡 Sentiment Agent (DSO1.3)
**Analyse de sentiment via NLP sur les actualités financières**

**Sources:**
- Reuters
- Bloomberg
- Financial Times
- CNBC

**Méthode:**
- Lexique de mots positifs/négatifs (>40 mots)
- Modificateurs d'intensité (very, extremely, etc.)
- Scoring relatif (devise base vs devise quote)

**Future:** Intégration FinBERT (transformer NLP)

**Poids par défaut:** 20% (0.2)

---

## 🎯 Ensemble System (DSO2.1 & DSO2.2)

### Méthodes de Vote

#### Weighted Voting (par défaut)
```python
score = Σ (confidence × weight) pour chaque agent
```
- Respecte les poids individuels des agents
- Normalise les scores par la somme des poids
- Seuil de confiance minimum: 30%

#### Majority Voting
```python
direction = mode(agent_directions)
```
- Chaque agent = 1 vote
- Simple majorité gagne
- Égalité → HOLD

### Résolution de Conflits (DSO2.2)

**Stratégie 1: By Confidence** (défaut)
- Choisit le signal avec la plus haute confiance pondérée
- Idéal quand un agent est très confiant

**Stratégie 2: By Priority**
- Ordre de priorité: Fundamental > Technical > Sentiment
- Logique: Fondamentaux dictent la direction long-terme

---

## 🚀 Installation & Usage

### Installation
```bash
cd forex-alpha-data
pip install -r requirements.txt
```

### Test Rapide
```python
from agents import EnsembleAgent

# Créer l'ensemble system
ensemble = EnsembleAgent(
    voting_method='weighted',
    min_confidence_threshold=0.3
)

# Analyser une paire forex
result = ensemble.analyze(symbol='EURUSD', forex_data=df)

print(f"Direction: {result['direction']}")
print(f"Confidence: {result['confidence']:.2%}")
```

### Test Complet
```bash
python test_agents.py
```

Cela exécute:
- ✅ Test de chaque agent individuellement
- ✅ Test du système ensemble
- ✅ Test de résolution de conflits
- ✅ Métriques de performance

---

## 📊 Exemples de Signaux

### Signal Unanime (Fort Consensus)
```
📈 ENSEMBLE DECISION: BUY
Confidence: 78%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Individual Signals:
  📈 Technical Agent:    BUY  (75%)
  📈 Fundamental Agent:  BUY  (82%)
  📈 Sentiment Agent:    BUY  (79%)
```

### Signal Conflictuel (Résolution Nécessaire)
```
⏸️ ENSEMBLE DECISION: HOLD
Confidence: 52%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Individual Signals:
  📈 Technical Agent:    BUY  (65%)
  📉 Fundamental Agent:  SELL (70%)
  ⏸️ Sentiment Agent:    HOLD (40%)

Resolution: Confidence-based → Fundamental wins
```

---

## 📁 Structure des Fichiers

```
agents/
├── __init__.py             # Package initialization
├── base_agent.py           # Classe abstraite BaseAgent + Signal
├── technical_agent.py      # Agent d'analyse technique
├── fundamental_agent.py    # Agent d'analyse fondamentale
├── sentiment_agent.py      # Agent d'analyse de sentiment
└── ensemble_agent.py       # Système d'ensemble

test_agents.py              # Suite de tests complète
```

---

## 🔧 Paramètres Configurables

### Technical Agent
```python
TechnicalAgent(
    rsi_period=14,          # Période RSI
    rsi_oversold=30,        # Seuil survente
    rsi_overbought=70,      # Seuil surachat
    macd_fast=12,           # MACD rapide
    macd_slow=26,           # MACD lent
    macd_signal=9,          # Signal MACD
    bb_period=20,           # Période Bollinger
    bb_std=2.0,             # Std dev Bollinger
    ma_short=20,            # MA courte
    ma_long=50              # MA longue
)
```

### Fundamental Agent
```python
FundamentalAgent(
    cpi_weight=0.3,               # Poids CPI
    interest_rate_weight=0.4,     # Poids taux
    unemployment_weight=0.2,      # Poids chômage
    gdp_weight=0.1                # Poids PIB
)
```

### Sentiment Agent
```python
SentimentAgent(
    lookback_days=7  # Fenêtre d'analyse news
)
```

### Ensemble Agent
```python
EnsembleAgent(
    voting_method='weighted',           # 'weighted' ou 'majority'
    conflict_resolution='confidence',   # 'confidence' ou 'priority'
    min_confidence_threshold=0.3        # Seuil minimum [0-1]
)
```

---

## 🎯 DSO Readiness Status

| DSO   | Composant           | Status | Complétion |
|-------|---------------------|--------|------------|
| DSO1.1| Fundamental Agent   | ✅ Complete | 100% |
| DSO1.2| Technical Agent     | ✅ Complete | 100% |
| DSO1.3| Sentiment Agent     | ✅ Complete | 85%  |
| DSO2.1| Ensemble Logic      | ✅ Complete | 95%  |
| DSO2.2| Conflict Resolution | ✅ Complete | 90%  |

**Notes:**
- DSO1.3: Utilise lexique keyword (85%). FinBERT NLP à intégrer (+15%)
- DSO2.1: Weighted & majority voting opérationnels. XGBoost ML à ajouter (+5%)
- DSO2.2: Résolution confidence/priority fonctionnelle. Backtesting à valider (+10%)

---

## 📈 Prochaines Étapes

### Phase 2 - Feature Engineering (2 semaines)
- [ ] Ajouter ATR (Average True Range) pour volatilité
- [ ] Calculer Fibonacci retracements
- [ ] Implémenter support/resistance detection
- [ ] Ajouter lag features économiques (1, 3, 6 mois)
- [ ] Intégrer FinBERT pour sentiment avancé

### Phase 3 - MLOps (3 semaines)
- [ ] XGBoost meta-learner pour ensemble
- [ ] MLflow tracking des expériences
- [ ] Prometheus monitoring en temps réel
- [ ] FastAPI REST endpoint
- [ ] Backtesting engine avec Backtrader

---

## 📚 Références

- **TA-Lib**: Technical Analysis Library ([ta-lib.org](https://ta-lib.org/))
- **FinBERT**: Financial Sentiment Analysis ([huggingface.co](https://huggingface.co/ProsusAI/finbert))
- **FRED API**: Federal Reserve Economic Data ([fred.stlouisfed.org](https://fred.stlouisfed.org/))
- **CRISP-DM**: Cross-Industry Standard Process for Data Mining

---

## 📞 Support

Pour toute question sur l'implémentation des agents:
- Consulter `test_agents.py` pour des exemples d'utilisation
- Lire les docstrings dans chaque classe d'agent
- Vérifier `DATA_UNDERSTANDING_REPORT.md` pour le contexte business

---

**Version:** 1.0.0  
**Date:** 22 février 2026  
**Phase:** CRISP-DM Phase 3 - Data Preparation & Modeling  
**Status:** ✅ Agents opérationnels et testés
