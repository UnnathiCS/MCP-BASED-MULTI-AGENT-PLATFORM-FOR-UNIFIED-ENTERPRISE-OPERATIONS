from __future__ import annotations
from typing import List, Optional, Any

from pydantic import BaseModel, Field


from datetime import datetime


class MeetingBase(BaseModel):
    title: str = Field(..., example="Team Sync")
    description: Optional[str] = Field(None, example="Weekly sync")
    # we use native `datetime` here; pydantic will parse ISO strings and
    # serialize back to ISO format in JSON responses.
    start_time: datetime = Field(..., example="2026-02-08T14:00:00+00:00")
    end_time: datetime = Field(..., example="2026-02-08T15:00:00+00:00")
    timezone: str = Field(..., example="UTC")
    attendees: Optional[List[str]] = Field(None, example=["alice@example.com"])
    location: Optional[str] = Field(None, example="Conference Room A")


class MeetingCreate(MeetingBase):
    pass


class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    timezone: Optional[str] = None
    attendees: Optional[List[str]] = None
    location: Optional[str] = None


class Explainability(BaseModel):
    api_call: str
    status: str
    details: Optional[Any]


class MeetingResponse(MeetingBase):
    id: str
    hangout_link: Optional[str]
    raw: Optional[Any]
    explainability: Optional[Explainability]
    conflicts: Optional[Any]

    class Config:
        schema_extra = {
            "example": {
                "id": "abcd1234",
                "title": "Team Sync",
                "description": "Weekly sync",
                "start_time": "2026-02-08T14:00:00+00:00",
                "end_time": "2026-02-08T15:00:00+00:00",
                "timezone": "UTC",
                "attendees": ["alice@example.com"],
                "location": "Conference Room A",
                "hangout_link": "https://meet.google.com/xyz-1234",
            }
        }


# Phase-2 models -----------------------------------------------------------


class AvailabilityRequest(BaseModel):
    time_min: datetime = Field(..., example="2026-02-08T00:00:00Z")
    time_max: datetime = Field(..., example="2026-02-09T00:00:00Z")
    attendees: Optional[List[str]] = Field(None, example=["alice@example.com"])


class AvailabilityResponse(BaseModel):
    availability: Any
    explainability: Optional[Explainability]


class SuggestionResponse(BaseModel):
    start_time: Optional[str]
    end_time: Optional[str]
    explainability: Optional[Explainability]
