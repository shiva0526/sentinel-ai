#!/usr/bin/env bash
# run_all.sh — Start the entire SentinelAI stack locally.
# Usage: bash scripts/run_all.sh

set -e

echo "═══════════════════════════════════════"
echo "  SentinelAI — Starting All Services"
echo "═══════════════════════════════════════"

# 1. Arena (Go sandbox)
echo ""
echo "[1/3] Starting Arena (Go sandbox) on :8080..."
cd arena
go build -o arena-server ./cmd/server.go 2>/dev/null && ./arena-server &
ARENA_PID=$!
cd ..
sleep 2

# 2. Orchestrator (Python pipeline)
echo "[2/3] Starting Orchestrator (Python) on :8000..."
cd orchestrator
python -m app.main &
ORCH_PID=$!
cd ..
sleep 2

# 3. Frontend (React)
echo "[3/3] Starting Frontend (React) on :5173..."
cd frontend
npm run dev &
FRONT_PID=$!
cd ..

echo ""
echo "═══════════════════════════════════════"
echo "  All services running!"
echo "  Arena:        http://localhost:8080"
echo "  Orchestrator: http://localhost:8000"
echo "  Frontend:     http://localhost:5173"
echo "═══════════════════════════════════════"
echo ""
echo "Press Ctrl+C to stop all services."

# Trap cleanup
cleanup() {
    echo "Stopping all services..."
    kill $ARENA_PID $ORCH_PID $FRONT_PID 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM

wait
