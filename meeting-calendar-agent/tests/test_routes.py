from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app

client = TestClient(app)


def _sample_event():
    return {
        "id": "ev1",
        "summary": "Team Sync",
        "description": "Weekly sync",
        "start": {"dateTime": "2026-02-08T14:00:00+00:00", "timeZone": "UTC"},
        "end": {"dateTime": "2026-02-08T15:00:00+00:00", "timeZone": "UTC"},
        "attendees": [{"email": "alice@example.com"}],
        "location": "Conference Room A",
        "hangoutLink": "https://meet.google.com/abc-123",
    }


def test_post_meeting_route():
    payload = {
        "title": "Team Sync",
        "description": "Weekly sync",
        "start_time": "2026-02-08T14:00:00+00:00",
        "end_time": "2026-02-08T15:00:00+00:00",
        "timezone": "UTC",
        "attendees": ["alice@example.com"],
        "location": "Conference Room A",
    }

def test_post_meeting_invalid_datetime():
    # missing 'T' between date and time should trigger validation error
    payload = {
        "title": "Team Sync",
        "description": "Weekly sync",
        "start_time": "2026-02-08T14:00:00+00:00",
        "end_time": "2026-02-08 15:00:00+00:00",  # invalid format
        "timezone": "UTC",
        "attendees": ["alice@example.com"],
        "location": "Conference Room A",
    }
    r = client.post("/meetings/", json=payload)
    assert r.status_code == 422
    assert "value is not a valid datetime" in r.text

    event = _sample_event()
    with patch(
        "app.routes.meetings.create_meeting",
        return_value={"event": event, "explainability": {"api_call": "events.insert", "status": "success", "details": {}}},
    ):
        r = client.post("/meetings/", json=payload)
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == "ev1"
        assert body["hangout_link"] == event["hangoutLink"]


def test_get_meeting_route():
    event = _sample_event()
    with patch(
        "app.routes.meetings.get_meeting",
        return_value={"event": event, "explainability": {"api_call": "events.get", "status": "success", "details": {}}},
    ):
        r = client.get(f"/meetings/{event['id']}")
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == event["id"]
        assert body["title"] == event["summary"]


def test_list_meetings_route():
    event = _sample_event()
    with patch(
        "app.routes.meetings.list_meetings",
        return_value={"events": [event], "nextPageToken": None, "explainability": {"api_call": "events.list", "status": "success", "details": {}}},
    ):
        r = client.get("/meetings/")
        assert r.status_code == 200
        body = r.json()
        assert "events" in body


