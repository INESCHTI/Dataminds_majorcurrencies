@echo off

echo ========================================================
echo        Starting FX-AlphaLab Dashboard Backend
echo ========================================================
echo.

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Starting FastAPI server...
cd platform\backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause
