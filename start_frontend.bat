@echo off
setlocal
title ResilientEdge - Frontend & Host

if not exist "node_modules" (
    echo Installing node dependencies...
    call npm install
)

echo Starting ResilientEdge Host at http://localhost:3000 ...
call npm run dev
