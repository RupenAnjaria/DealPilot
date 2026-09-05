#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "========================================="
echo " Starting DealPilot (Backend & Frontend)"
echo "========================================="

echo "Starting Backend on http://localhost:8000 ..."
(cd "$DIR/backend" && .venv/bin/python -m uvicorn app.main:app --reload --port 8000) &
BACKEND_PID=$!

echo "Starting Frontend on http://localhost:5173 ..."
(cd "$DIR/frontend" && npm run dev) &
FRONTEND_PID=$!

echo ""
echo "DealPilot is running!"
echo "  - Backend API:  http://localhost:8000 (Docs: http://localhost:8000/docs)"
echo "  - Frontend UI:  http://localhost:5173"
echo "Press Ctrl+C to stop both."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT INT TERM
wait
