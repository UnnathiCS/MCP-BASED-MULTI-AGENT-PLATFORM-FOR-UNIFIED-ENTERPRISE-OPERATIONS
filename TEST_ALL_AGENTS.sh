#!/bin/bash
# Quick test script for all 7 agents

echo "🔍 Testing all agents..."
echo ""

agents=(
    "Support:http://localhost:8000/health"
    "Documents:http://localhost:8001/health"
    "Meetings:http://localhost:8002/health"
    "HR:http://localhost:8003/health"
    "Email:http://localhost:8004/health"
    "Projects:http://localhost:8005/health"
    "Analytics:http://localhost:8007/health"
)

for agent in "${agents[@]}"; do
    IFS=':' read -r name url <<< "$agent"
    if curl -s "$url" > /dev/null 2>&1; then
        echo "✅ $name is running"
    else
        echo "❌ $name is NOT running"
    fi
done

echo ""
echo "📊 Sample API calls (copy-paste to test):"
echo ""
echo "# Email Agent - Process emails"
echo 'curl -X POST http://localhost:8004/process-emails -H "Content-Type: application/json" -d "{\"user_input\": \"Process customer emails\", \"request_id\": \"test-001\"}"'
echo ""
echo "# Email Agent - Fetch emails"
echo 'curl -X POST http://localhost:8004/emails/fetch -H "Content-Type: application/json" -d "{}"'
echo ""
echo "# Email Agent - Get tickets"
echo 'curl -X GET http://localhost:8004/tickets?limit=10'
echo ""
echo "# HR Agent - Get pending employees"
echo 'curl -X POST http://localhost:8003/agent/orchestrate -H "Content-Type: application/json" -d "{\"user_request\": \"Show pending employees\", \"intent\": \"onboarding\"}"'
echo ""
echo "# Projects Agent - Get project status"
echo 'curl -X POST http://localhost:8005/agent/orchestrate -H "Content-Type: application/json" -d "{\"user_request\": \"Show status of PROJ-001\", \"intent\": \"project_management\"}"'
echo ""
echo "# Analytics Agent - Get dashboard"
echo 'curl -X POST http://localhost:8007/agent/orchestrate -H "Content-Type: application/json" -d "{\"user_request\": \"Show system dashboard\", \"intent\": \"analytics\"}"'
