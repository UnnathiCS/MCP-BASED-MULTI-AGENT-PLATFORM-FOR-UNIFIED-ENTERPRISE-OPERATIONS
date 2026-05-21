from typing import Optional
from pydantic import BaseModel


class TicketCreateRequest(BaseModel):
    subject: str
    from_email: str
    body: str
    message_id: Optional[str] = None
    in_reply_to: Optional[str] = None


class TicketUpdateRequest(BaseModel):
    assigned_agent: Optional[str] = None
    intent: Optional[str] = None
    response: Optional[str] = None


class ReplyRequest(BaseModel):
    to_email: str
    subject: str
    body: str
    original_message_id: Optional[str] = None
    in_reply_to: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class GoogleVerifyRequest(BaseModel):
    token: str


class AgentProcessRequest(BaseModel):
    content: str


class AutoProcessRequest(BaseModel):
    interval: Optional[int] = 60
