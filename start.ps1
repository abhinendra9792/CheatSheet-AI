# ═══════════════════════════════════════════════════════════════
# AI Cheatsheet Generator — Start Both Servers
# Usage: .\start.ps1
# ═══════════════════════════════════════════════════════════════

$ErrorActionPreference = "SilentlyContinue"
$Root = $PSScriptRoot

Write-Host ""
Write-Host "  ========================================" -ForegroundColor Cyan
Write-Host "    AI Cheatsheet Generator - Full Stack  " -ForegroundColor Cyan
Write-Host "  ========================================" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Install backend deps ──
Write-Host "  [1/4] Checking backend dependencies..." -ForegroundColor Yellow
Set-Location "$Root\backend"
$installed = pip show fastapi 2>$null
if (-not $installed) {
    Write-Host "    Installing fastapi, uvicorn, python-multipart..." -ForegroundColor Gray
    pip install fastapi uvicorn python-multipart --quiet 2>$null
}
Write-Host "    Done!" -ForegroundColor Green

# ── Step 2: Install frontend deps ──
Write-Host "  [2/4] Checking frontend dependencies..." -ForegroundColor Yellow
Set-Location "$Root\frontend"
if (-not (Test-Path "node_modules")) {
    Write-Host "    Running npm install..." -ForegroundColor Gray
    npm install --silent 2>$null
}
Write-Host "    Done!" -ForegroundColor Green

# ── Step 3: Start backend in new window ──
Write-Host "  [3/4] Starting Backend (FastAPI :8000)..." -ForegroundColor Yellow
$backendCmd = "cd '$Root\backend'; Write-Host ''; Write-Host '  Backend Server (FastAPI)' -ForegroundColor Cyan; Write-Host '  http://localhost:8000' -ForegroundColor Green; Write-Host '  http://localhost:8000/docs' -ForegroundColor Green; Write-Host ''; python api_server.py; Read-Host 'Press Enter to close'"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -WindowStyle Normal
Write-Host "    Started in new window!" -ForegroundColor Green

# Wait for backend to boot
Write-Host "    Waiting for backend to start..." -ForegroundColor Gray
Start-Sleep -Seconds 3

# ── Step 4: Start frontend in new window ──
Write-Host "  [4/4] Starting Frontend (Vite :5173)..." -ForegroundColor Yellow
$frontendCmd = "cd '$Root\frontend'; Write-Host ''; Write-Host '  Frontend Server (Vite + React)' -ForegroundColor Cyan; Write-Host '  http://localhost:5173' -ForegroundColor Green; Write-Host ''; npx vite --host; Read-Host 'Press Enter to close'"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd -WindowStyle Normal
Write-Host "    Started in new window!" -ForegroundColor Green

# ── Done ──
Write-Host ""
Write-Host "  ========================================" -ForegroundColor Green
Write-Host "          BOTH SERVERS RUNNING!            " -ForegroundColor Green
Write-Host "  ========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Frontend:  http://localhost:5173" -ForegroundColor Cyan
Write-Host "  Backend:   http://localhost:8000" -ForegroundColor Cyan
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Close the two terminal windows to stop." -ForegroundColor Yellow
Write-Host ""

# Open browser
Start-Sleep -Seconds 2
Start-Process "http://localhost:5173"
 