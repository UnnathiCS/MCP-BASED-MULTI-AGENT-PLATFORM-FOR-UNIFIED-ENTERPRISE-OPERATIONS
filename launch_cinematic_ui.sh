#!/bin/bash

# 🌌 MCP ENTERPRISE AI OPERATING SYSTEM - CINEMATIC UI LAUNCHER
# Starts the futuristic holographic dashboard

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║   🌌 MCP ENTERPRISE AI OPERATING SYSTEM - CINEMATIC UI 🌌     ║"
echo "║                                                                ║"
echo "║    ✨ Holographic Autonomous Enterprise Intelligence ✨       ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if all agents are running
echo "📊 Checking Agent Services..."
echo ""

# Define ports
SUPPORT_AGENT_PORT=8000
DOC_AGENT_PORT=8001
MEETING_AGENT_PORT=8002
HR_AGENT_PORT=8003
EMAIL_AGENT_PORT=8004
PROJECT_AGENT_PORT=8005
ANALYTICS_AGENT_PORT=8007

# Function to check if service is running
check_service() {
    local port=$1
    local name=$2
    if nc -z localhost $port 2>/dev/null; then
        echo "✅ $name (Port $port): RUNNING"
        return 0
    else
        echo "❌ $name (Port $port): NOT RUNNING"
        return 1
    fi
}

# Check all services
check_service $SUPPORT_AGENT_PORT "Support Agent (LangGraph)"
check_service $DOC_AGENT_PORT "Document Review Agent"
check_service $MEETING_AGENT_PORT "Meeting Calendar Agent"
check_service $HR_AGENT_PORT "HR Onboarding Agent"
check_service $EMAIL_AGENT_PORT "Email Agent"
check_service $PROJECT_AGENT_PORT "Project Management Agent"
check_service $ANALYTICS_AGENT_PORT "Analytics Agent"

echo ""
echo "🚀 Launching Cinematic Dashboard..."
echo ""
echo "📝 UI Features:"
echo "   • Glassmorphic holographic cards"
echo "   • Neon gradient animations"
echo "   • Real-time agent orchestration"
echo "   • Multi-layer glow effects"
echo "   • Cinematic color palette"
echo ""
echo "🎨 Theme Colors:"
echo "   • Primary Accent: #00d9ff (Holographic Cyan)"
echo "   • Secondary Accent: #ff006e (Neon Magenta)"
echo "   • Tertiary Accent: #00ff88 (Neon Green)"
echo "   • Background: #0a0e27 (Deep Space Navy)"
echo ""

# Get project directory
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Launch Streamlit with cinematic UI
cd "$PROJECT_DIR"

echo "Opening browser at http://localhost:8501"
echo ""
echo "💡 Press Ctrl+C to stop the dashboard"
echo ""

streamlit run app.py \
    --server.port=8501 \
    --server.headless=true \
    --client.toolbarMode=minimal \
    --theme.primaryColor="#00d9ff" \
    --theme.backgroundColor="#0a0e27" \
    --theme.secondaryBackgroundColor="#1a1f3a"

echo ""
echo "🛑 Dashboard stopped"
echo ""
