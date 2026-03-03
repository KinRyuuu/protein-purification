#!/usr/bin/env bash
# Build the Protein Purification Electron app.
#
# Prerequisites:
#   - Python venv at .venv/ with project installed  (pip install -e ".[dev]")
#   - pyinstaller installed              (pip install pyinstaller)
#   - Node.js / npm installed
#
# Usage: ./scripts/build-electron.sh [--skip-frontend] [--skip-pyinstaller]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$SCRIPT_DIR/.."

SKIP_FRONTEND=false
SKIP_PYINSTALLER=false
for arg in "$@"; do
  case "$arg" in
    --skip-frontend)     SKIP_FRONTEND=true ;;
    --skip-pyinstaller)  SKIP_PYINSTALLER=true ;;
  esac
done

# ── Step 1: Build frontend ────────────────────────────────────────────────────
if [ "$SKIP_FRONTEND" = false ]; then
  echo "=== [1/3] Building frontend ==="
  npm --prefix "$ROOT/frontend" install
  npm --prefix "$ROOT/frontend" run build
else
  echo "=== [1/3] Skipping frontend build ==="
fi

if [ ! -d "$ROOT/frontend/dist" ]; then
  echo "ERROR: frontend/dist not found. Run without --skip-frontend first." >&2
  exit 1
fi

# ── Step 2: Bundle Python backend with PyInstaller ───────────────────────────
if [ "$SKIP_PYINSTALLER" = false ]; then
  echo "=== [2/3] Bundling Python backend with PyInstaller ==="

  PYINSTALLER="$ROOT/.venv/bin/pyinstaller"
  if [ ! -x "$PYINSTALLER" ]; then
    echo "ERROR: pyinstaller not found in .venv. Run:" >&2
    echo "  .venv/bin/pip install pyinstaller" >&2
    exit 1
  fi

  "$PYINSTALLER" "$ROOT/server.spec" --noconfirm --distpath "$ROOT/dist" --workpath "$ROOT/build/pyinstaller"
else
  echo "=== [2/3] Skipping PyInstaller build ==="
fi

if [ ! -d "$ROOT/dist/protein-purification-server" ]; then
  echo "ERROR: dist/protein-purification-server not found. Run without --skip-pyinstaller first." >&2
  exit 1
fi

# ── Step 3: Package with electron-builder ────────────────────────────────────
echo "=== [3/3] Packaging with electron-builder ==="
npm --prefix "$ROOT/electron" install
npm --prefix "$ROOT/electron" run dist

echo ""
echo "Done. Output packages are in release/"
