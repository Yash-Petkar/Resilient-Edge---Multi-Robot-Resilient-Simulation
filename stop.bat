@echo off
setlocal
echo Stopping all ResilientEdge background processes...

taskkill /F /IM node.exe >nul 2>nul
taskkill /F /IM python.exe >nul 2>nul
taskkill /F /IM py.exe >nul 2>nul

echo ResilientEdge stopped successfully.
