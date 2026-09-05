@echo off
setlocal
echo =========================================
echo  DealPilot One-Click Local Setup
echo =========================================

cd /d "%~dp0"

echo.
echo [1/2] Setting up Backend...
cd backend
if not exist .venv (
    echo Creating Python virtual environment in backend\.venv ...
    python -m venv .venv
) else (
    echo Python virtual environment already exists.
)

echo Installing backend dependencies...
.venv\Scripts\python.exe -m pip install -q -r requirements.txt

if not exist .env (
    echo Copying .env.example to .env ...
    copy .env.example .env
) else (
    echo .env already exists.
)
cd ..

echo.
echo [2/2] Setting up Frontend...
cd frontend
if not exist node_modules (
    echo Installing frontend dependencies...
    call npm.cmd install
) else (
    echo Frontend node_modules already exists.
)
cd ..

echo.
echo =========================================
echo  Setup complete!
echo  Run start.cmd to launch DealPilot.
echo =========================================
