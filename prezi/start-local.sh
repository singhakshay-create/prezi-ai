#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

export PATH="$HOME/.local/bin:$PATH"

echo "=== Prezi AI - Local Setup ==="
echo ""

# --- Check .env ---
if [ ! -f .env ]; then
    echo "[!] .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "[!] Please edit .env and add your API keys, then run this script again."
    exit 1
fi

# --- Check uv (Python manager) ---
if ! command -v uv &>/dev/null; then
    echo "Installing uv (fast Python package manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# --- Check Node ---
if ! command -v node &>/dev/null; then
    echo "[ERROR] Node.js not found. Please install Node.js 18+."
    exit 1
fi

echo "[OK] Node: $(node --version)"

# --- Backend Setup ---
echo ""
echo "--- Setting up backend ---"

if [ ! -d backend/.venv ]; then
    echo "Creating Python 3.11 virtual environment..."
    uv venv backend/.venv --python 3.11
fi

echo "Installing Python dependencies..."
uv pip install -r backend/requirements.txt --python backend/.venv/bin/python --quiet

# Create data directory
mkdir -p data

# --- Frontend Setup ---
echo ""
echo "--- Setting up frontend ---"

if [ ! -d frontend/node_modules ]; then
    echo "Installing npm dependencies..."
    (cd frontend && npm install)
else
    echo "[OK] npm dependencies already installed."
fi

# --- Start Services ---
echo ""
echo "--- Starting services ---"

# Kill any existing processes on our ports
for port in 8000 3000; do
    pid=$(lsof -ti :$port 2>/dev/null || true)
    if [ -n "$pid" ]; then
        echo "Killing existing process on port $port (PID $pid)"
        kill $pid 2>/dev/null || true
        sleep 1
    fi
done

# Start backend
echo "Starting backend (FastAPI on port 8000)..."
(cd "$SCRIPT_DIR" && source backend/.venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir backend) &
BACKEND_PID=$!

# Start frontend
echo "Starting frontend (Vite on port 3000)..."
(cd "$SCRIPT_DIR/frontend" && npm run dev) &
FRONTEND_PID=$!

# Wait a moment for startup
sleep 3

echo ""
echo "=== Prezi AI is running ==="
echo ""
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both services."
echo ""

# Trap Ctrl+C to kill both processes
cleanup() {
    echo ""
    echo "Shutting down..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    echo "Stopped."
}
trap cleanup INT TERM

# Wait for either to exit
wait $BACKEND_PID $FRONTEND_PID
