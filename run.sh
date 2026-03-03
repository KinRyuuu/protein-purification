#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cleanup() {
  echo ""
  echo "Shutting down..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  echo "Done."
}
trap cleanup EXIT INT TERM

# Start backend
echo "Starting backend on http://localhost:8000 ..."
"$SCRIPT_DIR/.venv/bin/uvicorn" backend.main:app --reload --app-dir "$SCRIPT_DIR" &
BACKEND_PID=$!

# Start frontend (Vite dev server proxies /api to backend)
echo "Starting frontend on http://localhost:5173 ..."
npx --prefix "$SCRIPT_DIR/frontend" vite --host &
FRONTEND_PID=$!

echo ""
echo "Open http://localhost:5173 in your browser."
echo "Press Ctrl-C to stop both servers."
echo ""

wait
