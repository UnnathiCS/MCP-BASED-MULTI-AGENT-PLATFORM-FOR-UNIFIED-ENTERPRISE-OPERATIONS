from pydantic import BaseModel
from typing import Optional

class ITSupportRequest(BaseModel):
    ticket_id: str
    message: Optional[str] = None  # for text
    use_voice: bool = False        # true if audio used

class ITSupportResponse(BaseModel):
    ticket_id: str
    decision: str
    reason: str
    answer: Optional[str] = None
    severity: Optional[str] = None
