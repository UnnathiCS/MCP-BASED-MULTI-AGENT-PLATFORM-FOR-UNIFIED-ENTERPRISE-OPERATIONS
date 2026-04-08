# Strict Agent Orchestrator Testing Guide

## Overview

The Phase-2 agent orchestrator now enforces **STRICT safety rules** in deterministic order:

1. **Time Extraction** – Parse start/end time from constraints or intent
2. **Time Validation** – Ensure time range is present; request approval if missing
3. **Working Hours Check** – Enforce 9:00 AM – 6:00 PM UTC; block if violated
4. **Conflict Detection** – Check if required participants are busy; block if HARD conflict found
5. **Auto-Booking** – If all checks pass, create meeting immediately
6. **Alternative Suggestions** – Provide next available slots for all blocking decisions

All responses include:
- `action`: One of `out_of_working_hours`, `conflict_detected`, `create_meeting`, `request_approval`, `execution_failed`
- `explanation`: Human-readable reason for decision
- `data`: Additional context (event_id, conflict details, suggested slots)

---

## API Endpoint: `POST /agent/schedule`

**Request Body (AgentRequest):**
```json
{
  "intent": "string - what user wants to do",
  "participants": ["email@example.com"],
  "constraints": {
    "time_min": "2026-02-08T09:00:00+00:00",
    "time_max": "2026-02-08T10:00:00+00:00"
  },
  "availability": null,
  "conflicts": null,
  "urgency": 0.5
}
```

**Response (AgentDecision):**
```json
{
  "action": "create_meeting|conflict_detected|out_of_working_hours|request_approval|execution_failed",
  "explanation": "Human-readable reason",
  "data": {
    "event_id": "optional event ID if created",
    "conflicts": {"...": "optional conflict details"},
    "suggested_slots": [
      {
        "start": "ISO timestamp",
        "end": "ISO timestamp",
        "explanation": "slot explanation"
      }
    ]
  }
}
```

---

## Test Cases

### Test 1: Normal Meeting Creation (Success Path)

**Scenario:** Schedule meeting with valid time, no conflicts, within working hours

**Request:**
```json
{
  "intent": "Schedule meeting with Alice",
  "participants": ["alice@example.com"],
  "constraints": {
    "time_min": "2026-02-09T09:00:00+00:00",
    "time_max": "2026-02-09T10:00:00+00:00"
  },
  "urgency": 0.5
}
```

**Expected Response:**
```json
{
  "action": "create_meeting",
  "explanation": "Meeting created successfully at 2026-02-09 09:00 UTC",
  "data": {
    "event_id": "abc123def456"
  }
}
```

**Validation:**
- ✅ Action is `create_meeting`
- ✅ Explanation describes the booking
- ✅ `data.event_id` is populated

---

### Test 2: Working Hours Violation (Out of Hours)

**Scenario:** Request meeting outside 9–18 UTC window

**Request (starts at 8:00 AM, before working hours begin):**
```json
{
  "intent": "Schedule meeting with Bob",
  "participants": ["bob@example.com"],
  "constraints": {
    "time_min": "2026-02-09T08:00:00+00:00",
    "time_max": "2026-02-09T09:00:00+00:00"
  },
  "urgency": 0.5
}
```

**Expected Response:**
```json
{
  "action": "out_of_working_hours",
  "explanation": "Meeting at 2026-02-09 08:00 UTC is outside working hours (9-18 UTC)",
  "data": {
    "suggested_slots": [
      {
        "start": "2026-02-09T09:00:00+00:00",
        "end": "2026-02-09T10:00:00+00:00",
        "explanation": "First available slot within working hours"
      },
      {
        "start": "2026-02-10T09:00:00+00:00",
        "end": "2026-02-10T10:00:00+00:00",
        "explanation": "Next day morning slot"
      }
    ]
  }
}
```

**Validation:**
- ✅ Action is `out_of_working_hours`
- ✅ Explanation mentions 9–18 UTC constraint
- ✅ `data.suggested_slots` contains at least one valid alternative
- ✅ Suggested slots are within 9–18 UTC

