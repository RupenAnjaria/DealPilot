@echo off
setlocal
cd /d "%~dp0backend"
echo Starting DealPilot FastAPI Backend on http://localhost:8000 ...
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
