@echo off
echo Starting Writing Assistant Backend Server...
echo.
cd /d "%~dp0"
call venv\Scripts\activate.bat
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
