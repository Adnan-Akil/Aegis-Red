@echo off
title Aegis-Red Setup
color 0A

echo.
echo  ============================================================
echo    AEGIS-RED  ^|  Autonomous AI Security Framework
echo    Setup Script (Windows)
echo  ============================================================
echo.

:: ── Resolve project root ──────────────────────────────────────────────────────
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"

:: ── Check Python ──────────────────────────────────────────────────────────────
where python >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Install Python 3.10+ from https://python.org
    pause
    exit /b 1
)
echo  [+] Python found.

:: ── Check Node/npm ────────────────────────────────────────────────────────────
where npm >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] npm not found. Install Node.js from https://nodejs.org
    pause
    exit /b 1
)
echo  [+] npm found.

:: ── Create venv ───────────────────────────────────────────────────────────────
if not exist "%ROOT%\venv\Scripts\python.exe" (
    echo  [*] Creating virtual environment...
    python -m venv "%ROOT%\venv"
)

:: ── Install Python deps ───────────────────────────────────────────────────────
echo  [*] Installing Python dependencies...
"%ROOT%\venv\Scripts\pip" install --upgrade pip -q
"%ROOT%\venv\Scripts\pip" install -r "%ROOT%\requirements.txt" -q

:: ── Install Playwright browsers ───────────────────────────────────────────────
echo  [*] Installing Playwright browser (Chromium)...
"%ROOT%\venv\Scripts\playwright" install chromium

:: ── Set up .env ───────────────────────────────────────────────────────────────
if not exist "%ROOT%\.env" (
    echo  [*] Creating .env from .env.example -- fill in your API keys!
    copy "%ROOT%\.env.example" "%ROOT%\.env" >nul
)

:: ── Install frontend deps ─────────────────────────────────────────────────────
echo  [*] Installing frontend dependencies...
if not exist "%ROOT%\frontend\.env.local" (
    echo  [*] Creating frontend\.env.local from .env.example -- fill in your keys!
    copy "%ROOT%\frontend\.env.example" "%ROOT%\frontend\.env.local" >nul
)
pushd "%ROOT%\frontend"
call npm install --silent
popd

echo.
echo  ============================================================
echo  [+] Setup complete!
echo.
echo    Start the dashboard:  cd frontend ^&^& npm run dev
echo    Start the backend:    venv\Scripts\python run_backend.py
echo    Run an attack:        venv\Scripts\python run_attack.py https://target.com
echo  ============================================================
echo.
pause
