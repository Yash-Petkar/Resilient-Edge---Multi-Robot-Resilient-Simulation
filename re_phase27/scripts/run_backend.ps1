# ResilientEdge Windows Run Backend Script
Write-Host "Starting ResilientEdge FastAPI Backend on Windows..." -ForegroundColor Cyan
$backendHost = if ($env:BACKEND_HOST) { $env:BACKEND_HOST } else { "127.0.0.1" }
$backendPort = if ($env:BACKEND_PORT) { $env:BACKEND_PORT } else { "8000" }
if (Test-Path ".\.venv\Scripts\uvicorn.exe") {
    & ".\.venv\Scripts\uvicorn.exe" backend.api.fastapi_app:app --host $backendHost --port $backendPort --reload
} else {
    python -m uvicorn backend.api.fastapi_app:app --host $backendHost --port $backendPort --reload
}
