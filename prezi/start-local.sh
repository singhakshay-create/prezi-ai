#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

export PATH="$HOME/.local/bin:$PATH"

echo "=== Prezi AI - Local Setup ==="
echo ""

# --- Check .env ---
if [ ! -f .env ]; then
    echo "[!] .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo ""
    echo "[!] Please edit .env and add at least one LLM API key, then run this script again."
    echo "    Required: ANTHROPIC_API_KEY, OPENAI_API_KEY, or NVIDIA_API_KEY"
    exit 1
fi

# Warn if no LLM key is configured
if ! grep -qE "^(ANTHROPIC|OPENAI|NVIDIA)_API_KEY=.+" .env; then
    echo "[WARNING] No LLM API key found in .env."
    echo "          Add ANTHROPIC_API_KEY, OPENAI_API_KEY, or NVIDIA_API_KEY to generate presentations."
    echo ""
fi

# --- Check Node ---
if ! command -v node &>/dev/null; then
    echo "[ERROR] Node.js not found. Please install Node.js 18+."
    exit 1
fi
echo "[OK] Node: $(node --version)"

# --- Python: prefer uv, fall back to system python3 ---
PYTHON_BIN=""
USE_UV=false

if command -v uv &>/dev/null; then
    USE_UV=true
    echo "[OK] uv: $(uv --version)"
elif command -v python3 &>/dev/null; then
    PYTHON_BIN="$(command -v python3)"
    echo "[OK] Python: $($PYTHON_BIN --version)"
else
    echo "[ERROR] Python 3 not found. Please install Python 3.8+."
    exit 1
fi

# --- Backend venv ---
echo ""
echo "--- Setting up backend ---"

if [ ! -d backend/.venv ]; then
    echo "Creating Python virtual environment..."
    if $USE_UV; then
        # Try Python 3.11 first, fall back to whatever is available
        uv venv backend/.venv --python 3.11 2>/dev/null || uv venv backend/.venv
    else
        $PYTHON_BIN -m venv backend/.venv
    fi
fi

VENV_PYTHON="$SCRIPT_DIR/backend/.venv/bin/python"
VENV_PIP="$SCRIPT_DIR/backend/.venv/bin/pip"
VENV_UVICORN="$SCRIPT_DIR/backend/.venv/bin/uvicorn"

echo "Installing Python dependencies..."
if $USE_UV; then
    uv pip install -r backend/requirements.txt --python "$VENV_PYTHON" --quiet
else
    "$VENV_PIP" install -r backend/requirements.txt --quiet
fi
echo "[OK] Python dependencies installed."

# --- Create data directories ---
mkdir -p data/presentations data/templates

# --- Frontend deps ---
echo ""
echo "--- Setting up frontend ---"

if [ ! -d frontend/node_modules ]; then
    echo "Installing npm dependencies..."
    (cd frontend && npm install)
else
    echo "[OK] npm dependencies already installed."
fi

# --- Kill any existing services on our ports ---
echo ""
echo "--- Starting services ---"

for port in 8000 3000; do
    # Use fuser if available, otherwise ss/lsof
    if command -v fuser &>/dev/null; then
        fuser -k "${port}/tcp" 2>/dev/null || true
    elif command -v lsof &>/dev/null; then
        pid=$(lsof -ti :"$port" 2>/dev/null || true)
        [ -n "$pid" ] && kill "$pid" 2>/dev/null || true
    fi
done
sleep 1

# Log files
BACKEND_LOG="$SCRIPT_DIR/backend.log"
FRONTEND_LOG="$SCRIPT_DIR/frontend.log"
> "$BACKEND_LOG"
> "$FRONTEND_LOG"

# --- Start backend ---
echo "Starting backend on http://localhost:8000 ..."
(
    cd "$SCRIPT_DIR"
    "$VENV_UVICORN" app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --app-dir backend \
        --reload \
        --reload-dir backend/app \
        --log-level info
) >> "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!

# --- Wait for backend to be healthy (up to 30s) ---
echo -n "Waiting for backend..."
READY=false
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
        READY=true
        break
    fi
    # Check if the process died
    if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo ""
        echo "[ERROR] Backend failed to start. Last log output:"
        echo "---"
        tail -20 "$BACKEND_LOG"
        echo "---"
        echo "Full log: $BACKEND_LOG"
        exit 1
    fi
    echo -n "."
    sleep 1
done
echo ""

if ! $READY; then
    echo "[ERROR] Backend didn't become healthy after 30s. Log output:"
    echo "---"
    tail -20 "$BACKEND_LOG"
    echo "---"
    echo "Full log: $BACKEND_LOG"
    kill "$BACKEND_PID" 2>/dev/null || true
    exit 1
fi
echo "[OK] Backend is healthy."

# --- Start frontend ---
echo "Starting frontend on http://localhost:3000 ..."
(cd "$SCRIPT_DIR/frontend" && npm run dev) >> "$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$!

sleep 2

echo ""
echo "========================================"
echo "  Prezi AI is running!"
echo "========================================"
echo ""
echo "  App:       http://localhost:3000"
echo "  API:       http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo ""
echo "  Logs:"
echo "    Backend:  tail -f $BACKEND_LOG"
echo "    Frontend: tail -f $FRONTEND_LOG"
echo ""
echo "Press Ctrl+C to stop."
echo ""

cleanup() {
    echo ""
    echo "Shutting down..."
    kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
    echo "Stopped."
}
trap cleanup INT TERM

wait "$BACKEND_PID" "$FRONTEND_PID"
