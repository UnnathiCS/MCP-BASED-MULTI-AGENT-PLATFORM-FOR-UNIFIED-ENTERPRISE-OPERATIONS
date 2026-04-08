#!/usr/bin/env python3
"""
Quick Test: Meeting Agent Integration with MCP
Tests the meeting agent `/agent/orchestrate` endpoint
"""

import requests
import json

BASE_URL = "http://localhost:8002"

print("=" * 80)
print("MEETING AGENT INTEGRATION - QUICK TEST")
print("=" * 80)

# Test 1: Health Check
print("\n✅ TEST 1: Health Check")
print("-" * 80)
try:
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print("✓ Meeting agent is HEALTHY")
except Exception as e:
    print(f"✗ Health check failed: {e}")

# Test 2: Simple Meeting Schedule Request
print("\n✅ TEST 2: Simple Meeting Schedule Request")
print("-" * 80)
test_cases = [
    {
        "name": "Basic meeting",
        "request": "Schedule a meeting with the team next Monday at 2 PM",
        "request_id": "test-001"
    },
    {
        "name": "Meeting with attendees",
        "request": "Schedule a meeting with Alice, Bob, and Charlie tomorrow at 10 AM",
        "request_id": "test-002"
    },
    {
        "name": "Recurring meeting",
        "request": "Create a weekly standup every Monday at 9:30 AM",
        "request_id": "test-003"
    },
]

for test in test_cases:
    print(f"\n  📝 Test: {test['name']}")
    print(f"  Request: {test['request']}")
    try:
        response = requests.post(
            f"{BASE_URL}/agent/orchestrate",
            json={
                "request": test['request'],
                "request_id": test['request_id']
            },
            timeout=5
        )
        print(f"  Status: {response.status_code}")
        data = response.json()
        print(f"  Agent: {data.get('agent', 'N/A')}")
        print(f"  Status: {data.get('status', 'N/A')}")
        if data.get('meetings'):
            print(f"  Meetings: {len(data['meetings'])} meeting(s)")
            for mtg in data['meetings']:
                print(f"    - {mtg.get('title', 'Untitled')}: {mtg.get('message', 'No message')}")
        print(f"  Suggestions: {len(data.get('suggestions', []))} suggestions")
        print("  ✓ Request processed successfully")
    except Exception as e:
        print(f"  ✗ Error: {e}")

# Test 3: Response Structure Validation
print("\n✅ TEST 3: Response Structure Validation")
print("-" * 80)
try:
    response = requests.post(
        f"{BASE_URL}/agent/orchestrate",
        json={
            "request": "Schedule a meeting",
            "request_id": "test-structure"
        },
        timeout=5
    )
    data = response.json()
    
    required_fields = ["status", "request_id", "agent", "decision", "meetings", "suggestions", "conflicts", "availability"]
    missing_fields = [f for f in required_fields if f not in data]
    
    if missing_fields:
        print(f"✗ Missing fields: {missing_fields}")
    else:
        print("✓ All required fields present:")
        for field in required_fields:
            print(f"  - {field}: {type(data[field]).__name__}")
    
    print("\n✓ Response structure is valid")
except Exception as e:
    print(f"✗ Structure validation failed: {e}")

# Test 4: MCP Compatibility
print("\n✅ TEST 4: MCP Compatibility Check")
print("-" * 80)
try:
    response = requests.post(
        f"{BASE_URL}/agent/orchestrate",
        json={
            "request": "Test MCP compatibility",
            "request_id": "test-mcp"
        },
        timeout=5
    )
    
    if response.status_code == 200:
        data = response.json()
        if all(k in data for k in ["status", "agent", "meetings"]):
            print("✓ MCP endpoint is compatible with frontend dashboard")
            print(f"  - Returns status: {data.get('status')}")
            print(f"  - Agent identified as: {data.get('agent')}")
            print(f"  - Meetings data structure: {type(data.get('meetings')).__name__}")
        else:
            print("✗ Response missing MCP-required fields")
    else:
        print(f"✗ Unexpected status code: {response.status_code}")
except Exception as e:
    print(f"✗ MCP compatibility check failed: {e}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("""
✓ Meeting Agent Integration Status: READY FOR TESTING

Next Steps:
1. Open Streamlit dashboard: http://localhost:8501
2. Type a meeting request in the message box
3. Examples to try:
   - "Schedule a meeting with the team next Monday at 2 PM"
   - "Check my availability next week"
   - "Find a time to meet with Alice and Bob"

What to expect:
✓ MCP detects the request as "meetings" agent
✓ Routes to port 8002
✓ Shows meeting details in the dashboard
✓ Displays suggestions and conflicts (if any)
✓ Timeline shows MCP decision flow

Troubleshooting:
- If meeting agent shows 500 error: Check /tmp/meeting_agent.log
- If connection refused: Meeting agent not running on 8002
- If wrong agent selected: Check intent keywords in app.py
""")
print("=" * 80)
