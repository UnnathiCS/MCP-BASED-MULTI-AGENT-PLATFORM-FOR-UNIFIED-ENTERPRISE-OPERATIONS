from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.schemas import (
    MeetingCreate,
    MeetingResponse,
    MeetingUpdate,
    AvailabilityRequest,
    AvailabilityResponse,
    SuggestionResponse,
)
from app.services.meetings_service import (
    create_meeting,
    get_meeting,
    list_meetings,
    update_meeting,
    delete_meeting,
    check_availability,
    suggest_meeting_time,
)
# agent planner imports
from app.services.agent.planner import plan as agent_plan_service
from app.services.agent.contracts import AgentRequest, AgentDecision
from app.services.agent.orchestrator import orchestrate
from typing import Any, Dict

router = APIRouter(prefix="/meetings", tags=["meetings"])


def _serialize(obj):
    from datetime import datetime

    if obj is None:
        return None
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize(v) for v in obj]
    return obj


def _prepare_update_dict(updates: MeetingUpdate) -> dict:
    """Convert MeetingUpdate to dict, serializing datetime to ISO strings."""
    data = updates.dict(exclude_unset=True)
    return _serialize(data)


@router.post("/", response_model=MeetingResponse)
def create(meeting: MeetingCreate):
    try:
        # convert datetime objects to ISO strings for the service
        meeting_dict = _serialize(meeting.dict())
        result = create_meeting(meeting_dict)
        event = result["event"]
        explain = result.get("explainability")
        hangout = event.get("hangoutLink") or (event.get("conferenceData", {}).get("entryPoints", [{}])[0].get("uri"))
        resp = {
            **meeting_dict,
            "id": event.get("id"),
            "hangout_link": hangout,
            "raw": event,
            "explainability": explain,
        }
        if "conflicts" in result:
            resp["conflicts"] = result["conflicts"]
        return _serialize(resp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{event_id}")
def get(event_id: str):
    try:
        result = get_meeting(event_id)
        event = result["event"]
        explain = result.get("explainability")
        resp = {
            "id": event.get("id"),
            "title": event.get("summary"),
            "description": event.get("description"),
            "start_time": event.get("start", {}).get("dateTime"),
            "end_time": event.get("end", {}).get("dateTime"),
            "timezone": event.get("start", {}).get("timeZone"),
            "attendees": [a.get("email") for a in event.get("attendees", [])],
            "location": event.get("location"),
            "hangout_link": event.get("hangoutLink") or (event.get("conferenceData", {}).get("entryPoints", [{}])[0].get("uri")),
            "raw": event,
            "explainability": explain,
        }
        return JSONResponse(content=_serialize(resp))
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/")
def list_events(
    time_min: Optional[str] = Query(None, description="RFC3339 timestamp, e.g. 2026-02-08T00:00:00Z"),
    time_max: Optional[str] = Query(None, description="RFC3339 timestamp"),
    page_token: Optional[str] = Query(None),
    max_results: int = Query(50, ge=1, le=250),
):
    try:
        result = list_meetings(time_min, time_max, page_token, max_results)
        return JSONResponse(content=_serialize(result))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{event_id}")
def update(event_id: str, updates: MeetingUpdate):
    try:
        # convert datetime objects back to ISO strings for the service
        update_dict = _prepare_update_dict(updates)
        result = update_meeting(event_id, update_dict)
        event = result["event"]
        explain = result.get("explainability")
        resp = {
            "id": event.get("id"),
            "title": event.get("summary"),
            "description": event.get("description"),
            "start_time": event.get("start", {}).get("dateTime"),
            "end_time": event.get("end", {}).get("dateTime"),
            "timezone": event.get("start", {}).get("timeZone"),
            "attendees": [a.get("email") for a in event.get("attendees", [])],
            "location": event.get("location"),
            "hangout_link": event.get("hangoutLink") or (event.get("conferenceData", {}).get("entryPoints", [{}])[0].get("uri")),
            "raw": event,
            "explainability": explain,
        }
        if "conflicts" in result:
            resp["conflicts"] = result["conflicts"]
        return JSONResponse(content=_serialize(resp))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/availability", response_model=AvailabilityResponse)
def availability(request: AvailabilityRequest):
    try:
        # serialize datetime objects to ISO strings
        time_min = _serialize(request.time_min)
        time_max = _serialize(request.time_max)
        return check_availability(time_min, time_max, request.attendees)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# separate router for agent-specific actions
agent_router = APIRouter(prefix="/agent", tags=["agent"])


@agent_router.post("/plan", response_model=Dict[str, Any])
def agent_plan(request: AgentRequest):
    try:
        # planner returns a plain dictionary
        return agent_plan_service(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@agent_router.post("/schedule", response_model=AgentDecision)
def agent_schedule(request: AgentRequest):
    try:
        return orchestrate(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest", response_model=SuggestionResponse)
def suggest(meeting: MeetingCreate):
    try:
        # convert datetime objects to ISO strings for the service
        meeting_dict = _serialize(meeting.dict())
        return suggest_meeting_time(meeting_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{event_id}")
def delete(event_id: str):
    try:
        result = delete_meeting(event_id)
        return JSONResponse(content=_serialize(result))
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
