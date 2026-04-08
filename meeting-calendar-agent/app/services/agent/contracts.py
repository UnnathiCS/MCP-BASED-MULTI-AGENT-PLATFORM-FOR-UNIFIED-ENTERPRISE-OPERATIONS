from __future__ import annotations
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ConflictDetail(BaseModel):
    type: str = Field(..., example="time_overlap")
    severity: str = Field(..., example="high")
    explanation: Optional[str] = Field(None, example="Attendee Alice is busy during requested slot")


class AgentRequest(BaseModel):
    intent: str = Field(..., example="schedule_meeting")
    participants: Optional[List[str]] = Field(None, example=["alice@example.com"])
    constraints: Optional[Any] = Field(
        None,
        example={"time_min": "2026-02-08T00:00:00Z", "time_max": "2026-02-08T23:59:59Z"},
    )
    # structured fields used by the planner
    availability: Optional[Any] = Field(
        None,
        example={"primary": {"busy": []}},
    )
    conflicts: Optional[List[ConflictDetail]] = Field(
        None,
        example=[{"type": "HARD", "severity": "high", "explanation": "..."}],
    )
    urgency: Optional[float] = Field(None, example=1.0)


class AgentDecision(BaseModel):
    action: str = Field(..., example="create_event")
    explanation: Optional[str] = Field(None, example="Selected first available slot after checking conflicts")
    data: Optional[Any] = Field(None, example={"start_time": "...", "end_time": "..."})
