#!/bin/bash

# Stop all MCP agents and Streamlit dashboard

echo "🛑 Stopping MCP Multi-Agent Platform..."
echo "=================================="

# Kill processes on all agent ports (including Email Agent on 8004)
for port in 8000 8001 8002 8003 8004 8005 8007 8501; do
  lsof -ti :$port 2>/dev/null | xargs kill -9 2>/dev/null
  echo "  ✅ Stopped port $port"
done

echo ""
echo "=================================="
echo "✅ All agents stopped!"
echo "=================================="
echo ""
