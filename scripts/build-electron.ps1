# Build the Protein Purification Electron app on Windows.
#
# Prerequisites:
#   - Python venv at .venv\ with project installed  (pip install -e ".[dev]")
#   - pyinstaller installed              (.venv\Scripts\pip install pyinstaller)
#   - Node.js / npm installed
#
# Usage: .\scripts\build-electron.ps1 [-SkipFrontend] [-SkipPyinstaller]
param(
    [switch]$SkipFrontend,
    [switch]$SkipPyinstaller
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptDir

# ── Step 1: Build frontend ────────────────────────────────────────────────────
if (-not $SkipFrontend) {
    Write-Host "=== [1/3] Building frontend ==="
    npm --prefix "$Root\frontend" install
    npm --prefix "$Root\frontend" run build
} else {
    Write-Host "=== [1/3] Skipping frontend build ==="
}

if (-not (Test-Path "$Root\frontend\dist")) {
    Write-Error "frontend\dist not found. Run without -SkipFrontend first."
}

# ── Step 2: Bundle Python backend with PyInstaller ───────────────────────────
if (-not $SkipPyinstaller) {
    Write-Host "=== [2/3] Bundling Python backend with PyInstaller ==="

    $PyInstaller = "$Root\.venv\Scripts\pyinstaller.exe"
    if (-not (Test-Path $PyInstaller)) {
        Write-Error "pyinstaller not found in .venv. Run: .venv\Scripts\pip install pyinstaller"
    }

    & $PyInstaller "$Root\server.spec" --noconfirm --distpath "$Root\dist" --workpath "$Root\build\pyinstaller"
} else {
    Write-Host "=== [2/3] Skipping PyInstaller build ==="
}

if (-not (Test-Path "$Root\dist\protein-purification-server")) {
    Write-Error "dist\protein-purification-server not found. Run without -SkipPyinstaller first."
}

# ── Step 3: Package with electron-builder ────────────────────────────────────
Write-Host "=== [3/3] Packaging with electron-builder ==="
npm --prefix "$Root\electron" install
npm --prefix "$Root\electron" run dist

Write-Host ""
Write-Host "Done. Output packages are in release\"