---

### Test 3: Hard Conflict Detected (Required Participant Busy)

**Scenario:** Required participant is busy during requested time

**Request:**
```json
{
  "intent": "Schedule meeting with alice@example.com",
  "participants": ["alice@example.com"],
  "constraints": {
    "time_min": "2026-02-09T10:00:00+00:00",
    "time_max": "2026-02-09T11:00:00+00:00"
  },
  "urgency": 0.5
}
```

*(Assume alice@example.com is busy 10:00–10:30 UTC that day)*

**Expected Response:**
```json
{
  "action": "conflict_detected",
  "explanation": "alice@example.com is busy during requested time (10:00–11:00 UTC)",
  "data": {
    "conflicts": {
      "type": "hard",
      "participants": ["alice@example.com"],
      "busy_period": "2026-02-09T10:00:00+00:00 to 2026-02-09T10:30:00+00:00"
    },
    "suggested_slots": [
      {
        "start": "2026-02-09T11:00:00+00:00",
        "end": "2026-02-09T12:00:00+00:00",
        "explanation": "Next available slot after alice@example.com's busy time"
      },
      {
        "start": "2026-02-10T09:00:00+00:00",
        "end": "2026-02-10T10:00:00+00:00",
        "explanation": "Next day morning slot"
      }
    ]
  }
}
```

**Validation:**
- ✅ Action is `conflict_detected`
- ✅ `data.conflicts.type` is `hard`
- ✅ `data.conflicts.participants` lists alice@example.com
- ✅ `data.suggested_slots` shows times when alice is free
- ✅ All suggested slots are within working hours

---

### Test 4: Soft Conflict (Optional Participant Busy)

**Scenario:** Optional participant is busy but not a blocker (behavior: STILL auto-books, includes conflict info)

**Request:**
```json
{
  "intent": "Schedule meeting with alice@example.com (required) and bob@example.com (optional)",
  "participants": ["alice@example.com", "bob@example.com"],
  "constraints": {
    "time_min": "2026-02-09T14:00:00+00:00",
    "time_max": "2026-02-09T15:00:00+00:00"
  },
  "urgency": 0.5
}
```

*(Assume alice@example.com is free but bob@example.com is busy 14:00–14:30)*

**Expected Response:**
```json
{
  "action": "create_meeting",
  "explanation": "Meeting created. Note: bob@example.com has a scheduling conflict but is optional.",
  "data": {
    "event_id": "xyz789abc123",
    "soft_conflicts": [
      {
        "participant": "bob@example.com",
        "type": "soft",
        "busy_time": "2026-02-09T14:00:00+00:00 to 2026-02-09T14:30:00+00:00"
      }
    ]
  }
}
```

