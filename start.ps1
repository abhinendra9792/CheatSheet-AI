# AI Cheatsheet Generator - Start Both Servers
# Usage: .\start.ps1

$ErrorActionPreference = "SilentlyContinue"
$Root = $PSScriptRoot
if (-not $Root) { $Root = (Get-Location).Path }

Write-Host ""
Write-Host "  ========================================" -ForegroundColor Magenta
Write-Host "    AI Cheatsheet Generator - Full Stack  " -ForegroundColor Magenta
Write-Host "  ========================================" -ForegroundColor Magenta
Write-Host ""

# Step 1: Install backend deps
Write-Host "  [1/4] Checking backend dependencies..." -ForegroundColor Yellow
Set-Location "$Root\backend"
$installed = pip show fastapi 2>$null
if (-not $installed) {
    Write-Host "    Installing requirements..." -ForegroundColor Gray
    pip install -r requirements.txt --quiet 2>$null
}
Write-Host "    [OK] Backend deps ready" -ForegroundColor Green

# Step 2: Install frontend deps
Write-Host "  [2/4] Checking frontend dependencies..." -ForegroundColor Yellow
Set-Location "$Root\frontend"
if (-not (Test-Path "node_modules")) {
    Write-Host "    Running npm install..." -ForegroundColor Gray
    npm install --silent 2>$null
}
Write-Host "    [OK] Frontend deps ready" -ForegroundColor Green

# Step 3: Start backend in new window
Write-Host "  [3/4] Starting Backend (FastAPI :8000)..." -ForegroundColor Yellow
$backendCmd = "Set-Location '" + $Root + "\backend'; Write-Host '  Backend: http://localhost:8000' -ForegroundColor Cyan; Write-Host '  Docs:    http://localhost:8000/docs' -ForegroundColor Cyan; Write-Host ''; python -m uvicorn api_server:app --reload --port 8000; Read-Host 'Press Enter'"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd
Write-Host "    [OK] Backend started in new window" -ForegroundColor Green

# Wait for backend to boot
Write-Host "    Waiting for backend to start..." -ForegroundColor Gray
Start-Sleep -Seconds 4

# Step 4: Start frontend in new window
Write-Host "  [4/4] Starting Frontend (Vite :5173)..." -ForegroundColor Yellow
$frontendCmd = "Set-Location '" + $Root + "\frontend'; Write-Host '  Frontend: http://localhost:5173' -ForegroundColor Magenta; Write-Host ''; npx vite --host; Read-Host 'Press Enter'"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd
Write-Host "    [OK] Frontend started in new window" -ForegroundColor Green

# Done
Write-Host ""
Write-Host "  ========================================" -ForegroundColor Green
Write-Host "       BOTH SERVERS RUNNING!              " -ForegroundColor Green
Write-Host "  ========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Frontend:  http://localhost:5173" -ForegroundColor Cyan
Write-Host "  Backend:   http://localhost:8000" -ForegroundColor Cyan
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Close the two terminal windows to stop." -ForegroundColor Yellow
Write-Host ""

# Open browser
Start-Sleep -Seconds 3
Start-Process "http://localhost:5173"

Set-Location $Root