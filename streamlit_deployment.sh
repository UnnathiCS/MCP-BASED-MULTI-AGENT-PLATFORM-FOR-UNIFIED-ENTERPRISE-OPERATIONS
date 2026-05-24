#!/bin/bash

# MCP UNIFIED AGENT SYSTEM - Deployment Script
# For Streamlit Cloud, Railway, Render, Heroku, or local deployment

echo "🚀 MCP Enterprise Platform - Deployment Initialization"
echo "======================================================"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

# Install agent-specific dependencies
echo "🔧 Installing agent dependencies..."
pip install -q -r Customer_support_agent/requirements.txt 2>/dev/null || true
pip install -q -r Document_Review_agent/document_review_agent/requirements.txt 2>/dev/null || true
pip install -q -r meeting-calendar-agent/requirements.txt 2>/dev/null || true
pip install -q -r HR_Onboarding_agent/requirements.txt 2>/dev/null || true
pip install -q -r Email_agent/requirements.txt 2>/dev/null || true
pip install -q -r Project_Management_agent/requirements.txt 2>/dev/null || true
pip install -q -r Analytics_agent/app/requirements.txt 2>/dev/null || true

# Run Streamlit app
echo "🎬 Starting MCP Platform..."
streamlit run app.py --logger.level=info
