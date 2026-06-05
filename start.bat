@echo off
title Aegis-Red Launcher
color 0A

echo.
echo  ============================================================
echo    AEGIS-RED  ^|  Autonomous AI Security Framework
echo  ============================================================
echo.

:: ── Resolve project root (directory of this .bat file) ──────────────────────
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"

:: ── Check venv exists ────────────────────────────────────────────────────────
if not exist "%ROOT%\venv\Scripts\python.exe" (
    echo  [ERROR] Virtual environment not found at venv\Scripts\python.exe
    echo          Run: python -m venv venv ^&^& venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

:: ── Check Node / npm ─────────────────────────────────────────────────────────
where npm >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] npm not found. Install Node.js from https://nodejs.org
    pause
    exit /b 1
)

:: ── Kill anything already on port 3000 (Next.js default) ────────────────────
echo  [*] Clearing port 3000...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":3000 " ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

:: ── Install frontend deps if node_modules missing ───────────────────────────
if not exist "%ROOT%\frontend\node_modules" (
    echo  [*] Installing frontend dependencies ^(first run^)...
    pushd "%ROOT%\frontend"
    call npm install
    popd
)

:: ── Start Next.js dashboard in a new window ──────────────────────────────────
echo  [*] Starting Aegis-Red Dashboard ^(Next.js^)...
start "Aegis-Red Dashboard" cmd /k "cd /d "%ROOT%\frontend" && npm run dev"

:: ── Wait for Next.js to be ready ─────────────────────────────────────────────
echo  [*] Waiting for dashboard to come online...
set /a attempts=0
:wait_loop
set /a attempts+=1
if %attempts% gtr 30 (
    echo  [WARN] Dashboard took longer than expected. Opening browser anyway...
    goto open_browser
)
timeout /t 1 /nobreak >nul
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:3000' -UseBasicParsing -TimeoutSec 1; exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 goto wait_loop

:open_browser
echo  [+] Dashboard is up!
echo.
echo  ============================================================
echo    Opening: http://localhost:3000
echo  ============================================================
echo.
start "" "http://localhost:3000"

echo  [+] Aegis-Red is running.
echo  [+] Close the "Aegis-Red Dashboard" window to stop the server.
echo.
echo  To run an attack:
echo    venv\Scripts\python run_attack.py ^<target^> [--iter N]
echo    venv\Scripts\python runner.py --target chatbot --iter 5
echo.
pause
