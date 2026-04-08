#!/usr/bin/env python3
"""
Test Cases for Meeting Calendar Agent Integration with MCP System
Tests the natural language interface for meeting scheduling through the unified dashboard
"""

import requests
import json
from datetime import datetime, timedelta

# API Endpoints
DASHBOARD_API = "http://localhost:8501"  # Streamlit (frontend)
MEETING_API = "http://localhost:8002"    # Meeting Agent backend
REQUEST_TIMEOUT = 30

print("=" * 80)
print("MEETING CALENDAR AGENT - MCP INTEGRATION TEST CASES")
print("=" * 80)

# Test Case 1: Simple Meeting Detection
print("\n" + "=" * 80)
print("TEST 1: Intent Detection - Meeting Keywords")
print("=" * 80)

test_queries_meeting = [
    {
        "query": "Schedule a meeting with the team next Monday at 2 PM",
        "expected": "meetings",
        "description": "Simple meeting scheduling request"
    },
    {
        "query": "Find a time slot for all attendees",
        "expected": "meetings",
        "description": "Availability checking request"
    },
    {
        "query": "Check my calendar for conflicts on Wednesday",
        "expected": "meetings",
        "description": "Conflict resolution request"
    },
    {
        "query": "Book a conference room for the product review",
        "expected": "meetings",
        "description": "Meeting booking request"
    },
]

for i, test in enumerate(test_queries_meeting, 1):
    print(f"\n  Test {i}: {test['description']}")
    print(f"  Query: '{test['query']}'")
    print(f"  Expected Agent: {test['expected']}")
    print(f"  ✓ Should detect as MEETING agent (score > 0.7)")

# Test Case 2: Agent Routing
print("\n\n" + "=" * 80)
print("TEST 2: MCP Agent Routing")
print("=" * 80)

routing_tests = [
    {
        "query": "Schedule a meeting at 3 PM with John and Sarah",
        "expected_agent": "meetings",
        "expected_port": 8002
    },
    {
        "query": "My VPN is not working",
        "expected_agent": "support",
        "expected_port": 8000
    },
    {
        "query": "Review this contract for risks",
        "expected_agent": "documents",
        "expected_port": 8001
    },
]

for i, test in enumerate(routing_tests, 1):
    print(f"\n  Test {i}:")
    print(f"  Query: '{test['query']}'")
    print(f"  Expected Routing: {test['expected_agent']} (port {test['expected_port']})")
    print(f"  ✓ MCP should route to correct agent")

# Test Case 3: Meeting Agent Capabilities
print("\n\n" + "=" * 80)
print("TEST 3: Meeting Agent Capabilities")
print("=" * 80)

capability_tests = [
    {
        "task": "Meeting Creation",
        "query": "Create a meeting titled 'Q1 Planning' on April 15 from 2-3 PM with alice@company.com and bob@company.com",
        "expected_response": ["meeting created", "title", "attendees", "time"],
    },
    {
        "task": "Availability Check",
        "query": "Check availability for team members next week",
        "expected_response": ["available", "slots", "time", "attendees"],
    },
    {
        "task": "Conflict Detection",
        "query": "Schedule meeting with everyone on Thursday at 2 PM - check for conflicts",
        "expected_response": ["conflict", "busy", "suggest", "available time"],
    },
    {
        "task": "Meeting Suggestions",
        "query": "Suggest the best time for a 1-hour meeting with 5 people",
        "expected_response": ["suggest", "time", "availability", "slot"],
    },
    {
        "task": "Calendar Integration",
        "query": "Show my calendar for next week and find free slots",
        "expected_response": ["calendar", "free", "busy", "slot"],
    },
]

for i, test in enumerate(capability_tests, 1):
    print(f"\n  Test {i}: {test['task']}")
    print(f"  Query: '{test['query']}'")
    print(f"  Expected Response Contains: {', '.join(test['expected_response'])}")
    print(f"  ✓ Should handle and return appropriate meeting data")

# Test Case 4: Complex Scenarios
print("\n\n" + "=" * 80)
print("TEST 4: Complex Meeting Scenarios")
print("=" * 80)

complex_tests = [
    {
        "scenario": "Multi-attendee scheduling with conflict resolution",
        "query": "Schedule a 1-hour sync with John, Sarah, and Mike. I'm busy Tuesday afternoon, John is busy Wednesday morning, and Sarah is unavailable Thursday. Find a time that works for everyone.",
        "expected_outputs": ["suggested time", "attendees confirmed", "no conflicts"],
    },
    {
        "scenario": "Recurring meeting creation",
        "query": "Create a weekly standup every Monday at 10 AM with the team",
        "expected_outputs": ["recurring", "weekly", "time", "attendees"],
    },
    {
        "scenario": "Meeting rescheduling",
        "query": "Move my 2 PM meeting on Wednesday to Thursday at 3 PM and notify attendees",
        "expected_outputs": ["rescheduled", "new time", "attendees notified"],
    },
    {
        "scenario": "Multi-location meeting",
        "query": "Schedule a meeting in New York timezone with participants in London and Tokyo",
        "expected_outputs": ["timezone", "location", "time conversion", "attendees"],
    },
]

