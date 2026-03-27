# Forex Alpha - Multi-Agent Currency Prediction System

## Overview
Forex Alpha is an end-to-end machine learning and multi-agent system for predicting major currency pairs (EUR/USD, GBP/USD, USD/JPY). The project combines market data, macro indicators, and sentiment signals into a hybrid prediction and decision workflow.

## What Is Included
- Data acquisition pipelines for MT5 market data, FRED macro data, and news sentiment
- Data understanding and exploratory analysis artifacts
- Feature engineering and model training workflows
- Multi-agent decision layer (technical, fundamental, sentiment, ensemble)
- Deployment options for Python app and Dockerized services
- Full-stack interface with React frontend and Django backend API

## Branch Update Notes (`mahaaloui`)

### Frontend Updates
- Added React application structure in `frontend/`
- Implemented pages/components for dashboard, charts, chat, and signals
- Added API service layer in `frontend/src/services/api.js` to consume backend endpoints
- Included style assets for reusable UI components

### Backend Updates
- Added Django backend project in `backend/`
- Implemented API app with models, serializers, routes, and views
- Added integration points for LangChain service and RL agent logic
- Included backend Dockerfile and environment-specific requirements

### Full-Stack Integration Updates
- Added Docker Compose files for service orchestration
- Added dedicated documentation for React/Django setup in `REACT_DJANGO_README.md`
- Organized project for local development and container-based execution

## Quick Start (Python Pipeline)
```bash
pip install -r requirements.txt
python quickstart.py
```

## Full-Stack Quick Start
1. Backend setup:
```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
2. Frontend setup (new terminal):
```bash
cd frontend
npm install
npm start
```

## Team
ESPRIT - 4DS11 - 2025/2026
