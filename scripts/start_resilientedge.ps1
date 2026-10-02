# Start the complete ResilientEdge stack. server.ts owns the FastAPI child process.
$ErrorActionPreference = "Stop"
$env:DEMO_MODE = "true"
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Launching ResilientEdge Full Stack" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
if (-not (Test-Path ".\node_modules")) {
    Write-Host "Node dependencies are missing. Run .\scripts\setup_windows.ps1 first." -ForegroundColor Yellow
    exit 1
}
npm run dev