for i, test in enumerate(complex_tests, 1):
    print(f"\n  Test {i}: {test['scenario']}")
    print(f"  Query: '{test['query']}'")
    print(f"  Expected Outputs: {', '.join(test['expected_outputs'])}")
    print(f"  ✓ Should handle complex logic and return comprehensive result")

# Test Case 5: Error Handling
print("\n\n" + "=" * 80)
print("TEST 5: Error Handling & Edge Cases")
print("=" * 80)

error_tests = [
    {
        "case": "Ambiguous query",
        "query": "Meet tomorrow",
        "expected": "Should ask for clarification or suggest possible times",
    },
    {
        "case": "Missing required info",
        "query": "Schedule a meeting with John",
        "expected": "Should ask for time/date/duration",
    },
    {
        "case": "No availability",
        "query": "Find a time when everyone is available",
        "expected": "Should report no common slots or suggest alternatives",
    },
    {
        "case": "Invalid time",
        "query": "Schedule meeting at 25:00 PM",
        "expected": "Should reject invalid time and ask for valid time",
    },
]

for i, test in enumerate(error_tests, 1):
    print(f"\n  Test {i}: {test['case']}")
    print(f"  Query: '{test['query']}'")
    print(f"  Expected Behavior: {test['expected']}")

# Test Case 6: Integration with Other Agents
print("\n\n" + "=" * 80)
print("TEST 6: Multi-Agent Integration")
print("=" * 80)

integration_tests = [
    {
        "sequence": "IT Support → Meeting",
        "queries": [
            "My VPN is not working",  # Goes to Support Agent
            "Schedule a meeting to discuss the VPN issue",  # Should go to Meeting Agent
        ],
        "expected": "System maintains context across agents",
    },
    {
        "sequence": "Document Review → Meeting",
        "queries": [
            "Review this NDA for issues",  # Goes to Document Agent
            "Schedule a call with legal to discuss the NDA",  # Goes to Meeting Agent
        ],
        "expected": "Each request routes to correct agent",
    },
]

for i, test in enumerate(integration_tests, 1):
    print(f"\n  Test {i}: {test['sequence']}")
    for query in test['queries']:
        print(f"    • '{query}'")
    print(f"  Expected: {test['expected']}")

# Test Case 7: Performance & Response
print("\n\n" + "=" * 80)
print("TEST 7: Performance Metrics")
print("=" * 80)

print("""
  Response Time:
    ✓ Intent detection: < 100ms
    ✓ Agent routing: < 50ms
    ✓ Meeting processing: < 2000ms
    ✓ Total end-to-end: < 3000ms
  
  Accuracy:
    ✓ Correct agent selection: > 95%
    ✓ Intent detection accuracy: > 90%
    ✓ Meeting data extraction: > 98%
""")

# Test Case 8: API Endpoint Tests
print("\n\n" + "=" * 80)
print("TEST 8: Direct API Testing")
print("=" * 80)

api_tests = [
    {
        "endpoint": "POST /agent/orchestrate",
        "port": 8002,
        "payload": {
            "request": "Schedule a meeting with Alice on Friday at 2 PM",
            "request_id": "test-001"
        },
        "expected_fields": ["status", "decision", "meetings", "suggestions"],
    },
    {
        "endpoint": "GET /health",
        "port": 8002,
        "expected_status": 200,
        "expected_fields": ["status"],
    },
]

for i, test in enumerate(api_tests, 1):
    print(f"\n  Test {i}: {test['endpoint']}")
    print(f"  Port: {test['port']}")
    if "payload" in test:
        print(f"  Payload: {json.dumps(test['payload'], indent=2)}")
    print(f"  Expected Response Fields: {', '.join(test.get('expected_fields', []))}")
    print(f"  ✓ Should return valid JSON with all required fields")

# Test Case 9: UI/Dashboard Integration
print("\n\n" + "=" * 80)
print("TEST 9: Dashboard UI Integration")
print("=" * 80)

