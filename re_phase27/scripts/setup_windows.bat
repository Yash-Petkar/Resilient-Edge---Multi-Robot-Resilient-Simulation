@echo off
setlocal
title ResilientEdge - Windows Setup
echo ============================================================
echo ResilientEdge Windows Setup
echo ============================================================
where python >nul 2>nul || (echo [ERROR] Python is not installed or not in PATH.& pause& exit /b 1)
where node >nul 2>nul || (echo [ERROR] Node.js is not installed or not in PATH.& pause& exit /b 1)
if not exist ".venv\Scripts\python.exe" python -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt || (echo [ERROR] Python dependency installation failed.& pause& exit /b 1)
if not exist ".env" copy /Y .env.example .env >nul
python -c "from pathlib import Path; import secrets; p=Path('.env'); s=p.read_text(); s=s.replace('JWT_SECRET=replace-with-a-random-secret-at-least-32-characters','JWT_SECRET='+secrets.token_urlsafe(48)); p.write_text(s) if 'JWT_SECRET=replace-with-a-random-secret-at-least-32-characters' in p.read_text() else None"
npm install || (echo [ERROR] Node dependency installation failed.& pause& exit /b 1)
python -m backend.init_db
echo.
echo Setup complete. Run scripts\start_resilientedge.bat
pause
