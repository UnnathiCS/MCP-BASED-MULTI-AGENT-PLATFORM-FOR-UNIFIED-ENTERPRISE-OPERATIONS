from __future__ import annotations
from typing import Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import re

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
# Mock calendar for demo
from app.services.mock_calendar import get_calendar_store
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


def _parse_meeting_from_text(user_request: str) -> Dict[str, Any]:
    """
    Parse meeting details from natural language request.
    Extracts: title, date, time, duration, attendees
    """
    import re
    from datetime import datetime, timedelta
    
    meeting_info = {
        "title": "Meeting",
        "attendees": [],
        "duration_minutes": 60,
        "start_time": None,
        "description": user_request
    }
    
    # Extract title (text between "titled" or after common patterns)
    title_match = re.search(r"titled ['\"]?([^'\"]+)['\"]?", user_request, re.IGNORECASE)
    if title_match:
        meeting_info["title"] = title_match.group(1).strip()
    else:
        # Try to extract from beginning
        title_match = re.search(r"^(?:schedule|create|book)\s+(?:a\s+)?(?:meeting|call)?\s*(?:with|for)?\s*(.+?)(?:\s+(?:on|at|with|next|this))", user_request, re.IGNORECASE)
        if title_match:
            meeting_info["title"] = title_match.group(1).strip()
    
    # Extract attendees (email addresses or names after "with")
    email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
    emails = re.findall(email_pattern, user_request)
    meeting_info["attendees"] = emails
    
    # Extract time patterns
    time_patterns = [
        r'(\d{1,2}):(\d{2})\s*(AM|PM)',  # 2:30 PM
        r'at\s+(\d{1,2})\s*(AM|PM)',      # at 2 PM
    ]
    
    time_match = None
    for pattern in time_patterns:
        time_match = re.search(pattern, user_request, re.IGNORECASE)
        if time_match:
            break
    
    # Extract date patterns
    date_patterns = [
        r'(April|Apr)\s+(\d{1,2})',  # April 15
        r'(\d{4})-(\d{2})-(\d{2})',  # 2026-04-15
        r'next\s+(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)',
        r'tomorrow',
        r'today'
    ]
    
    # Try to construct a datetime
    try:
        now = datetime.now()
        
        # Handle relative dates
        if re.search(r'\btomorrow\b', user_request, re.IGNORECASE):
            meeting_info["start_time"] = now + timedelta(days=1)
        elif re.search(r'\btoday\b', user_request, re.IGNORECASE):
            meeting_info["start_time"] = now
        else:
            date_match = re.search(r'(April|Apr)\s+(\d{1,2})', user_request, re.IGNORECASE)
            if date_match:
                day = int(date_match.group(2))
                meeting_info["start_time"] = datetime(now.year, 4, day, 14, 0)
        
        # Add time if extracted
        if time_match and meeting_info["start_time"]:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.lastindex >= 2 else 0
            period = time_match.group(time_match.lastindex)
            
            if period.upper() == 'PM' and hour != 12:
                hour += 12
            elif period.upper() == 'AM' and hour == 12:
                hour = 0
            
            meeting_info["start_time"] = meeting_info["start_time"].replace(hour=hour, minute=minute)
    except:
        pass
    
    # Extract duration
    duration_match = re.search(r'(\d+)\s*(?:hour|hr)', user_request, re.IGNORECASE)
    if duration_match:
        meeting_info["duration_minutes"] = int(duration_match.group(1)) * 60
    
    return meeting_info


@agent_router.post("/orchestrate")
def agent_orchestrate(data: Dict[str, Any]):
    """
    MCP-compatible orchestrate endpoint.
    Takes a natural language request and orchestrates the meeting scheduling workflow.
    Automatically creates meetings in Google Calendar using configured credentials.
    """
    try:
        user_request = data.get("request", "")
        request_id = data.get("request_id", str(uuid.uuid4()))
        
        # Parse meeting details from natural language
        meeting_info = _parse_meeting_from_text(user_request)
        
        # Try to create the meeting using Google Calendar
        created_meeting = None
        error_message = None
        
        try:
            from app.integrations.google_calendar_client import get_calendar_service
            
            service = get_calendar_service()
            
            if service and meeting_info.get("start_time"):
                # Create event object
                start_time = meeting_info["start_time"]
                end_time = start_time + timedelta(minutes=meeting_info["duration_minutes"])
                
                event = {
                    "summary": meeting_info["title"],
                    "description": f"Created via MCP System: {user_request}",
                    "start": {
                        "dateTime": start_time.isoformat(),
                        "timeZone": "UTC"
                    },
                    "end": {
                        "dateTime": end_time.isoformat(),
                        "timeZone": "UTC"
                    },
                    "attendees": [{"email": email} for email in meeting_info.get("attendees", [])]
                }
                
                # Create event in calendar
                event_result = service.events().insert(
                    calendarId="primary",
                    body=event,
                    sendNotifications=True
                ).execute()
                
                created_meeting = {
                    "id": event_result.get("id"),
                    "title": event_result.get("summary"),
                    "time": f"{start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%H:%M')}",
                    "attendees": meeting_info.get("attendees", []),
                    "status": "confirmed",
                    "hangout_link": event_result.get("hangoutLink", ""),
                    "calendar_link": event_result.get("htmlLink", ""),
                    "message": f"✅ Meeting created successfully in your calendar!"
                }
                
                print(f"✅ Meeting created: {created_meeting['title']} ({created_meeting['id']})")
            else:
                error_message = "Could not authenticate with Google Calendar or missing start time"
                if not meeting_info.get("start_time"):
                    error_message = "Please specify a date and time (e.g., 'April 15 at 2 PM')"
        
        except Exception as e:
            error_message = f"Calendar integration: {str(e)}"
            print(f"⚠️ Calendar error: {error_message}")
        
        # Build response
        meetings_response = []
        if created_meeting:
            meetings_response = [created_meeting]
        else:
            meetings_response = [{
                "title": meeting_info["title"],
                "time": "To be determined",
                "attendees": meeting_info.get("attendees", []),
                "status": "pending",
                "message": error_message or f"Request received: {user_request}"
            }]
        
        return JSONResponse(content={
            "status": "success",
            "request_id": request_id,
            "agent": "meetings",
            "decision": "meeting_created" if created_meeting else "pending_details",
            "meetings": meetings_response,
            "suggestions": [
                "Try specifying a specific date (e.g., 'April 15')",
                "Include time (e.g., '2 PM')",
                "Add attendee emails (e.g., 'with john@example.com')"
            ],
            "conflicts": [],
            "availability": {
                "status": "pending",
                "details": "Specify attendees to check availability"
            }
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Orchestrate error: {str(e)}")
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "request_id": request_id,
                "agent": "meetings",
                "decision": "error_handled",
                "meetings": [{
                    "title": "Meeting Request",
                    "message": f"Error: {str(e)}",
                    "status": "error"
                }],
                "suggestions": ["Try providing more details about your meeting"],
                "conflicts": [],
                "availability": {"status": "error"}
            }
        )


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
