from __future__ import annotations
from typing import Any, Dict, List, Optional
from uuid import uuid4

from googleapiclient.errors import HttpError

from app.integrations.google_calendar_client import get_calendar_service
from app.integrations.google_calendar import query_freebusy
from datetime import datetime, timedelta


# helpers for Phase‑2 availability/conflict detection and AI suggestions

from datetime import datetime


def _to_iso(val):
    if isinstance(val, datetime):
        return val.isoformat()
    return val


def check_availability(
    time_min: datetime | str, time_max: datetime | str, attendees: list[str] | None = None
) -> dict:
    """Return busy intervals for primary calendar and optional attendees.

    The structure mirrors the raw ``freebusy`` response under the key
    ``availability`` for consistency with other service responses.
    """
    # freebusy API expects ISO strings
    tmin = _to_iso(time_min)
    tmax = _to_iso(time_max)
    resp = query_freebusy(tmin, tmax, attendees)
    explain = {"api_call": "freebusy.query", "status": "success", "details": None}
    return {"availability": resp.get("calendars", {}), "explainability": explain}


def _extract_conflicts(fb_response: dict) -> dict:
    # fb_response is expected to be in the shape returned by
    # ``check_availability`` above.
    conflicts: dict = {}
    for cal_id, cal_data in fb_response.get("availability", {}).items():
        busy = cal_data.get("busy")
        if busy:
            conflicts[cal_id] = busy
    return conflicts


def find_conflicts(payload: dict) -> dict:
    """Given a meeting payload, look for overlapping busy slots.

    Returns a mapping of calendar IDs to lists of busy time ranges.  The
    caller may decide how to handle the returned value (warn, block, or
    reschedule).

    We deliberately catch ``HttpError`` from Google freebusy queries so that a
    malformed time range or temporary API failure does **not** prevent the
    caller from continuing with event creation.  The API will log the
    exception and return an empty conflict map in that case.
    """
    try:
        fb = check_availability(
            payload.get("start_time"), payload.get("end_time"), payload.get("attendees")
        )
        return _extract_conflicts(fb)
    except HttpError as e:  # pragma: no cover - defensive path
        # if freebusy fails we don't want to abort the whole operation
        # (the event may still be created), so log and return no conflicts.
        print(f"freebusy query failed: {e}")
        return {}


def suggest_meeting_time(
    payload: dict, search_hours: int = 24, step_minutes: int = 30
) -> dict:
    """Basic availability-based suggestion logic.

    If the requested slot is free for all attendees, returns it
    unchanged.  Otherwise the function searches forward in ``step_minutes``
    increments until it finds an open interval within ``search_hours``.
    This is a placeholder for more advanced AI reasoning that may be
    added in Phase‑3.
    """
    # payload values may already be datetime objects thanks to pydantic
    start = payload["start_time"]
    if isinstance(start, str):
        start = datetime.fromisoformat(start)
    end = payload["end_time"]
    if isinstance(end, str):
        end = datetime.fromisoformat(end)
    duration = end - start
    limit = start + timedelta(hours=search_hours)

    current_start = start
    while current_start <= limit:
        current_end = current_start + duration
        conflicts = find_conflicts(
            {**payload, "start_time": current_start.isoformat(), "end_time": current_end.isoformat()}
        )
        if not conflicts:
            explain = {
                "api_call": "suggest_meeting_time",
                "status": "success",
                "details": {
                    "recommended_start": current_start.isoformat(),
                    "recommended_end": current_end.isoformat(),
                },
            }
            return {"start_time": current_start.isoformat(), "end_time": current_end.isoformat(), "explainability": explain}
        current_start += timedelta(minutes=step_minutes)
    explain = {"api_call": "suggest_meeting_time", "status": "no_available_slot", "details": None}
    return {"start_time": None, "end_time": None, "explainability": explain}


def _build_event_body(payload: Dict) -> Dict:
    # convert any datetime objects to iso strings before sending to Google
    start_iso = _to_iso(payload.get("start_time"))
    end_iso = _to_iso(payload.get("end_time"))
    event: Dict[str, Any] = {
        "summary": payload.get("title"),
        "description": payload.get("description"),
        "start": {"dateTime": start_iso, "timeZone": payload.get("timezone")},
        "end": {"dateTime": end_iso, "timeZone": payload.get("timezone")},
    }

    if payload.get("location"):
        event["location"] = payload.get("location")

    if payload.get("attendees"):
        event["attendees"] = [{"email": e} for e in payload.get("attendees")]

    # Request adding a Meet link
    event["conferenceData"] = {
        "createRequest": {"requestId": uuid4().hex, "conferenceSolutionKey": {"type": "hangoutsMeet"}}
    }

    return event


