#!/usr/bin/env bash
set -e

echo "========================================="
echo " DealPilot One-Click Local Setup"
echo "========================================="

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo ""
echo "[1/2] Setting up Backend..."
cd backend
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment in backend/.venv ..."
    python3 -m venv .venv
fi

echo "Installing backend dependencies..."
.venv/bin/pip install -q -r requirements.txt

if [ ! -f ".env" ]; then
    echo "Copying .env.example to .env ..."
    cp .env.example .env
fi
cd "$DIR"

echo ""
echo "[2/2] Setting up Frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi
cd "$DIR"

echo ""
echo "========================================="
echo " Setup complete!"
echo " Run ./start.sh to launch DealPilot."
echo "========================================="
