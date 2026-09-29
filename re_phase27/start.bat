@echo off
setlocal
cd /d "%~dp0"
set "DEMO_MODE=true"
set "VITE_DEMO_MODE=true"
title ResilientEdge - Full Stack
echo ============================================================
echo ResilientEdge Full Stack
echo ============================================================
if not exist ".venv\Scripts\python.exe" (
  echo [INFO] First run detected: creating Python virtual environment...
  python -m venv .venv || (echo [ERROR] Python is unavailable or venv creation failed.& pause& exit /b 1)
  call .venv\Scripts\activate.bat
  python -m pip install --upgrade pip
  python -m pip install -r requirements.txt || (echo [ERROR] Python dependency installation failed.& pause& exit /b 1)
  python -m backend.init_db || (echo [ERROR] Database initialization failed.& pause& exit /b 1)
)
if not exist "node_modules" (
  echo [INFO] Installing Node dependencies...
  npm install || (echo [ERROR] Node dependency installation failed.& pause& exit /b 1)
)
call npm run dev
