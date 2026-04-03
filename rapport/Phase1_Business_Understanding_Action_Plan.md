# Phase 1 - Business Understanding Action Plan

Duree cible: 2-3 semaines
Objectif: Cadrer le projet, definir KPI, roles, contraintes et architecture initiale

## Semaine 1 - Cadrage

### Tache 1.1 - Objectifs SMART (2 jours)
Actions:
- Atelier de cadrage (PO, DS Lead, Analyste, DevOps)
- Validation des 4 paires cibles
- Validation objectif principal: systeme d aide a la decision multi-agent

Livrables:
- SMART_Objectives.md
- Decision log de cadrage

Critere d acceptation:
- objectifs mesurables et datees
- accord explicite de toutes les parties prenantes

### Tache 1.2 - KPIs projet (1 jour)
Actions:
- Definir KPI trading, systeme, agents et couts
- Definir periodicite de mesure

Livrables:
- KPI_Framework.md
- KPI_Dashboard_Spec.md

Critere d acceptation:
- seuils de succes quantifies
- methode de calcul documentee

### Tache 1.3 - Traduction en objectifs Data Science (2 jours)
Actions:
- Cartographier objectifs business vers problemes ML/NLP/TS
- Definir output standardise des agents (schema signal)

Livrables:
- DS_Objectives_and_Problem_Mapping.md
- Signal_Schema_v1.json

Critere d acceptation:
- chaque objectif business associe a metrique ML

## Semaine 2 - Domaine et contraintes

### Tache 2.1 - Analyse Forex cible (2 jours)
Actions:
- Caracteriser les 4 paires (volatilite, sessions, events)
- Lister evenements macro critiques

Livrables:
- Forex_Domain_Analysis.md
- Event_Calendar_Priority_List.md

Critere d acceptation:
- scenarios de marche couverts (risk-on, risk-off, annonces)

### Tache 2.2 - Contraintes techniques et legales (2 jours)
Actions:
- Budget, latence, dispo, compliance
- Clarifier limite: aide a decision, pas execution autonome sans validation humaine

Livrables:
- Constraints_Matrix.md
- Legal_Disclaimer.md

Critere d acceptation:
- contraintes classes P0/P1/P2
- mitigation par contrainte P0

### Tache 2.3 - Etat de l art (2 jours)
Actions:
- benchmark algorithmes time series, NLP, ensemble
- benchmark frameworks agents

Livrables:
- State_of_the_Art.md
- Tech_Choice_Rationale.md

Critere d acceptation:
- choix techno justifies par cout, latence, performance

## Semaine 3 - Architecture et planification

### Tache 3.1 - Architecture systeme (3 jours)
Actions:
- Definir architecture en 5 couches
- Definir interfaces et contrats API

Livrables:
- System_Architecture.md
- API_Contracts_v1.md

Critere d acceptation:
- flux bout-en-bout valide en revue technique

### Tache 3.2 - Backlog et plan release (2 jours)
Actions:
- Ecrire user stories par phase
- Estimer et prioriser (MoSCoW)

Livrables:
- Product_Backlog_Phase2_4.csv
- Release_Gantt.md
- Risk_Register.md

Critere d acceptation:
- 2 prochains sprints prets

### Tache 3.3 - Setup environnement (2 jours)
Actions:
- verifier stack locale (DB + API + UI)
- verifier CI basique

Livrables:
- Environment_Setup_Status.md
- CI_Checklist.md

Critere d acceptation:
- onboarding dev < 60 min

### Tache 3.4 - Revue fin Phase 1 (1 jour)
Actions:
- presentation aux stakeholders
- arbitrage Go/No-Go

Livrables:
- Phase1_Review_Slides.md
- Go_NoGo_Record.md

Critere d acceptation:
- decision officielle pour lancement Phase 2

## RACI simplifie

- Product Owner: scope, priorisation, validation metier
- DS Lead: architecture, qualite scientifique
- Data Engineer: pipelines data, stockage
- ML Engineer: deploiement, monitoring, CI/CD
- Financial Analyst: coherence marche et hypotheses de trading

## Definition of Done - Phase 1

- objectifs/KPI valides
- contraintes et risques documentes
- architecture v1 approuvee
- backlog Sprint 1 Phase 2 pret
- decision Go/No-Go enregistree
