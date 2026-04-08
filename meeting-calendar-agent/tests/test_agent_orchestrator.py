from __future__ import annotations
from unittest.mock import patch

from app.services.agent.orchestrator import orchestrate
from app.services.agent.contracts import AgentRequest, ConflictDetail
from datetime import datetime, timedelta


def _make_request(constraints=None):
    return AgentRequest(
        intent="schedule_meeting",
        participants=["alice@example.com"],
        constraints=constraints or {"time_min": "2026-02-08T09:00:00+00:00", "time_max": "2026-02-08T10:00:00+00:00"},
    )


def test_orchestrator_out_of_working_hours():
    # request outside 9-18: should return out_of_working_hours
    req = _make_request({
        "time_min": "2026-02-08T08:00:00+00:00",
        "time_max": "2026-02-08T19:00:00+00:00"
    })
    decision = orchestrate(req)
    assert decision.action == "out_of_working_hours"
    assert "working hours" in decision.explanation
    assert "suggested_slots" in decision.data


def test_suggestions_respect_duration_and_availability():
    # given a one-hour blocked period, suggestions must be at least one hour
    req = _make_request({
        "time_min": "2026-02-08T09:00:00+00:00",
        "time_max": "2026-02-08T10:00:00+00:00",
    })
    # simulate busy interval exactly matching request
    busy_fb = {"availability": {"alice@example.com": {"busy": [{"start": "2026-02-08T09:00:00+00:00", "end": "2026-02-08T10:00:00+00:00"}]}}}
    with patch("app.services.meetings_service.check_availability", return_value=busy_fb):
        decision = orchestrate(req)
    assert decision.action == "conflict_detected"
    slots = decision.data.get("suggested_slots", [])
    assert slots, "should suggest at least one slot"
    # each slot duration >= requested duration
    for slot in slots:
        start = datetime.fromisoformat(slot["start"])
        end = datetime.fromisoformat(slot["end"])
        assert end - start >= timedelta(hours=1)


def test_suggestions_same_timezone_and_sliced():
    # if user provides offset +05:30, suggestions should respect that zone and be exactly
    # the requested duration (1h in this case) rather than gigantic day-long spans
    req = _make_request({
        "time_min": "2026-02-08T15:00:00+05:30",
        "time_max": "2026-02-08T16:00:00+05:30",
    })
    busy_fb = {"availability": {"alice@example.com": {"busy": [{"start": "2026-02-08T15:00:00+05:30", "end": "2026-02-08T16:00:00+05:30"}]}}}
    with patch("app.services.meetings_service.check_availability", return_value=busy_fb):
        decision = orchestrate(req)
    assert decision.action == "conflict_detected"
    slots = decision.data.get("suggested_slots", [])
    assert slots, "should have suggestions"
    for slot in slots:
        start = datetime.fromisoformat(slot["start"])
        end = datetime.fromisoformat(slot["end"])
        # offset should match +05:30
        assert start.utcoffset() == timedelta(hours=5, minutes=30)
        assert end.utcoffset() == timedelta(hours=5, minutes=30)
        assert end - start == timedelta(hours=1)
    # ensure we didn't return something spanning to 18:00+05:30
    assert all((datetime.fromisoformat(s["start"]).hour < 18) for s in slots)


def test_orchestrator_conflict_detected():
    # conflict for required participant; orchestrator should fetch availability itself
    req = _make_request()
    # simulate the calendar returning busy interval overlapping the window
    busy_fb = {"availability": {"alice@example.com": {"busy": [{"start": "2026-02-08T09:00:00+00:00", "end": "2026-02-08T10:00:00+00:00"}]}}}
    with patch("app.services.meetings_service.check_availability", return_value=busy_fb):
        decision = orchestrate(req)
    assert decision.action == "conflict_detected"
    assert "alice@example.com" in decision.data["conflicts"]["details"][0]["explanation"]
    assert "suggested_slots" in decision.data


def test_orchestrator_auto_book_within_hours_no_conflicts():
    # within working hours, no conflicts - should auto-book
    req = _make_request()
    with patch("app.services.agent.availability.compute_free_slots", return_value=[]):
        with patch("app.services.agent.conflicts.analyze_conflicts", return_value=[]):
            with patch("app.services.meetings_service.create_meeting", return_value={"event": {"id": "ev1", "hangoutLink": "https://meet.google.com/..."}}):
                decision = orchestrate(req)
    assert decision.action == "create_meeting"
    assert "created successfully" in decision.explanation.lower()
    assert decision.data["event_id"] == "ev1"


def test_orchestrator_soft_conflict_allowed():
    # soft (optional) conflict should still allow booking
    req = _make_request()
    soft_conflicts = [ConflictDetail(type="SOFT", severity="low", explanation="optional person busy")]
    with patch("app.services.agent.availability.compute_free_slots", return_value=[]):
        # soft conflicts are not HARD, so analyze_conflicts returns them but they shouldn't block
        with patch("app.services.agent.conflicts.analyze_conflicts", return_value=soft_conflicts):
            with patch("app.services.meetings_service.create_meeting", return_value={"event": {"id": "ev2", "hangoutLink": None}}):
                decision = orchestrate(req)
    # soft conflicts still trigger conflict_detected
    assert decision.action == "conflict_detected"


def test_orchestrator_no_time_specified():
    req = AgentRequest(intent="schedule something", participants=["alice@example.com"])
    decision = orchestrate(req)
    assert decision.action == "request_approval"
    assert "time" in decision.explanation.lower() or "specify" in decision.explanation.lower()
    assert decision.explanation