ui_tests = [
    {
        "component": "Input Detection",
        "check": "Type meeting query in text area",
        "expected": "Should detect as meeting and highlight it",
    },
    {
        "component": "Response Display",
        "check": "Submit meeting request",
        "expected": "Should show meeting details, attendees, time, calendar link",
    },
    {
        "component": "Timeline",
        "check": "After processing",
        "expected": "Should show MCP routing decision and processing time",
    },
    {
        "component": "Developer View",
        "check": "Expand JSON section",
        "expected": "Should display full response including meeting data",
    },
]

for i, test in enumerate(ui_tests, 1):
    print(f"\n  Test {i}: {test['component']}")
    print(f"  Check: {test['check']}")
    print(f"  Expected: {test['expected']}")

# Test Case 10: Actual Test Prompts to Use
print("\n\n" + "=" * 80)
print("TEST 10: ACTUAL TEST PROMPTS TO USE IN DASHBOARD")
print("=" * 80)

actual_prompts = [
    {
        "priority": "HIGH",
        "prompt": "Schedule a meeting with the marketing team next Tuesday at 10 AM for 1 hour",
        "what_to_check": [
            "✓ MCP detects this as 'meetings' agent",
            "✓ Routing shows port 8002",
            "✓ Response shows meeting details with attendees",
            "✓ Timeline shows meeting-specific processing steps",
        ]
    },
    {
        "priority": "HIGH", 
        "prompt": "Check my availability next week and find a time to meet with Alice, Bob, and Charlie",
        "what_to_check": [
            "✓ Detected as meetings agent",
            "✓ Returns available time slots",
            "✓ Shows attendee availability",
            "✓ Suggests best meeting times",
        ]
    },
    {
        "priority": "HIGH",
        "prompt": "I have a conflict on Thursday afternoon. Can you reschedule my 2 PM meeting to Friday morning?",
        "what_to_check": [
            "✓ Detected as meetings agent",
            "✓ Identifies the meeting that needs rescheduling",
            "✓ Detects conflict and suggests alternatives",
            "✓ Returns new meeting time and confirmation",
        ]
    },
    {
        "priority": "MEDIUM",
        "prompt": "Create a recurring weekly standup at 9:30 AM every Monday with dev team",
        "what_to_check": [
            "✓ Detected as meetings agent",
            "✓ Understands 'recurring' and 'weekly'",
            "✓ Returns recurring meeting details",
            "✓ Shows all instances created",
        ]
    },
    {
        "priority": "MEDIUM",
        "prompt": "Book the conference room for a 2-hour workshop next Wednesday",
        "what_to_check": [
            "✓ Detected as meetings agent",
            "✓ Includes resource/room booking",
            "✓ Returns room availability and booking confirmation",
        ]
    },
]

for i, test in enumerate(actual_prompts, 1):
    print(f"\n  Test {i} [{test['priority']}]:")
    print(f"  📝 Prompt: \"{test['prompt']}\"")
    print(f"  ✅ What to Check:")
    for check in test['what_to_check']:
        print(f"     {check}")

print("\n\n" + "=" * 80)
print("HOW TO RUN THESE TESTS")
print("=" * 80)

print("""
STEP 1: Start all services
  Terminal 1: cd ~/Documents/SEM-6/MINI-PROJECT/Customer_support_agent
             source .venv/bin/activate
             python main.py
  
  Terminal 2: cd ~/Documents/SEM-6/MINI-PROJECT/meeting-calendar-agent
             source .venv/bin/activate
             python -m uvicorn app.main:app --reload --port 8002
  
  Terminal 3: cd ~/Documents/SEM-6/MINI-PROJECT
             streamlit run app.py

STEP 2: Open dashboard
  → http://localhost:8501

STEP 3: Run test prompts from "TEST 10" above
  → Type each prompt in the message box
  → Verify the expected checks pass
  → Check timeline and routing information

STEP 4: Verify API endpoints (optional)
  → curl -X POST http://localhost:8002/agent/orchestrate \\
      -H "Content-Type: application/json" \\
      -d '{"request":"Schedule a meeting with Alice on Friday at 2 PM","request_id":"test-001"}'
  
  → curl http://localhost:8002/health

STEP 5: Check MCP Integration
  → Look at "Timeline" after each request
  → Verify it shows:
    • Category detected: "Meeting Scheduling"
    • Agent selected: "Meeting Calendar Agent"
    • Port: 8002
    • Response time < 3 seconds

SUCCESS CRITERIA:
✅ All 3 agents respond correctly
✅ MCP routes meeting queries to port 8002
✅ Meeting agent returns meeting data (title, time, attendees)
✅ Dashboard displays meeting results properly
✅ Timeline shows correct processing flow
✅ Response times reasonable (< 3 seconds)
""")

print("\n" + "=" * 80)
print("END OF TEST CASES")
print("=" * 80)
