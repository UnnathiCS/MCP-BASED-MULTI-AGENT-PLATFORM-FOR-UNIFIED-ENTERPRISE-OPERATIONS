from __future__ import annotations
from unittest.mock import Mock, patch
import pytest

from app.services import meetings_service


def _make_mock_service(insert_resp=None, get_resp=None, list_resp=None, patch_resp=None):
    svc = Mock()
    events = svc.events.return_value
    # insert
    if insert_resp is None:
        insert_resp = {"id": "ev1", "hangoutLink": "https://meet.google.com/abc-123"}
    events.insert.return_value.execute.return_value = insert_resp
    # get
    if get_resp is None:
        get_resp = {"id": "ev1", "summary": "Team Sync", "start": {"dateTime": "2026-02-08T14:00:00Z", "timeZone": "UTC"}, "end": {"dateTime": "2026-02-08T15:00:00Z", "timeZone": "UTC"}, "attendees": [{"email": "alice@example.com"}]}
    events.get.return_value.execute.return_value = get_resp
    # list
    if list_resp is None:
        list_resp = {"items": [get_resp], "nextPageToken": None}
    events.list.return_value.execute.return_value = list_resp
    # patch
    if patch_resp is None:
        patch_resp = {**get_resp, "summary": "Updated"}
    events.patch.return_value.execute.return_value = patch_resp
    # delete returns None
    events.delete.return_value.execute.return_value = None
    return svc


def test_create_meeting_success():
    payload = {
        "title": "Team Sync",
        "description": "Weekly sync",
        "start_time": "2026-02-08T14:00:00+00:00",
        "end_time": "2026-02-08T15:00:00+00:00",
        "timezone": "UTC",
        "attendees": ["alice@example.com"],
        "location": "Conference Room A",
    }

    mock_svc = _make_mock_service()
    with patch("app.services.meetings_service.get_calendar_service", return_value=mock_svc):
        result = meetings_service.create_meeting(payload)
        assert "event" in result
        assert result["event"]["id"] == "ev1"


def test_get_meeting_success():
    mock_svc = _make_mock_service()
    with patch("app.services.meetings_service.get_calendar_service", return_value=mock_svc):
        result = meetings_service.get_meeting("ev1")
        assert "event" in result
        assert result["event"]["id"] == "ev1"


def test_list_meetings_success():
    mock_svc = _make_mock_service()
    with patch("app.services.meetings_service.get_calendar_service", return_value=mock_svc):
        result = meetings_service.list_meetings()
        assert "events" in result
        assert isinstance(result["events"], list)


def test_update_meeting_success():
    mock_svc = _make_mock_service()
    with patch("app.services.meetings_service.get_calendar_service", return_value=mock_svc):
        result = meetings_service.update_meeting("ev1", {"title": "Updated"})
        assert "event" in result
        assert result["event"]["summary"] == "Updated"


def test_delete_meeting_success():
    mock_svc = _make_mock_service()
    with patch("app.services.meetings_service.get_calendar_service", return_value=mock_svc):
        result = meetings_service.delete_meeting("ev1")
        assert result.get("deleted") is True


def test_check_availability_and_conflicts():
    # freebusy returns no busy times
    with patch("app.services.meetings_service.query_freebusy", return_value={"calendars": {"primary": {"busy": []}}}):
        resp = meetings_service.check_availability("2026-02-08T00:00:00Z", "2026-02-09T00:00:00Z", ["alice@example.com"])
        assert "availability" in resp
        assert resp["availability"]["primary"]["busy"] == []
        # conflicts should be empty
        conflicts = meetings_service.find_conflicts({"start_time": "2026-02-08T00:00:00Z", "end_time": "2026-02-08T01:00:00Z", "attendees": ["alice@example.com"]})
        assert conflicts == {}


def test_find_conflicts_freebusy_error():
    # simulate a bad request from Google (e.g., malformed datetime)
    from googleapiclient.errors import HttpError
    err = HttpError(Mock(status=400), b"Bad Request")
    with patch("app.services.meetings_service.check_availability", side_effect=err):
        conflicts = meetings_service.find_conflicts({"start_time": "bad", "end_time": "bad"})
        assert conflicts == {}


def test_check_availability_freebusy_error():
    # simulate freebusy API failure
    from googleapiclient.errors import HttpError
    err = HttpError(Mock(status=400), b"Bad Request")
    with patch("app.services.meetings_service.query_freebusy", side_effect=err):
        resp = meetings_service.check_availability("2026-02-08T00:00:00Z", "2026-02-09T00:00:00Z", ["alice@example.com"])
        # should return empty availability rather than crashing
        assert "availability" in resp


def test_create_with_conflict():
    payload = {
        "title": "Team Sync",
        "description": "Weekly sync",
        "start_time": "2026-02-08T14:00:00+00:00",
        "end_time": "2026-02-08T15:00:00+00:00",
        "timezone": "UTC",
        "attendees": ["alice@example.com"],
        "location": "Conference Room A",
    }
    mock_svc = _make_mock_service()
    with patch("app.services.meetings_service.get_calendar_service", return_value=mock_svc):
        with patch("app.services.meetings_service.find_conflicts", return_value={"primary": [{"start": "x", "end": "y"}]}):
            result = meetings_service.create_meeting(payload)
            assert "conflicts" in result


def test_suggest_meeting_time_advances_on_conflict():
    payload = {
        "title": "Team Sync",
        "description": "Weekly sync",
        "start_time": "2026-02-08T14:00:00+00:00",
        "end_time": "2026-02-08T15:00:00+00:00",
        "timezone": "UTC",
        "attendees": ["alice@example.com"],
        "location": "Conference Room A",
    }
    # first call returns conflict, second call empty
    with patch("app.services.meetings_service.find_conflicts", side_effect=[{"primary": [{"start": "x", "end": "y"}]}, {}]):
        suggestion = meetings_service.suggest_meeting_time(payload, search_hours=1, step_minutes=60)
        assert suggestion["start_time"] != payload["start_time"]
        assert suggestion["explainability"]["status"] == "success"


def test_update_meeting_conflict_propagation():
    mock_svc = _make_mock_service()
    with patch("app.services.meetings_service.get_calendar_service", return_value=mock_svc):
        # patch existing retrieval and patch execute as usual from _make_mock_service
        with patch("app.services.meetings_service.find_conflicts", return_value={"primary": [{"start": "a", "end": "b"}]}):
            result = meetings_service.update_meeting("ev1", {"title": "New"})
            assert "conflicts" in result