**Validation:**
- ✅ Action is `create_meeting` (soft conflicts don't block)
- ✅ Explanation mentions soft conflict
- ✅ Meeting still created (event_id populated)
- ✅ `data.soft_conflicts` lists optional attendee issues

---

### Test 5: Missing Time in Constraints

**Scenario:** Request lacks time_min/time_max; should request approval

**Request:**
```json
{
  "intent": "Schedule meeting sometime next week",
  "participants": ["alice@example.com"],
  "constraints": {
    "location": "Conf Room A"
  },
  "urgency": 0.5
}
```

**Expected Response:**
```json
{
  "action": "request_approval",
  "explanation": "Cannot determine meeting time from constraints or intent. Manual approval required.",
  "data": {
    "reason": "time_min and time_max not found in constraints"
  }
}
```

**Validation:**
- ✅ Action is `request_approval`
- ✅ Explanation indicates missing time information

---

### Test 6: Evening Meeting (Outside Hours)

**Scenario:** Request meeting at 7:00 PM UTC (after 6:00 PM cutoff)

**Request:**
```json
{
  "intent": "Schedule end-of-day sync",
  "participants": ["alice@example.com"],
  "constraints": {
    "time_min": "2026-02-09T19:00:00+00:00",
    "time_max": "2026-02-09T20:00:00+00:00"
  },
  "urgency": 0.8
}
```

**Expected Response:**
```json
{
  "action": "out_of_working_hours",
  "explanation": "Meeting at 2026-02-09 19:00 UTC is outside working hours (9-18 UTC)",
  "data": {
    "suggested_slots": [
      {
        "start": "2026-02-10T09:00:00+00:00",
        "end": "2026-02-10T10:00:00+00:00",
        "explanation": "Next available working hours slot"
      }
    ]
  }
}
```

**Validation:**
- ✅ Action is `out_of_working_hours`
- ✅ Suggested slot is next day (system respects working hours even with high urgency)

---

## Running Tests Manually

### Using curl:

```bash
# Test 1: Successful booking
curl -X POST http://localhost:8000/agent/schedule \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "Schedule meeting with alice@example.com",
    "participants": ["alice@example.com"],
    "constraints": {
      "time_min": "2026-02-09T10:00:00+00:00",
      "time_max": "2026-02-09T11:00:00+00:00"
    },
    "urgency": 0.5
  }'

# Test 2: Out of working hours
curl -X POST http://localhost:8000/agent/schedule \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "Schedule meeting",
    "participants": ["alice@example.com"],
    "constraints": {
      "time_min": "2026-02-09T08:00:00+00:00",
      "time_max": "2026-02-09T09:00:00+00:00"
    },
    "urgency": 0.5
  }'
```

### Using Python requests:

```python
import requests
import json

url = "http://localhost:8000/agent/schedule"

# Test: Working hours violation
payload = {
    "intent": "Schedule meeting",
    "participants": ["alice@example.com"],
    "constraints": {
        "time_min": "2026-02-09T08:00:00+00:00",
        "time_max": "2026-02-09T09:00:00+00:00"
    },
    "urgency": 0.5
}

response = requests.post(url, json=payload)
print(json.dumps(response.json(), indent=2))
```

---

## Expected Behavior Summary

| Scenario | Action | Auto-Books? | Alternatives? |
|----------|--------|-------------|---------------|
| Valid time, no conflicts, working hours | `create_meeting` | ✅ Yes | ❌ No |
| Outside 9–18 UTC window | `out_of_working_hours` | ❌ No | ✅ Yes |
| Required participant busy | `conflict_detected` | ❌ No | ✅ Yes |
| Optional participant busy | `create_meeting` | ✅ Yes | ❌ Note conflict |
| Missing time in constraints | `request_approval` | ❌ No | ❌ No |
| Execution fails (e.g., API error) | `execution_failed` | ❌ No | ❌ No |

---

## Key Guarantees

1. **No Out-of-Hours Bookings** – Meetings outside 9–18 UTC are always blocked with alternatives
2. **No Required Participant Conflicts** – Hard conflicts are always detected and block auto-booking
3. **All Blocks Include Alternatives** – Every rejection includes suggested slots
4. **Clear Explanations** – Every decision includes human-readable explanation
5. **Soft Conflicts Noted** – Optional attendee conflicts don't block but are reported
6. **Deterministic Behavior** – Same input always produces same action (no randomness from planner in critical path)

---

## Debugging

If response doesn't match expectations:

1. **Check time_min/time_max format** – Must be ISO 8601 with timezone (e.g., `2026-02-09T09:00:00+00:00`)
2. **Verify UTC times** – System works in UTC; convert local times if needed
3. **Check Google Calendar availability** – Conflicts only detected if participant shows busy on their calendar
4. **Review logs** – Check server logs for `_extract_time_from_intent` and `_get_working_hours_violation` calls
5. **Test with fixed time** – Use explicit constraints with time_min/time_max to eliminate time-parsing ambiguity

---

## Integration Notes

The orchestrator follows zero-trust principle:
- **Safety first** – All blocking checks run before any API calls
- **Explainability** – Every decision includes reasoning
- **Auditability** – All actions logged with participant/time/reason

For MCP integration, wrap the orchestrator's `orchestrate(request)` function to expose as MCP tool.
