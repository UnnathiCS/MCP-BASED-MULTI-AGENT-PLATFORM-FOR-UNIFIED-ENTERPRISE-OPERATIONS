#!/bin/bash

# MCP Multi-Agent Platform - Start All 6 Agents + Streamlit Dashboard
# Usage: bash START_ALL_AGENTS.sh
# Starts all agents in background with logging to /tmp/mcp_logs/

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON3="${PYTHON3:-python3}"

echo "🚀 Starting MCP Multi-Agent Platform..."
echo "=================================="

# Install required Python packages automatically
echo "📦 Installing required Python packages..."
$PYTHON3 -m pip install -q plotly streamlit requests pandas fastapi uvicorn sentence-transformers PyPDF2 torch python-multipart 2>/dev/null && echo "  ✅ Dependencies installed" || true
sleep 1

# Create logs directory
mkdir -p /tmp/mcp_logs

# Kill any existing processes on these ports
echo "🧹 Cleaning up existing processes..."
lsof -ti :8000,:8001,:8002,:8003,:8005,:8007,:8501 2>/dev/null | xargs kill -9 2>/dev/null || true
sleep 2

# Agent 1: Support Agent (Port 8000)
echo "✨ Starting Support Agent (Port 8000)..."
cd "$PROJECT_DIR/Customer_support_agent"
if [ -x ".venv/bin/python" ]; then
  .venv/bin/python main.py > /tmp/mcp_logs/agent_8000.log 2>&1 &
else
  $PYTHON3 main.py > /tmp/mcp_logs/agent_8000.log 2>&1 &
fi
echo "  ✅ Started (PID: $!)"
sleep 1

# Agent 2: Document Review Agent (Port 8001)
echo "✨ Starting Document Agent (Port 8001)..."
cd "$PROJECT_DIR/Document_Review_agent/document_review_agent"
source venv/bin/activate 2>/dev/null || true
$PYTHON3 -m uvicorn app.main:app --port 8001 > /tmp/mcp_logs/agent_8001.log 2>&1 &
echo "  ✅ Started (PID: $!)"
sleep 1

# Agent 3: Meeting Calendar Agent (Port 8002)
echo "✨ Starting Meeting Agent (Port 8002)..."
cd "$PROJECT_DIR/meeting-calendar-agent"
source .venv/bin/activate 2>/dev/null || true
$PYTHON3 -m uvicorn app.main:app --port 8002 > /tmp/mcp_logs/agent_8002.log 2>&1 &
echo "  ✅ Started (PID: $!)"
sleep 1

# Agent 4: HR Onboarding Agent (Port 8003)
echo "✨ Starting HR Onboarding Agent (Port 8003)..."
cd "$PROJECT_DIR/HR_Onboarding_agent"
$PYTHON3 -m uvicorn app.main:app --port 8003 > /tmp/mcp_logs/agent_8003.log 2>&1 &
echo "  ✅ Started (PID: $!)"
sleep 1

# Agent 4.5: Email Agent (Port 8004)
echo "✨ Starting Email Agent (Port 8004)..."
cd "$PROJECT_DIR/Email_agent"
$PYTHON3 -m uvicorn app.main:app --host 127.0.0.1 --port 8004 > /tmp/mcp_logs/agent_8004.log 2>&1 &
echo "  ✅ Started (PID: $!)"
sleep 1

# Agent 5: Project Management Agent (Port 8005)
echo "✨ Starting Project Management Agent (Port 8005)..."
cd "$PROJECT_DIR/Project_Management_agent"
$PYTHON3 -m uvicorn app.main:app --port 8005 > /tmp/mcp_logs/agent_8005.log 2>&1 &
echo "  ✅ Started (PID: $!)"
sleep 1

# Agent 6: Analytics Agent (Port 8007)
echo "✨ Starting Analytics Agent (Port 8007)..."
cd "$PROJECT_DIR/Analytics_agent"
$PYTHON3 -m uvicorn app.main:app --port 8007 > /tmp/mcp_logs/agent_8007.log 2>&1 &
echo "  ✅ Started (PID: $!)"
sleep 2

# Start Streamlit Dashboard (Port 8501)
echo "✨ Starting Streamlit Dashboard (Port 8501)..."
cd "$PROJECT_DIR"
streamlit run app.py --server.port 8501 > /tmp/mcp_logs/streamlit_8501.log 2>&1 &
echo "  ✅ Started (PID: $!)"

echo ""
echo "=================================="
echo "✅ All 6 Agents Started!"
echo "=================================="
echo ""
echo "📊 Agent Ports:"
echo "  • Support Agent:          http://localhost:8000"
echo "  • Document Agent:         http://localhost:8001"
echo "  • Meeting Agent:          http://localhost:8002"
echo "  • HR Onboarding Agent:    http://localhost:8003"
echo "  • Project Management:     http://localhost:8005"
echo "  • Analytics Agent:        http://localhost:8007"
echo ""
echo "🎨 Dashboard:"
echo "  • Streamlit Dashboard:    http://localhost:8501"
echo ""
echo "📋 View Logs:"
echo "  • tail -f /tmp/mcp_logs/agent_800*.log"
echo "  • tail -f /tmp/mcp_logs/streamlit_8501.log"
echo ""
echo "🛑 Stop All:"
echo "  • pkill -f 'port 800'"
echo "  • pkill -f streamlit"
echo ""

# Wait a few seconds and health check
sleep 3

echo "🔍 Health Checks:"
for port in 8000 8001 8002 8003 8005 8007; do
  response=$(curl -s http://localhost:$port/health 2>/dev/null || echo "")
  if echo "$response" | grep -q "ok"; then
    echo "  ✅ Port $port: Running"
  else
    echo "  ⏳ Port $port: Initializing..."
  fi
done

echo ""
echo "🎉 MCP Platform Ready!"
echo "   Dashboard: http://localhost:8501"
echo ""