def test_put_meeting_route():
    event = _sample_event()
    updated = {**event, "summary": "Updated"}
    with patch(
        "app.routes.meetings.update_meeting",
        return_value={"event": updated, "explainability": {"api_call": "events.patch", "status": "success", "details": {}}},
    ):
        # include a few fields to ensure validation passes
        r = client.put(
            f"/meetings/{event['id']}",
            json={"title": "Updated", "start_time": event["start"]["dateTime"], "end_time": event["end"]["dateTime"], "timezone": event["start"]["timeZone"]},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["title"] == "Updated"


def test_put_conflict_route():
    event = _sample_event()
    updated = {**event, "summary": "Updated"}
    with patch(
        "app.routes.meetings.update_meeting",
        return_value={"event": updated, "explainability": {"api_call": "events.patch", "status": "success", "details": {}}, "conflicts": {"primary": [{"start": "x", "end": "y"}] }},
    ):
        r = client.put(
            f"/meetings/{event['id']}",
            json={"title": "Updated"},
        )
        assert r.status_code == 200
        body = r.json()
        assert "conflicts" in body


def test_delete_meeting_route():
    with patch(
        "app.routes.meetings.delete_meeting",
        return_value={"deleted": True, "explainability": {"api_call": "events.delete", "status": "success", "details": {}}},
    ):
        r = client.delete("/meetings/ev1")
        assert r.status_code == 200
        body = r.json()
        assert body.get("deleted") is True


def test_availability_route():
    with patch(
        "app.routes.meetings.check_availability",
        return_value={"availability": {"primary": {"busy": []}}, "explainability": {"api_call": "freebusy.query", "status": "success"}},
    ):
        r = client.post(
            "/meetings/availability",
            json={"time_min": "2026-02-08T00:00:00Z", "time_max": "2026-02-09T00:00:00Z"},
        )
        assert r.status_code == 200
        body = r.json()
        assert "availability" in body


def test_suggest_route():
    with patch(
        "app.routes.meetings.suggest_meeting_time",
        return_value={"start_time": "2026-02-08T15:00:00+00:00", "end_time": "2026-02-08T16:00:00+00:00", "explainability": {"api_call": "suggest_meeting_time", "status": "success"}},
    ):
        payload = {
            "title": "Team Sync",
            "description": "Weekly sync",
            "start_time": "2026-02-08T14:00:00+00:00",
            "end_time": "2026-02-08T15:00:00+00:00",
            "timezone": "UTC",
            "attendees": ["alice@example.com"],
            "location": "Conference Room A",
        }
        r = client.post("/meetings/suggest", json=payload)
        assert r.status_code == 200
        body = r.json()
        assert body["start_time"] != payload["start_time"]


def test_create_conflict_route():
    payload = {
        "title": "Team Sync",
        "description": "Weekly sync",
        "start_time": "2026-02-08T14:00:00+00:00",
        "end_time": "2026-02-08T15:00:00+00:00",
        "timezone": "UTC",
        "attendees": ["alice@example.com"],
        "location": "Conference Room A",
    }
    event = _sample_event()
    with patch(
        "app.routes.meetings.create_meeting",
        return_value={"event": event, "explainability": {"api_call": "events.insert", "status": "success", "details": {}}, "conflicts": {"primary": [{"start": "x", "end": "y"}]}},
    ):
        r = client.post("/meetings/", json=payload)
        assert r.status_code == 200
        body = r.json()
        assert "conflicts" in body


def test_agent_plan_route():
    req = {"intent": "schedule_meeting", "participants": ["alice@example.com"], "constraints": {"time_min": "2026-02-08T09:00:00+00:00", "time_max": "2026-02-08T10:00:00+00:00"}}
    with patch("app.routes.meetings.agent_plan_service", return_value={"action": "noop", "reason": "ok", "data": {}}):
        r = client.post("/meetings/agent/plan", json=req)
        assert r.status_code == 200
        body = r.json()
        assert body["action"] == "noop"


def test_agent_schedule_route():
    req = {"intent": "schedule_meeting", "participants": ["alice@example.com"], "constraints": {"time_min": "2026-02-08T09:00:00+00:00", "time_max": "2026-02-08T10:00:00+00:00"}}
    with patch("app.routes.meetings.orchestrate", return_value={"action": "executed", "explanation": "done", "data": {}}):
        r = client.post("/agent/schedule", json=req)
        assert r.status_code == 200
        body = r.json()
        assert body["action"] == "executed"
        assert "done" in body["explanation"]


def test_agent_schedule_suggestion_flow():
    req = {"intent": "schedule_meeting", "participants": ["alice@example.com"], "constraints": {"time_min": "2026-02-08T09:00:00+00:00", "time_max": "2026-02-08T10:00:00+00:00"}}
    with patch("app.routes.meetings.orchestrate", return_value={"action": "create_meeting", "explanation": "Meeting created", "data": {"event_id": "ev1"}}):
        r = client.post("/agent/schedule", json=req)
        assert r.status_code == 200
        body = r.json()
        assert body["action"] == "create_meeting"


def test_agent_schedule_out_of_hours():
    req = {"intent": "schedule_meeting", "participants": ["alice@example.com"], "constraints": {"time_min": "2026-02-08T08:00:00+00:00", "time_max": "2026-02-08T19:00:00+00:00"}}
    with patch("app.routes.meetings.orchestrate", return_value={"action": "out_of_working_hours", "explanation": "Outside 9-18", "data": {"suggested_slots": []}}):
        r = client.post("/agent/schedule", json=req)
        assert r.status_code == 200
        body = r.json()
        assert body["action"] == "out_of_working_hours"
        assert "suggested_slots" in body["data"]


def test_agent_schedule_conflict():
    req = {"intent": "schedule_meeting", "participants": ["alice@example.com"], "constraints": {"time_min": "2026-02-08T09:00:00+00:00", "time_max": "2026-02-08T10:00:00+00:00"}}
    with patch("app.routes.meetings.orchestrate", return_value={"action": "conflict_detected", "explanation": "Alice is busy", "data": {"conflicts": {"type": "hard"}, "suggested_slots": []}}):
        r = client.post("/agent/schedule", json=req)
        assert r.status_code == 200
        body = r.json()
        assert body["action"] == "conflict_detected"
        assert "conflicts" in body["data"]
        assert "suggested_slots" in body["data"]


def test_agent_plan_route_unsupported():
    req = {"intent": "unknown"}
    with patch("app.routes.meetings.agent_plan_service", return_value={"action": "request_approval", "reason": "unsupported_intent", "data": {}}):
        r = client.post("/meetings/agent/plan", json=req)
        assert r.status_code == 200
        body = r.json()
        assert body["reason"].startswith("unsupported")
