# BO et DSO

## BO1 - Improve FX Decision Quality Through Multi-Dimensional Market Understanding
Provide analysts with a unified and explainable view of the FX market by integrating macroeconomic, technical, sentiment, and event-driven insights.

- DSO1.1 - Develop a macroeconomic agent that ingests central bank rates, economic indicators (CPI, NFP, PMI), and analyzes FOMC/ECB/BoE communications using NLP/LLMs to generate a fundamental directional bias (-100 to +100) for each of the four major currency pairs.
- DSO1.2 - Build a multi-horizon technical agent that processes MT5 OHLC data across intraday (1H-4H), swing (D1), and position (W1-M1) timeframes using TA-Lib indicators and pattern recognition to generate entry/exit timing signals with confidence scores.
- DSO1.3 - Create a sentiment agent that scrapes and analyzes financial news, social media, and COT reports using FinBERT to quantify market positioning and detect sentiment extremes for contrarian signal generation.

## BO2 - Generate Explainable and Actionable Alpha Signals
Transform multi-agent insights into clear buy/sell recommendations accompanied by explanations and confidence levels.

- DSO2.1 - Develop a coordinating agent that aggregates signals from all specialized agents using ensemble methods (weighted voting/XGBoost) and produces final BUY/SELL/HOLD signals with validated confidence scores for each currency pair.
- DSO2.2 - Implement a robust backtesting framework with walk-forward validation on 5 years of historical data to evaluate signal performance, calculate key metrics (Sharpe ratio, win rate, max drawdown), and prevent overfitting.
- DSO2.3 - Create an intelligent position sizing module that recommends optimal trade size based on conviction scores and current volatility using Kelly Criterion and ATR-based risk management formulas.

## BO3 - Reduce Risks Related to False Signals
Improve recommendation robustness and limit decisions based on partial information.

- DSO3.1 - Implement rule-based and probabilistic agreement checks (agent voting, confidence thresholds, contradiction detection) to validate signals and resolve conflicts between macro, technical, and sentiment outputs.

## BO4 - Ensure System Reliability and Operational Robustness
Guarantee stable and reliable system operation by continuously monitoring data pipelines, models, and signal behavior.

- DSO4.1 - Implement automated validation checks (missing values, outliers, timestamp consistency) on incoming FX and macroeconomic data using Python data validation pipelines.
- DSO4.2 - Track model accuracy, signal stability, and end-to-end processing latency using MLflow metrics, logging, and real-time monitoring dashboards (Prometheus/Grafana).

## BO5 - Enable Transparent Evaluation and Decision Support Through Automated Reporting
Guarantee stable and reliable system operation by continuously monitoring data pipelines, models, and signal behavior.

- DSO5.1 - Generate structured analytical reports via FastAPI + dashboard (React) summarizing signals, explanations and backtesting performance.