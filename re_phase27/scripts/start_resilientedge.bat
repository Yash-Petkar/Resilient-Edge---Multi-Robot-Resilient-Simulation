@echo off
setlocal
set "DEMO_MODE=true"
title ResilientEdge - Full Stack
echo ============================================================
echo Launching ResilientEdge Full Stack
echo ============================================================
if not exist "node_modules" (
  echo [ERROR] Node dependencies are missing. Run scripts\setup_windows.bat first.
  pause
  exit /b 1
)
call npm run dev
