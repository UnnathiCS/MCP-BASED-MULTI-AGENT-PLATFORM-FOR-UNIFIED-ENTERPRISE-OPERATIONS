#!/usr/bin/env bash

# 🌌 CINEMATIC UI - QUICK START GUIDE
# Launch the futuristic holographic dashboard

set -e

PROJECT_DIR="/Users/unnathics/Documents/SEM-6/MINI-PROJECT copy"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║   🌌 MCP ENTERPRISE AI OPERATING SYSTEM - CINEMATIC UI 🌌     ║"
echo "║                                                                ║"
echo "║      ✨ Holographic Autonomous Enterprise Intelligence ✨     ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Verify files
echo "📋 Verifying files..."
if [ -f "$PROJECT_DIR/app.py" ]; then
    echo "✅ app.py found"
else
    echo "❌ app.py not found"
    exit 1
fi

if [ -f "$PROJECT_DIR/cinematic_ui.py" ]; then
    echo "✅ cinematic_ui.py found"
else
    echo "❌ cinematic_ui.py not found"
    exit 1
fi

echo ""

# Step 2: Check Python environment
echo "🐍 Checking Python environment..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    echo "✅ Python $PYTHON_VERSION found"
else
    echo "❌ Python3 not found"
    exit 1
fi

echo ""

# Step 3: Check dependencies
echo "📦 Checking dependencies..."
REQUIRED_PACKAGES=("streamlit" "plotly" "pandas" "requests")

for package in "${REQUIRED_PACKAGES[@]}"; do
    if python3 -c "import $package" 2>/dev/null; then
        echo "✅ $package installed"
    else
        echo "⚠️  $package not installed - installing..."
        pip3 install $package --quiet
        echo "✅ $package installed"
    fi
done

echo ""

# Step 4: Display features
echo "🎨 CINEMATIC UI FEATURES:"
echo "   ✨ Glassmorphic holographic cards"
echo "   ✨ Neon gradient animations (cyan/magenta/green)"
echo "   ✨ Real-time agent orchestration visualization"
echo "   ✨ Multi-layer glow effects"
echo "   ✨ Smooth cinematic transitions"
echo "   ✨ Professional dark theme"
echo "   ✨ Enterprise-grade aesthetic"
echo ""

# Step 5: Agent status
echo "📊 Agent Services Status:"
echo "   • Support Agent (8000):          Check via http://127.0.0.1:8000/health"
echo "   • Document Agent (8001):         Check via http://127.0.0.1:8001/health"
echo "   • Meeting Agent (8002):          Check via http://127.0.0.1:8002/health"
echo "   • HR Agent (8003):               Check via http://127.0.0.1:8003/health"
echo "   • Email Agent (8004):            Check via http://127.0.0.1:8004/health"
echo "   • Project Agent (8005):          Check via http://127.0.0.1:8005/health"
echo "   • Analytics Agent (8007):        Check via http://127.0.0.1:8007/health"
echo ""

echo "⏳ Starting Streamlit dashboard..."
echo "🌐 Dashboard will open at: http://localhost:8501"
echo ""
echo "📝 Tips:"
echo "   • The interface has a dark holographic theme"
echo "   • Hover over cards to see glow effects"
echo "   • Click workflow buttons to test agents"
echo "   • Watch for smooth animations and transitions"
echo ""
echo "💡 To stop: Press Ctrl+C"
echo ""

# Step 6: Launch Streamlit
cd "$PROJECT_DIR"
streamlit run app.py \
    --client.toolbarMode="minimal" \
    --client.showErrorDetails=false \
    --logger.level=error

echo ""
echo "🛑 Dashboard closed"
echo ""
