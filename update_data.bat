@echo off

echo ========================================================
echo        FX-AlphaLab Data Pipeline Updater
echo ========================================================
echo.

echo [1/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [2/5] Running Data Acquisition...
python data_understanding\acquire_mt5_data.py
python data_understanding\acquire_fred_data.py
python data_understanding\acquire_news_data.py

echo.
echo [3/5] Running Feature Engineering...
python data_understanding\feature_engineering.py

echo.
echo [4/5] Running Data Integration...
python data_understanding\data_integration.py

echo.
echo [5/6] Running Statistical Analysis...
python data_understanding\statistical_analysis.py

echo.
echo [6/6] Training Sentiment Agent...
python modeling\sentiment_agent\train_sentiment_agent.py

echo.
echo ========================================================
echo        Pipeline Execution Complete!
echo ========================================================
pause
