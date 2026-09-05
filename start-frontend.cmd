@echo off
setlocal
cd /d "%~dp0frontend"
echo Starting DealPilot React Frontend on http://localhost:5173 ...
call npm.cmd run dev
