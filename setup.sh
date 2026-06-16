#!/usr/bin/env bash
# setup.sh — One-command setup for Aegis-Red on Linux / macOS
# Usage: bash setup.sh

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "============================================================"
echo "   AEGIS-RED  |  Autonomous AI Security Framework"
echo "   Setup Script"
echo "============================================================"
echo ""

# 1. Check Python
if ! command -v python3 &>/dev/null; then
  echo -e "${RED}[ERROR] python3 not found. Install Python 3.10+ and re-run.${NC}"
  exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${GREEN}[+] Python ${PYTHON_VERSION} found.${NC}"

# 2. Check Node/npm
if ! command -v npm &>/dev/null; then
  echo -e "${RED}[ERROR] npm not found. Install Node.js from https://nodejs.org${NC}"
  exit 1
fi
echo -e "${GREEN}[+] npm $(npm --version) found.${NC}"

# 3. Create venv if it doesn't exist
if [ ! -f "venv/bin/python" ]; then
  echo -e "${YELLOW}[*] Creating virtual environment...${NC}"
  python3 -m venv venv
fi

# 4. Install Python deps
echo -e "${YELLOW}[*] Installing Python dependencies...${NC}"
venv/bin/pip install --upgrade pip -q
venv/bin/pip install -r requirements.txt -q

# 5. Install Playwright browsers
echo -e "${YELLOW}[*] Installing Playwright browser (Chromium)...${NC}"
venv/bin/playwright install chromium

# 6. Set up .env if not present
if [ ! -f ".env" ]; then
  echo -e "${YELLOW}[*] Creating .env from .env.example — fill in your API keys!${NC}"
  cp .env.example .env
fi

# 7. Install frontend deps
echo -e "${YELLOW}[*] Installing frontend dependencies...${NC}"
cd frontend
if [ ! -f ".env.local" ]; then
  echo -e "${YELLOW}[*] Creating frontend/.env.local from .env.example — fill in your keys!${NC}"
  cp .env.example .env.local
fi
npm install --silent
cd ..

echo ""
echo "============================================================"
echo -e "${GREEN}[+] Setup complete!${NC}"
echo ""
echo "  Start the dashboard:  cd frontend && npm run dev"
echo "  Start the backend:    venv/bin/uvicorn backend.main:app --reload"
echo "  Run an attack:        venv/bin/python run_attack.py https://target.com"
echo "============================================================"
echo ""
