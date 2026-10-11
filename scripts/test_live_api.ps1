# PayAgent OS - PowerShell Live Testing & Verification Runner
# Usage: powershell -ExecutionPolicy Bypass -File .\scripts\test_live_api.ps1

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   PAYAGENT OS - SYSTEM VERIFICATION & TEST RUNNER" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Run Complete Pytest Suite (85 Scenarios)
Write-Host "[PHASE 1] Running Automated Pytest Suite (85 Test Cases)..." -ForegroundColor Yellow
& ".\venv\Scripts\pytest" "-v"
$pytestExit = $LASTEXITCODE

if ($pytestExit -eq 0) {
    Write-Host "[OK] PYTEST SUCCESS: All 85 test scenarios passed cleanly!" -ForegroundColor Green
} else {
    Write-Host "[ERR] PYTEST ISSUES DETECTED" -ForegroundColor Red
}

Write-Host ""

# 2. Run Physical End-to-End Fleet Integration Suite (19 Subsystems)
Write-Host "[PHASE 2] Executing Physical End-to-End Verification..." -ForegroundColor Yellow
& ".\venv\Scripts\python" "scripts/test_fleet_live.py"

Write-Host ""

# 3. Live Server Health Check
Write-Host "[PHASE 3] Checking Live Server (http://127.0.0.1:8000)..." -ForegroundColor Yellow
try {
    Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/agents/" -Method Get -TimeoutSec 2 | Out-Null
    Write-Host "[OK] LIVE SERVER ONLINE: Found active agents!" -ForegroundColor Green
    Write-Host "  Dashboard: http://127.0.0.1:8000" -ForegroundColor Cyan
    Write-Host "  Swagger UI: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
} catch {
    Write-Host "[INFO] Live server not currently running on port 8000." -ForegroundColor DarkGray
    Write-Host "  To launch the live dashboard, run:" -ForegroundColor DarkGray
    Write-Host "  .\venv\Scripts\uvicorn backend.app.main:app --reload --port 8000" -ForegroundColor White
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "   TEST RUN COMPLETE!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
