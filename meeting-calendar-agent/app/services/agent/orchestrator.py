from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta, time

from app.services.agent.contracts import AgentRequest, AgentDecision
from app.services.agent import availability, conflicts, suggestions, planner, policies
from app.services.meetings_service import create_meeting


# The orchestrator drives the entire agent loop described in Phase‑2.
# STRICT behavior:
# 1. Extract meeting time from intent if not in constraints.
# 2. Check working hours FIRST.
# 3. Check conflicts SECOND.
# 4. Auto-book ONLY if both pass.
# 5. Always provide explanation and alternatives when blocking.


def _extract_time_from_intent(intent: str) -> Tuple[Optional[str], Optional[str]]:
    """Very basic intent parsing to extract time references.
    
    Returns (start_time_iso, end_time_iso) or (None, None) if not found.
    This is a simplified pattern matcher; in production you'd use NER or LLM.
    """
    intent_lower = intent.lower()
    # placeholder: in real world, use datetime NER or call LLM for parsing
    # for now, return None to indicate time must come from constraints
    return None, None


def _get_working_hours_violation(start: str, end: str) -> Optional[str]:
    """Check if meeting is outside 9–18 working hours.
    
    Returns explanation string if violation, else None.
    """
    try:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
        if start_dt.time() < time(hour=9) or end_dt.time() > time(hour=18):
            return f"Requested time {start}–{end} is outside working hours (9–18)"
    except Exception:
        pass
    return None


def _get_conflict_details(conflict_list: List[conflicts.ConflictDetail], avail_map: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract conflict details for response.
    
    Returns dict with who is conflicting and when, or None if no conflicts.
    """
    if not conflict_list:
        return None
    hard_conflicts = [c for c in conflict_list if c.type == "HARD"]
    if hard_conflicts:
        return {
            "type": "hard",
            "details": [c.dict() for c in hard_conflicts],
        }
    # soft conflicts
    soft_conflicts = [c for c in conflict_list if c.type == "SOFT"]
    if soft_conflicts:
        return {
            "type": "soft",
            "details": [c.dict() for c in soft_conflicts],
        }
    return None


def _suggest_alternatives(participants: List[str], blocked_start: str, blocked_end: str, reason: str) -> List[Dict[str, Any]]:
    """Generate alternative time slot suggestions.

    Suggestions are computed by asking the availability engine for free
    intervals and then slicing those intervals into pieces that match the
    requested meeting duration.  We then convert the results to the same
    timezone as the original request and return the first three candidates.
    """
    try:
        blocked_start_dt = datetime.fromisoformat(blocked_start)
        blocked_end_dt = datetime.fromisoformat(blocked_end)
        duration = blocked_end_dt - blocked_start_dt
        # keep request timezone for output
        req_tz = blocked_start_dt.tzinfo
        # search forward one week
        search_end = (blocked_start_dt + timedelta(days=7)).isoformat()
        free = availability.compute_free_slots(participants, blocked_start, search_end)

        candidates: List[Dict[str, Any]] = []
        for slot in free:
            slot_start = datetime.fromisoformat(slot["start"])
            slot_end = datetime.fromisoformat(slot["end"])
            # slide a window of length ``duration`` through the free slot
            cur = slot_start
            while cur + duration <= slot_end and len(candidates) < 10:
                end_candidate = cur + duration
                # convert back to request tz for output
                if req_tz is not None:
                    out_start = cur.astimezone(req_tz)
                    out_end = end_candidate.astimezone(req_tz)
                else:
                    out_start = cur
                    out_end = end_candidate
                candidates.append({
                    "start": out_start.isoformat(),
                    "end": out_end.isoformat(),
                })
                # step forward 30 minutes
                cur += timedelta(minutes=30)
        # return first three, sorted by start
        candidates.sort(key=lambda s: s["start"])
        return candidates[:3]
    except Exception:
        return []


def orchestrate(request: AgentRequest) -> AgentDecision:
    """Full agent orchestration with strict safety checks.
    
    Flow:
    1. Extract time from intent if not in constraints.
    2. Check working hours → if violation, block and suggest alternatives.
    3. Compute availability and detect conflicts.
    4. If conflicts exist → block and suggest alternatives.
    5. If all checks pass → auto-book.
    6. Return AgentDecision with action and explanation.
    """
    participants = request.participants or []
    
    # extract time from constraints or intent
    time_min = None
    time_max = None
    if request.constraints:
        time_min = request.constraints.get("time_min")
        time_max = request.constraints.get("time_max")
    
    # if not in constraints, try parsing intent
    if not time_min or not time_max:
        intent_start, intent_end = _extract_time_from_intent(request.intent or "")
        if intent_start and intent_end:
            time_min = intent_start
            time_max = intent_end
    
    # if still no time, can't proceed
    if not time_min or not time_max:
        return AgentDecision(
            action="request_approval",
            explanation="No meeting time specified in intent or constraints. Please provide time_min and time_max.",
            data={},
        )
    
    # STRICT CHECK 1: working hours
    working_hours_violation = _get_working_hours_violation(time_min, time_max)
    if working_hours_violation:
        alternatives = _suggest_alternatives(participants, time_min, time_max, "outside working hours")
        return AgentDecision(
            action="out_of_working_hours",
            explanation=working_hours_violation,
            data={"suggested_slots": alternatives},
        )
    
    # compute availability for conflict checking
    if request.availability:
        avail_map = request.availability
    else:
        # pull availability directly from calendar for the window
        from app.services.meetings_service import check_availability

        try:
            fb = check_availability(time_min, time_max, participants)
            avail_map = fb.get("availability", {})
        except Exception:
            # if the freebusy call fails, fall back to empty busy lists
            avail_map = {p: {"busy": []} for p in participants}
    
    # STRICT CHECK 2: conflicts
    conflict_list = conflicts.analyze_conflicts(time_min, time_max, avail_map, required=participants)
    conflict_data = _get_conflict_details(conflict_list, avail_map)
    if conflict_data:
        alternatives = _suggest_alternatives(participants, time_min, time_max, "conflict detected")
        return AgentDecision(
            action="conflict_detected",
            explanation=f"Conflict detected for required participants: {conflict_data}",
            data={"conflicts": conflict_data, "suggested_slots": alternatives},
        )
    
    # both checks passed: auto-book
    # generate meeting title from intent if possible
    title = "Meeting"
    if request.intent:
        # use first meaningful part of intent as title
        title = request.intent[:80]
    
    payload = {
        "title": title,
        "description": f"Scheduled by AI agent: {request.intent or 'Auto-scheduled meeting'}",
        "start_time": time_min,
        "end_time": time_max,
        "timezone": "UTC",
        "attendees": participants,
    }
    
    try:
        result = create_meeting(payload)
        event = result.get("event", {})
        return AgentDecision(
            action="create_meeting",
            explanation=f"Meeting created successfully at {time_min}. Hangout: {event.get('hangoutLink', 'N/A')}",
            data={"event_id": event.get("id"), "start": time_min, "end": time_max},
        )
    except Exception as e:
        return AgentDecision(
            action="execution_failed",
            explanation=f"Failed to create meeting: {str(e)}",
            data={},
        )
