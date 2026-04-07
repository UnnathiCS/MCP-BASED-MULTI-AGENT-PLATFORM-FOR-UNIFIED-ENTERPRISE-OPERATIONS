#!/bin/bash
# Complete startup script for MCP Multi-Agent System with LangGraph

echo "🚀 MCP Multi-Agent System - Complete Startup"
echo "=============================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Groq API key is set
if [ -z "$GROQ_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  GROQ_API_KEY not set in environment${NC}"
    echo ""
    echo "Checking for .env file in Customer_support_agent..."
    
    if [ -f "Customer_support_agent/.env" ]; then
        echo -e "${GREEN}✅ Found .env file${NC}"
        export $(grep GROQ_API_KEY Customer_support_agent/.env | xargs)
    else
        echo -e "${RED}❌ No .env file found${NC}"
        echo ""
        echo "Please create Customer_support_agent/.env with your Groq API key:"
        echo "GROQ_API_KEY=gsk_YOUR_KEY_HERE"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Groq API Key configured${NC}"
echo ""

# Function to check if port is in use
check_port() {
    lsof -i :$1 > /dev/null 2>&1
    return $?
}

# Check ports
echo "Checking required ports..."
for port in 8000 8001 8501; do
    if check_port $port; then
        echo -e "${YELLOW}⚠️  Port $port is already in use${NC}"
    else
        echo -e "${GREEN}✅ Port $port is free${NC}"
    fi
done

echo ""
echo "Ready to start! In 3 separate terminals, run:"
echo ""
echo -e "${BLUE}Terminal 1 (Support Agent with LangGraph):${NC}"
echo "cd ~/Documents/SEM-6/MINI-PROJECT/Customer_support_agent"
echo ". .venv/bin/activate"
echo "python -m uvicorn main:app --reload --port 8000"
echo ""
echo -e "${BLUE}Terminal 2 (Document Review Agent):${NC}"
echo "cd ~/Documents/SEM-6/MINI-PROJECT/Document_Review_agent/document_review_agent"
echo ". .venv/bin/activate"
echo "python -m uvicorn app.main:app --reload --port 8001"
echo ""
echo -e "${BLUE}Terminal 3 (Streamlit Dashboard):${NC}"
echo "cd ~/Documents/SEM-6/MINI-PROJECT"
echo "streamlit run app.py"
echo ""
echo -e "${GREEN}Open: http://localhost:8501${NC}"
