#!/bin/bash

# ============================================================================
#  UrjaAI Special Features - Multi-Service Startup Script
# ============================================================================
#
# This script starts all three required services for the UrjaAI platform
# with integrated browniepoint1 and browniepoint2 features.
#
# Prerequisites:
#   - Python 3.8+ installed
#   - Node.js 16+ installed
#   - All dependencies installed (requirements.txt, package.json)
#
# Usage: bash START_ALL_SERVICES.sh
# ============================================================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "============================================================================"
echo "  UrjaAI Special Features - Starting All Services"
echo "============================================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is not installed. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js is not installed. Please install Node.js 16 or higher.${NC}"
    exit 1
fi

echo -e "${BLUE}✓ Python and Node.js detected. Starting services...${NC}"
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${RED}Stopping all services...${NC}"
    kill $PID1 $PID2 $PID3 $PID4 2>/dev/null
    exit 0
}

# Set trap to cleanup on Ctrl+C
trap cleanup SIGINT SIGTERM

# Start Terminal 1: UrjaAI Backend
echo -e "${YELLOW}Terminal 1: Starting UrjaAI Backend (FastAPI on port 8000)...${NC}"
cd "$SCRIPT_DIR/UrjaAI/backend"
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > /tmp/urjaai_backend.log 2>&1 &
PID1=$!
sleep 2

# Start Terminal 2: Browniepoint1 (Carbon Tracker)
echo -e "${YELLOW}Terminal 2: Starting Browniepoint1 - Carbon Tracker (Flask on port 5000)...${NC}"
cd "$SCRIPT_DIR/browniepoint1"
python3 api_server.py > /tmp/browniepoint1.log 2>&1 &
PID2=$!
sleep 2

# Start Terminal 3: Browniepoint2 (ML Platform)
echo -e "${YELLOW}Terminal 3: Starting Browniepoint2 - TabTransformer ML (FastAPI on port 8001)...${NC}"
cd "$SCRIPT_DIR/browniepoint2"
python3 main_app.py --port 8001 > /tmp/browniepoint2.log 2>&1 &
PID3=$!
sleep 2

# Start Terminal 4: UrjaAI Frontend
echo -e "${YELLOW}Terminal 4: Starting UrjaAI Frontend (Vite on port 5173)...${NC}"
cd "$SCRIPT_DIR/UrjaAI/frontend"
npm run dev > /tmp/urjaai_frontend.log 2>&1 &
PID4=$!
sleep 2

echo ""
echo "============================================================================"
echo -e "${GREEN}✓ All services started successfully!${NC}"
echo "============================================================================"
echo ""
echo "Service URLs:"
echo -e "  ${BLUE}Frontend Dashboard: http://localhost:5173${NC}"
echo -e "  ${BLUE}Special Features:  http://localhost:5173/special-features${NC}"
echo -e "  ${BLUE}UrjaAI API Docs:   http://localhost:8000/docs${NC}"
echo -e "  ${BLUE}Browniepoint1:     http://localhost:5000${NC}"
echo -e "  ${BLUE}Browniepoint2:     http://localhost:8001/docs${NC}"
echo ""
echo "Quick Links:"
echo -e "  ${YELLOW}1. Login to http://localhost:5173/login${NC}"
echo -e "  ${YELLOW}2. Navigate to Special Features (🎉 icon)${NC}"
echo -e "  ${YELLOW}3. Switch between Carbon Tracker and ML Platform tabs${NC}"
echo ""
echo "Log Files:"
echo -e "  ${BLUE}/tmp/urjaai_backend.log${NC}"
echo -e "  ${BLUE}/tmp/browniepoint1.log${NC}"
echo -e "  ${BLUE}/tmp/browniepoint2.log${NC}"
echo -e "  ${BLUE}/tmp/urjaai_frontend.log${NC}"
echo ""
echo "Press Ctrl+C to stop all services"
echo "============================================================================"
echo ""

# Wait for all processes
wait $PID1 $PID2 $PID3 $PID4
