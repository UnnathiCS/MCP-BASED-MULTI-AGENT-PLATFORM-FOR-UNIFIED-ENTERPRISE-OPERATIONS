#!/bin/bash

# Comprehensive Test Suite for All 6 MCP Agents
# Tests all agents with realistic scenarios and validates responses

set -e

echo ""
echo "🧪 MCP Multi-Agent Platform - Comprehensive Test Suite"
echo "======================================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to run a test
run_test() {
    local test_name=$1
    local port=$2
    local endpoint=$3
    local data=$4
    
    echo -n "🔍 Testing: $test_name... "
    
    response=$(curl -s -X POST "http://localhost:$port$endpoint" \
        -H "Content-Type: application/json" \
        -d "$data" 2>/dev/null || echo "{\"error\": \"Connection failed\"}")
    
    # Check if response contains "status" or "decision" (valid response)
    if echo "$response" | grep -q '"status"'; then
        echo -e "${GREEN}✅ PASS${NC}"
        echo "   Response: $(echo "$response" | python3 -c 'import sys, json; print(json.load(sys.stdin).get("status", "unknown"))' 2>/dev/null || echo 'Valid JSON')"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        echo "   Response: $response"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Health Check
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  HEALTH CHECKS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

for port in 8000 8001 8002 8003 8005 8007; do
    if curl -s http://localhost:$port/health | grep -q "ok"; then
        echo -e "  ✅ Port $port: ${GREEN}OK${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "  ❌ Port $port: ${RED}DOWN${NC}"
        ((TESTS_FAILED++))
    fi
done
echo ""

# Test Support Agent
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  SUPPORT AGENT (Port 8000) - IT Ticket Resolution"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

run_test "Create IT Support Ticket" 8000 "/agent/orchestrate" \
    '{"user_request": "My laptop wont connect to WiFi, I need help immediately", "intent": "support"}'

run_test "Resolve Password Reset" 8000 "/agent/orchestrate" \
    '{"user_request": "I forgot my password and need to reset it", "intent": "support"}'

echo ""

# Test Document Review Agent
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  DOCUMENT AGENT (Port 8001) - Contract Analysis"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

run_test "Analyze Contract Risks" 8001 "/agent/orchestrate" \
    '{"user_request": "Analyze this contract for liability risks", "intent": "document"}'

run_test "Extract Contract Terms" 8001 "/agent/orchestrate" \
    '{"user_request": "What are the payment terms in the document?", "intent": "document"}'

echo ""

# Test Meeting Calendar Agent
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  MEETING AGENT (Port 8002) - Calendar Management"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

run_test "Schedule Team Meeting" 8002 "/agent/orchestrate" \
    '{"user_request": "Schedule a meeting with the team next Monday at 2 PM", "intent": "meeting"}'

run_test "Book 1-on-1 with Manager" 8002 "/agent/orchestrate" \
    '{"user_request": "Set up a 30-minute sync with my manager this Friday", "intent": "meeting"}'

echo ""

# Test HR Onboarding Agent
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  HR ONBOARDING AGENT (Port 8003) - Employee Onboarding"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

run_test "Create Onboarding Checklist" 8003 "/agent/orchestrate" \
    '{"user_request": "Onboard Alice Johnson as Senior Software Engineer in Engineering", "intent": "onboarding"}'

run_test "Get Employee Status" 8003 "/agent/orchestrate" \
    '{"user_request": "Show me the onboarding status for EMP-001", "intent": "onboarding"}'

run_test "List Pending Employees" 8003 "/agent/orchestrate" \
    '{"user_request": "Show me all pending employees", "intent": "onboarding"}'

run_test "Get Mentorship Assignments" 8003 "/agent/orchestrate" \
    '{"user_request": "Who is assigned as mentor for the new employee?", "intent": "onboarding"}'

echo ""

# Test Project Management Agent
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6️⃣  PROJECT AGENT (Port 8005) - Project Management"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

run_test "Get Project Status" 8005 "/agent/orchestrate" \
    '{"user_request": "What is the status of PROJ-001?", "intent": "project"}'

run_test "List All Projects" 8005 "/agent/orchestrate" \
    '{"user_request": "Show me all projects", "intent": "project"}'

run_test "Identify At-Risk Projects" 8005 "/agent/orchestrate" \
    '{"user_request": "Which projects are at risk?", "intent": "project"}'

run_test "Get Upcoming Milestones" 8005 "/agent/orchestrate" \
    '{"user_request": "What are the upcoming milestones?", "intent": "project"}'

run_test "Resource Utilization" 8005 "/agent/orchestrate" \
    '{"user_request": "Show me resource utilization across projects", "intent": "project"}'

echo ""

# Test Analytics Agent
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7️⃣  ANALYTICS AGENT (Port 8007) - System Metrics"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

run_test "Dashboard Generation" 8007 "/agent/orchestrate" \
    '{"user_request": "Show me the system dashboard", "intent": "analytics"}'

run_test "Performance Trends" 8007 "/agent/orchestrate" \
    '{"user_request": "What are the performance trends?", "intent": "analytics"}'

run_test "System Health Check" 8007 "/agent/orchestrate" \
    '{"user_request": "Check system health and all agent metrics", "intent": "analytics"}'

run_test "Multi-Agent Workflow" 8007 "/agent/orchestrate" \
    '{"user_request": "Show multi-agent workflow metrics", "intent": "analytics"}'

echo ""

# Multi-Agent Workflow Tests
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "8️⃣  MULTI-AGENT WORKFLOWS (End-to-End)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📋 Workflow 1: Complete Onboarding Journey"
echo "   HR Agent → Support Agent (IT tickets) → Meeting Agent (training)"
echo ""
run_test "  Step 1: HR Onboarding" 8003 "/agent/orchestrate" \
    '{"user_request": "Hire Sarah for Mobile App project", "intent": "onboarding"}'

echo "   [In production, this would trigger Support & Meeting agents]"
echo ""

echo "📋 Workflow 2: Project Health Check"
echo "   Project Agent → Analytics Agent (aggregation)"
echo ""
run_test "  Step 1: Get Project Status" 8005 "/agent/orchestrate" \
    '{"user_request": "Complete status report for Q2 Mobile App Launch", "intent": "project"}'

echo "   [Then Analytics aggregates all project metrics]"
echo ""

echo "📋 Workflow 3: System Monitoring"
echo "   Analytics Agent → All Agents (health check)"
echo ""
run_test "  Step 1: System Dashboard" 8007 "/agent/orchestrate" \
    '{"user_request": "Show complete system health", "intent": "analytics"}'

echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 TEST SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "  ${GREEN}✅ Tests Passed: $TESTS_PASSED${NC}"
echo -e "  ${RED}❌ Tests Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All Tests Passed! System is operational.${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed. Check agent logs:${NC}"
    echo "   tail -f /tmp/mcp_logs/agent_800*.log"
    echo ""
    exit 1
fi
