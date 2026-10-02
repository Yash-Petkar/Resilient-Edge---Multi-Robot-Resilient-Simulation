@echo off
setlocal
cd /d "%~dp0"
set "DEMO_MODE=true"
if not exist ".venv\Scripts\python.exe" (
  echo [INFO] Creating Python virtual environment...
  python -m venv .venv || (echo [ERROR] Python venv creation failed.& exit /b 1)
  call .venv\Scripts\activate.bat
  python -m pip install --upgrade pip
  python -m pip install -r requirements.txt || (echo [ERROR] Python dependency installation failed.& exit /b 1)
)
call .venv\Scripts\activate.bat
.venv\Scripts\python.exe -m uvicorn backend.api.fastapi_app:app --host %BACKEND_HOST% --port %BACKEND_PORT% --reload