def create_meeting(payload: Dict) -> Dict:
    # Before creating we can detect existing busy slots; callers may look at
    # the ``conflicts`` key in the response to decide whether to proceed or
    # ask the user to reschedule.  For now we simply return the conflicts
    # but keep the API behaviour the same (event is still created).
    conflicts = find_conflicts(payload)

    service = get_calendar_service()
    body = _build_event_body(payload)
    try:
        created = (
            service.events()
            .insert(calendarId="primary", body=body, conferenceDataVersion=1)
            .execute()
        )
        explain = {"api_call": "events.insert", "status": "success", "details": {"calendarId": "primary"}}
        result = {"event": created, "explainability": explain}
        if conflicts:
            result["conflicts"] = conflicts
        return result
    except HttpError as e:
        explain = {"api_call": "events.insert", "status": "failed", "details": str(e)}
        raise


def get_meeting(event_id: str) -> Dict:
    service = get_calendar_service()
    try:
        event = service.events().get(calendarId="primary", eventId=event_id).execute()
        explain = {"api_call": "events.get", "status": "success", "details": None}
        return {"event": event, "explainability": explain}
    except HttpError as e:
        explain = {"api_call": "events.get", "status": "failed", "details": str(e)}
        raise


def list_meetings(time_min: Optional[str] = None, time_max: Optional[str] = None, page_token: Optional[str] = None, max_results: int = 50) -> Dict:
    service = get_calendar_service()
    params: Dict[str, Any] = {"calendarId": "primary", "singleEvents": True, "orderBy": "startTime", "maxResults": max_results}
    if time_min:
        params["timeMin"] = time_min
    if time_max:
        params["timeMax"] = time_max
    if page_token:
        params["pageToken"] = page_token

    try:
        events = service.events().list(**params).execute()
        explain = {"api_call": "events.list", "status": "success", "details": None}
        return {"events": events.get("items", []), "nextPageToken": events.get("nextPageToken"), "explainability": explain}
    except HttpError as e:
        explain = {"api_call": "events.list", "status": "failed", "details": str(e)}
        raise


def update_meeting(event_id: str, updates: Dict) -> Dict:
    service = get_calendar_service()
    try:
        existing = service.events().get(calendarId="primary", eventId=event_id).execute()
    except HttpError:
        raise

    # Apply updates selectively
    if updates.get("title") is not None:
        existing["summary"] = updates.get("title")
    if "description" in updates:
        existing["description"] = updates.get("description")
    if updates.get("start_time") is not None or updates.get("timezone") is not None:
        existing.setdefault("start", {})["dateTime"] = updates.get("start_time", existing.get("start", {}).get("dateTime"))
        existing.setdefault("start", {})["timeZone"] = updates.get("timezone", existing.get("start", {}).get("timeZone"))
    if updates.get("end_time") is not None or updates.get("timezone") is not None:
        existing.setdefault("end", {})["dateTime"] = updates.get("end_time", existing.get("end", {}).get("dateTime"))
        existing.setdefault("end", {})["timeZone"] = updates.get("timezone", existing.get("end", {}).get("timeZone"))
    if "location" in updates:
        existing["location"] = updates.get("location")
    if "attendees" in updates:
        existing["attendees"] = [{"email": e} for e in (updates.get("attendees") or [])]

    try:
        patched = service.events().patch(calendarId="primary", eventId=event_id, body=existing, conferenceDataVersion=1).execute()
        explain = {"api_call": "events.patch", "status": "success", "details": None}
        result = {"event": patched, "explainability": explain}
        # also surface any conflicts detected for the updated slot
        conflicts = find_conflicts(
            {
                "start_time": patched.get("start", {}).get("dateTime"),
                "end_time": patched.get("end", {}).get("dateTime"),
                "attendees": [a.get("email") for a in patched.get("attendees", [])],
            }
        )
        if conflicts:
            result["conflicts"] = conflicts
        return result
    except HttpError as e:
        explain = {"api_call": "events.patch", "status": "failed", "details": str(e)}
        raise


def delete_meeting(event_id: str) -> Dict:
    service = get_calendar_service()
    try:
        service.events().delete(calendarId="primary", eventId=event_id).execute()
        explain = {"api_call": "events.delete", "status": "success", "details": None}
        return {"deleted": True, "explainability": explain}
    except HttpError as e:
        explain = {"api_call": "events.delete", "status": "failed", "details": str(e)}
        raise
