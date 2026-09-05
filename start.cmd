@echo off
setlocal
echo =========================================
echo  Starting DealPilot (Backend ^& Frontend)
echo =========================================

cd /d "%~dp0"

echo.
echo Launching FastAPI Backend on http://localhost:8000 ...
start "DealPilot Backend" cmd /k "cd /d "%~dp0backend" ^&^& .venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"

echo Launching Vite Frontend on http://localhost:5173 ...
start "DealPilot Frontend" cmd /k "cd /d "%~dp0frontend" ^&^& npm.cmd run dev"

echo.
echo DealPilot is starting in two separate terminal windows.
echo   - Backend API:  http://localhost:8000 (Docs: http://localhost:8000/docs)
echo   - Frontend UI:  http://localhost:5173
echo.
