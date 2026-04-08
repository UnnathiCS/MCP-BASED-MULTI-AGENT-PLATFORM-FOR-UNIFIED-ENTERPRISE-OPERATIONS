#!/bin/bash

# START_ALL_AGENTS.sh
# Starts all 3 MCP agents + Streamlit dashboard in separate terminal windows
# For macOS and Linux

set -e

PROJECT_DIR="$HOME/Documents/SEM-6/MINI-PROJECT"

echo "=========================================="
echo "Starting MCP Multi-Agent System"
echo "=========================================="
echo ""
echo "This will start:"
echo "  ✓ Support Agent (Port 8000)"
echo "  ✓ Document Agent (Port 8001)"
echo "  ✓ Meeting Agent (Port 8002)"
echo "  ✓ Streamlit Dashboard (Port 8501)"
echo ""
echo "=========================================="

# Function to start a service in a new terminal tab (macOS)
start_service_mac() {
    local name=$1
    local path=$2
    local command=$3
    
    osascript <<EOF
tell application "Terminal"
    do script "cd '$path' && $command"
    set title of front window to "$name"
end tell
EOF
    sleep 2
}

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "[1/4] Starting Support Agent on port 8000..."
    start_service_mac "Support Agent (8000)" \
        "$PROJECT_DIR/Customer_support_agent" \
        "source .venv/bin/activate 2>/dev/null; python main.py"
    
    echo "[2/4] Starting Document Agent on port 8001..."
    start_service_mac "Document Agent (8001)" \
        "$PROJECT_DIR/Document_Review_agent/document_review_agent" \
        "source .venv/bin/activate 2>/dev/null; python -m uvicorn app.main:app --reload --port 8001"
    
    echo "[3/4] Starting Meeting Agent on port 8002..."
    start_service_mac "Meeting Agent (8002)" \
        "$PROJECT_DIR/meeting-calendar-agent" \
        "source .venv/bin/activate 2>/dev/null; python -m uvicorn app.main:app --reload --port 8002"
    
    echo "[4/4] Starting Streamlit Dashboard on port 8501..."
    start_service_mac "Streamlit Dashboard (8501)" \
        "$PROJECT_DIR" \
        "source ~/.zshrc 2>/dev/null; streamlit run app.py"
    
    echo ""
    echo "=========================================="
    echo "✅ All agents started in separate terminals!"
    echo "=========================================="
    echo ""
    echo "📊 Dashboard: http://localhost:8501"
    echo "🔧 Support Agent API: http://localhost:8000"
    echo "📄 Document Agent API: http://localhost:8001"
    echo "📅 Meeting Agent API: http://localhost:8002"
    echo ""
    echo "Test with:"
    echo "  curl http://localhost:8002/health"
    echo ""

elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux (GNOME Terminal or similar)
    echo "[1/4] Starting Support Agent on port 8000..."
    gnome-terminal --tab --title="Support Agent (8000)" -- bash -c "cd '$PROJECT_DIR/Customer_support_agent' && source .venv/bin/activate && python main.py"
    
    echo "[2/4] Starting Document Agent on port 8001..."
    gnome-terminal --tab --title="Document Agent (8001)" -- bash -c "cd '$PROJECT_DIR/Document_Review_agent/document_review_agent' && source .venv/bin/activate && python -m uvicorn app.main:app --reload --port 8001"
    
    echo "[3/4] Starting Meeting Agent on port 8002..."
    gnome-terminal --tab --title="Meeting Agent (8002)" -- bash -c "cd '$PROJECT_DIR/meeting-calendar-agent' && source .venv/bin/activate && python -m uvicorn app.main:app --reload --port 8002"
    
    echo "[4/4] Starting Streamlit Dashboard on port 8501..."
    gnome-terminal --tab --title="Streamlit Dashboard (8501)" -- bash -c "cd '$PROJECT_DIR' && streamlit run app.py"
    
    echo "✅ All agents started in separate terminals!"
    
else
    echo "❌ Unsupported OS: $OSTYPE"
    exit 1
fi

sleep 3

# Verify all services are running
echo ""
echo "=========================================="
echo "Checking service health..."
echo "=========================================="
echo ""

check_service() {
    local name=$1
    local port=$2
    sleep 1
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "✅ $name (port $port) - RUNNING"
    else
        echo "⏳ $name (port $port) - Starting... (may take a moment)"
    fi
}

check_service "Support Agent" 8000
check_service "Document Agent" 8001
check_service "Meeting Agent" 8002

echo ""
echo "=========================================="
echo "🎉 System startup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Wait 10-15 seconds for services to fully initialize"
echo "2. Open: http://localhost:8501"
echo "3. Try a meeting query: 'Schedule a meeting with the team next Monday at 2 PM'"
echo ""
