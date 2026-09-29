# ResilientEdge Windows Setup PowerShell Script
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "ResilientEdge Windows Environment Setup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Check Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "[ERROR] Python is not installed or not in PATH. Please install Python 3.10+." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Detected Python: $(python --version)" -ForegroundColor Green

# 2. Check Node
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeCmd) {
    Write-Host "[ERROR] Node.js is not installed or not in PATH. Please install Node.js 18+." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Detected Node.js: $(node --version)" -ForegroundColor Green

# 3. Create Python Virtual Environment
if (-not (Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment in .venv..." -ForegroundColor Yellow
    python -m venv .venv
}
Write-Host "[OK] Virtual environment ready." -ForegroundColor Green

# 4. Install Python Dependencies
Write-Host "Installing Python requirements..." -ForegroundColor Yellow
& ".\.venv\Scripts\pip.exe" install -r requirements.txt

# 5. Create local environment configuration if needed
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "[OK] Created .env from .env.example" -ForegroundColor Green
}
$envText = Get-Content ".env" -Raw
if ($envText -match 'JWT_SECRET=replace-with-a-random-secret-at-least-32-characters') {
    $secret = python -c "import secrets; print(secrets.token_urlsafe(48))"
    $envText = $envText.Replace('JWT_SECRET=replace-with-a-random-secret-at-least-32-characters', "JWT_SECRET=$secret")
    Set-Content -Path ".env" -Value $envText -NoNewline
    Write-Host "[OK] Generated local JWT_SECRET" -ForegroundColor Green
}

# 6. Install Node Dependencies
Write-Host "Installing NPM dependencies..." -ForegroundColor Yellow
npm install

# 7. Initialize the local database (idempotent)
Write-Host "Initializing SQLite database..." -ForegroundColor Yellow
python -m backend.init_db

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Setup Completed Successfully! Run .\scripts\start_resilientedge.ps1 to start." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
