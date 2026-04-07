#!/bin/bash

# LangGraph Multi-Agent System - Quick Start
# This script starts all 3 services with proper virtual environment activation

set -e

PROJECT_DIR="/Users/unnathics/Documents/SEM-6/MINI-PROJECT"
VENV="$PROJECT_DIR/Customer_support_agent/.venv"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  LangGraph Multi-Agent System - Quick Start                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"

# Kill any existing processes
echo -e "\n${YELLOW}Cleaning up old processes...${NC}"
pkill -f "python.*main.py" || true
pkill -f "streamlit run" || true
sleep 2

# Verify venv exists
if [ ! -d "$VENV" ]; then
    echo -e "${YELLOW}Error: Virtual environment not found at $VENV${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Virtual environment found${NC}"

# Start Support Agent
echo -e "\n${BLUE}Starting Support Agent (port 8000)...${NC}"
"$VENV/bin/python" "$PROJECT_DIR/Customer_support_agent/main.py" > /tmp/support_agent.log 2>&1 &
SUPPORT_PID=$!
echo -e "${GREEN}✓ Support Agent started (PID: $SUPPORT_PID)${NC}"

# Wait for it to start
sleep 3

# Verify it's running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Support Agent responding${NC}"
else
    echo -e "${YELLOW}⚠ Support Agent not responding yet, check logs:${NC}"
    echo "  tail -f /tmp/support_agent.log"
fi

# Start Document Agent
echo -e "\n${BLUE}Starting Document Review Agent (port 8001)...${NC}"
cd "$PROJECT_DIR/Document_Review_agent/document_review_agent"
"$VENV/bin/python" -m uvicorn app.main:app --port 8001 > /tmp/document_agent.log 2>&1 &
DOC_PID=$!
echo -e "${GREEN}✓ Document Agent started (PID: $DOC_PID)${NC}"

# Wait for it to start
sleep 2

# Start Streamlit
echo -e "\n${BLUE}Starting Streamlit Dashboard (port 8501)...${NC}"
cd "$PROJECT_DIR"
"$VENV/bin/python" -m streamlit run app.py > /tmp/streamlit.log 2>&1 &
STREAMLIT_PID=$!
echo -e "${GREEN}✓ Streamlit started (PID: $STREAMLIT_PID)${NC}"

# Summary
echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ All services started!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"

echo -e "\n${GREEN}Access your services:${NC}"
echo "  • Streamlit Dashboard: http://localhost:8501"
echo "  • Support Agent API: http://localhost:8000"
echo "  • Document Agent API: http://localhost:8001"

echo -e "\n${GREEN}Monitor logs:${NC}"
echo "  tail -f /tmp/support_agent.log"
echo "  tail -f /tmp/document_agent.log"
echo "  tail -f /tmp/streamlit.log"

echo -e "\n${GREEN}Stop services:${NC}"
echo "  pkill -f 'python.*main.py'"
echo "  pkill -f 'streamlit run'"
echo "  Or press Ctrl+C"

echo -e "\n${YELLOW}Waiting for services to fully initialize...${NC}"
sleep 3

echo -e "\n${GREEN}✓ Ready! Open browser to: http://localhost:8501${NC}\n"

# Keep the script running so processes don't terminate
wait
