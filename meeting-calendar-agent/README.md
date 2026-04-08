(Meeting Calendar Agent)

Local testing

- Ensure Python 3.10+
- Install dependencies:

```bash
pip install fastapi uvicorn google-api-python-client google-auth google-auth-oauthlib pydantic
```

- Place OAuth credentials at `config/credentials.json` (already present).
- On first run, the app will open a browser to complete OAuth and will save token to `config/token.json`.

Run locally:

```bash
uvicorn app.main:app --reload --port 8000
```

Open Swagger UI: http://localhost:8000/docs

Example POST /meetings payload (JSON):

> **Note:** `start_time` and `end_time` must be valid ISO‑8601 datetimes
> (e.g. `2026-02-08T14:00:00+00:00`).  Invalid strings result in a
> 422 validation error.

```json
{
	"title": "Team Sync",
	"description": "Weekly sync",
	"start_time": "2026-02-08T14:00:00+00:00",
	"end_time": "2026-02-08T15:00:00+00:00",
	"timezone": "UTC",
	"attendees": ["alice@example.com"],
	"location": "Conference Room A"
}
```

Health check: `GET /health` returns `{"status": "ok"}`

## Phase 2: Availability & Conflict-Aware Features

Additional endpoints have been added to support availability queries and
conflict‑aware scheduling:

* `POST /meetings/availability` – send a JSON body with `time_min`,
  `time_max` and optional `attendees` to retrieve busy intervals for the
  primary calendar and any specified attendees.
* `POST /meetings/suggest` – submit the same payload as `/meetings/` to
  receive a recommended start/end time if the requested slot is busy.

The standard `/meetings/` create endpoint now returns a `conflicts` field
when it detects overlapping events; existing clients will continue to
receive the created event as before.

These features are designed to be backward compatible and serve as a
foundation for future AI‑driven availability intelligence and MCP
integration.

### Agent Planner

A simple local AI planner endpoint has been added for Phase‑2.  Under the
hood it uses the open‑source Mistral model `mistralai/mistral-small`
via `transformers` and `torch`.  The model is loaded once (singleton) and
invoked with temperature=0 to guarantee deterministic behavior.

The planner expects the request body to include structured information
rather than free text.  Example body:

```json
{
  "intent": "schedule_meeting",
  "availability": {"primary": {"busy": []}},
  "conflicts": [{"type": "POLICY", "severity": "low", "explanation": "outside hours"}],
  "urgency": 1.0
}
```

The LLM is prompted to **return strict JSON only** with this format:

```json
{
  "action": "suggest_slots" | "create_meeting" | "request_approval",
  "reason": "...",
  "data": { ... }
}
```

No freeform text is allowed outside the JSON.  If the model is unavailable
or returns invalid output, a deterministic fallback decision is used
(request approval).

Call `POST /agent/plan` to use the planner endpoint.

### Agent Orchestrator (STRICT Safety Mode)

The orchestrator (`POST /agent/schedule`) implements a **STRICT, deterministic** meeting scheduling workflow that
prioritizes safety and explainability:

#### Execution Order (Guaranteed):

1. **Time Extraction** – Parse start/end time from constraints
2. **Time Validation** – Demand that time_min/time_max are provided
3. **Working Hours Check** – Enforce 9:00 AM – 6:00 PM UTC; block if violated
4. **Conflict Detection** – Check required participants' calendars; block if busy
5. **Auto-Booking** – Create meeting if all checks pass
6. **Alternative Suggestions** – Provide next available slots for any block

#### Responses Always Include:

- **action** – One of: `create_meeting`, `out_of_working_hours`, `conflict_detected`, `request_approval`, `execution_failed`
- **explanation** – Human-readable reasoning for every decision
- **data** – Event ID (on success), conflict details, or suggested alternative time slots

#### Key Guarantees:

- ✅ **No out-of-hours bookings** – All requests outside 9–18 UTC are blocked with working-hours alternatives
- ✅ **No required-participant conflicts** – Hard conflicts detected and block auto-booking
- ✅ **All blocks include alternatives** – Every rejection suggests next-available slots  
- ✅ **Clear explanations** – Every decision includes human-readable reasoning
- ✅ **Soft conflicts noted** – Optional attendee conflicts don't block but are reported in response
- ✅ **Deterministic** – Same input always produces same action (strictly enforced before any LLM calls)

#### Example Request:

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

#### Example Response (Success):

```json
{
  "action": "create_meeting",
  "explanation": "Meeting created successfully at 2026-02-09 10:00 UTC",
  "data": {
    "event_id": "abc123def456"
  }
}
```

#### Example Response (Out of Hours):

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
      }
    ]
  }
}
```

For comprehensive testing guidance, see [ORCHESTRATOR_TESTING_GUIDE.md](./ORCHESTRATOR_TESTING_GUIDE.md).

Notes
- Token is stored at `config/token.json` locally for now.
- Uses minimal calendar scope: `https://www.googleapis.com/auth/calendar`.


