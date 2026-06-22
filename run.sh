#!/usr/bin/env bash
# ── RupeeRadar Launcher (Unix) ──
# Starts both backend and frontend development servers.
# Usage: bash run.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        RupeeRadar Launcher           ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════╝${NC}"
echo ""

# ── Check Python ──
echo -e "${YELLOW}[1/4] Checking Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3.10+ is required but not found."
    exit 1
fi
echo "  Python $(python3 --version | cut -d' ' -f2)"

# ── Check Node.js ──
echo -e "${YELLOW}[2/4] Checking Node.js...${NC}"
if ! command -v node &> /dev/null; then
    echo "Error: Node.js 18+ is required but not found."
    exit 1
fi
echo "  Node.js $(node --version | cut -d'v' -f2)"

# ── Setup Backend ──
echo -e "${YELLOW}[3/4] Setting up backend...${NC}"
cd backend

# Create .env if not exists
if [ ! -f .env ]; then
    cp .env.example .env 2>/dev/null || true
    echo "  Created .env from .env.example"
fi

# Install Python deps if needed
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "  Created virtual environment"
fi
source venv/bin/activate
pip install -q -r requirements.txt > /dev/null 2>&1
echo "  Python dependencies installed"

cd ..

# ── Setup Frontend ──
echo -e "${YELLOW}[4/4] Setting up frontend...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    npm install --silent 2>/dev/null
    echo "  Node dependencies installed"
fi
cd ..

echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  Starting servers...${NC}"
echo -e "${GREEN}  Backend:  http://localhost:8000${NC}"
echo -e "${GREEN}  Frontend: http://localhost:5173${NC}"
echo -e "${GREEN}  API Docs: http://localhost:8000/docs${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo "Press Ctrl+C to stop both servers."
echo ""

# Start backend in background
cd backend
source venv/bin/activate 2>/dev/null || true
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Start frontend
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Trap Ctrl+C to kill both
trap "echo ''; echo 'Shutting down...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM

# Wait for either to exit
wait $BACKEND_PID $FRONTEND_PID 2>/dev/null
