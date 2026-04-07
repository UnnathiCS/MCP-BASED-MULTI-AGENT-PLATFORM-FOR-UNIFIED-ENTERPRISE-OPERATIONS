#!/bin/bash

# LangGraph Multi-Agent System - Complete Startup Guide
# This guide will help you start all services and verify everything is working

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  LangGraph Multi-Agent System - Complete Startup Guide         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"

# Step 1: Verify setup
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STEP 1: Verifying LangGraph Setup${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

python3 verify_langgraph_setup.py

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Setup verification failed. Please fix the issues above.${NC}"
    exit 1
fi

echo -e "\n${GREEN}✓ All verifications passed!${NC}"

# Step 2: Ask user if they want to start services
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STEP 2: Ready to Start Services${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${YELLOW}This will start 3 services:${NC}"
echo "  • Support Agent API (port 8000) - FastAPI with LangGraph"
echo "  • Document Review Agent (port 8001) - FastAPI"  
echo "  • Streamlit Dashboard (port 8501) - Web UI"
echo ""
echo -e "${YELLOW}Make sure you have 3 terminal windows open or use tmux/screen.${NC}"

read -p "Do you want to start all services now? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Skipping service startup.${NC}"
    echo ""
    echo -e "${BLUE}Manual startup commands:${NC}"
    echo "  Terminal 1: cd Customer_support_agent && python main.py"
    echo "  Terminal 2: cd Document_Review_agent/document_review_agent && python -m uvicorn app.main:app --port 8001"
    echo "  Terminal 3: streamlit run app.py"
    exit 0
fi

# Step 3: Start services
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STEP 3: Starting Services${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Function to check if port is available
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port in use
    else
        return 1  # Port available
    fi
}

# Check ports
echo -e "\n${YELLOW}Checking ports...${NC}"
if check_port 8000; then
    echo -e "${YELLOW}⚠ Port 8000 already in use (Support Agent)${NC}"
fi
if check_port 8001; then
    echo -e "${YELLOW}⚠ Port 8001 already in use (Document Agent)${NC}"
fi
if check_port 8501; then
    echo -e "${YELLOW}⚠ Port 8501 already in use (Streamlit)${NC}"
fi

echo -e "\n${GREEN}Starting Support Agent on port 8000...${NC}"
cd Customer_support_agent
python main.py > /tmp/support_agent.log 2>&1 &
SUPPORT_PID=$!
echo "Support Agent PID: $SUPPORT_PID"
cd ..

sleep 2

echo -e "${GREEN}Starting Document Review Agent on port 8001...${NC}"
cd Document_Review_agent/document_review_agent
python -m uvicorn app.main:app --port 8001 > /tmp/document_agent.log 2>&1 &
DOC_PID=$!
echo "Document Agent PID: $DOC_PID"
cd ../../

sleep 2

echo -e "${GREEN}Starting Streamlit Dashboard on port 8501...${NC}"
streamlit run app.py > /tmp/streamlit.log 2>&1 &
STREAMLIT_PID=$!
echo "Streamlit PID: $STREAMLIT_PID"

# Step 4: Verification
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STEP 4: Verifying Services${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

sleep 3

echo -e "\nChecking service status..."

# Check Support Agent
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Support Agent (port 8000) - Running${NC}"
else
    echo -e "${RED}✗ Support Agent (port 8000) - Not responding${NC}"
    echo "  Check logs: tail -f /tmp/support_agent.log"
fi

# Check Document Agent
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Document Agent (port 8001) - Running${NC}"
else
    echo -e "${RED}✗ Document Agent (port 8001) - Not responding${NC}"
    echo "  Check logs: tail -f /tmp/document_agent.log"
fi

# Check Streamlit (note: Streamlit doesn't have /health endpoint, so we check if port is listening)
if lsof -Pi :8501 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Streamlit Dashboard (port 8501) - Running${NC}"
else
    echo -e "${YELLOW}⚠ Streamlit Dashboard (port 8501) - Checking...${NC}"
    echo "  Check logs: tail -f /tmp/streamlit.log"
fi

# Step 5: Summary
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}STEP 5: Access Your Services${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${GREEN}Services are starting! Access them at:${NC}"
echo "  • Streamlit Dashboard: http://localhost:8501"
echo "  • Support Agent API: http://localhost:8000"
echo "  • Document Agent API: http://localhost:8001"

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Next: Test LangGraph Integration${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\nTo verify LangGraph is working:"
echo "  1. Open another terminal in the project root"
echo "  2. Run: ${GREEN}python3 test_langgraph.py${NC}"
echo ""
echo "This will:"
echo "  • Test 3 different support requests"
echo "  • Show LangGraph processing steps"
echo "  • Display LLM reasoning from Groq"
echo "  • Verify all 4 nodes are executing"

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Helpful Commands${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo ""
echo -e "${YELLOW}View Logs:${NC}"
echo "  tail -f /tmp/support_agent.log"
echo "  tail -f /tmp/document_agent.log"
echo "  tail -f /tmp/streamlit.log"

echo ""
echo -e "${YELLOW}Stop Services:${NC}"
echo "  kill $SUPPORT_PID      # Stop Support Agent"
echo "  kill $DOC_PID          # Stop Document Agent"
echo "  kill $STREAMLIT_PID    # Stop Streamlit"
echo "  kill $SUPPORT_PID $DOC_PID $STREAMLIT_PID  # Stop all"

echo ""
echo -e "${YELLOW}Test LLM Decision Making:${NC}"
echo "  curl -X POST http://localhost:8000/debug/test-langgraph \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"ticket_id\": \"test\", \"message\": \"My VPN is not working\"}'"

echo ""
echo -e "${YELLOW}Get Workflow Visualization:${NC}"
echo "  curl http://localhost:8000/graph/visualization"
echo "  curl http://localhost:8000/graph/mermaid"

echo -e "\n${GREEN}✓ Setup complete! Happy testing!${NC}\n"
