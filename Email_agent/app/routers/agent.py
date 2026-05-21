from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.core.security import rate_limit_check, sanitize_input
from app.services.agent_service import process_email_with_agent
from app.services.email_service import extract_customer_name
from app.utils.helpers import retry_function
from app.schemas.schemas import AgentProcessRequest

router = APIRouter(prefix="/agent", tags=["agent"])


class OrchestrateRequest(BaseModel):
    user_request: Optional[str] = None
    request: Optional[str] = None
    content: Optional[str] = None
    intent: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


@router.post("/process")
def process_arbitrary_email(request: Request, data: AgentProcessRequest):
    rate_limit_check(request, max_requests=30, window=60)
    email_content = sanitize_input(data.content, max_length=50000)
    if not email_content:
        raise HTTPException(status_code=400, detail="Content cannot be empty")
    response = retry_function(process_email_with_agent, max_retries=2, initial_delay=1.0, email_content=email_content)
    customer_name = extract_customer_name(email_content)
    return {"response": response, "customer_name": customer_name, "preview": True}


@router.post("/orchestrate")
def orchestrate_email(request: Request, payload: OrchestrateRequest):
    """MCP-style orchestration endpoint for Email Agent.

    Accepts flexible payloads (user_request / request / content) and returns a
    normalized JSON response suitable for MCP integration.
    """
    # Do not enforce interactive rate limits for service-to-service calls
    text = payload.user_request or payload.request or payload.content or ""
    text = sanitize_input(text, max_length=50000)
    if not text:
        raise HTTPException(status_code=400, detail="No request text provided")

    # Process the email content (use retry to be resilient)
    response_text = retry_function(process_email_with_agent, max_retries=2, initial_delay=1.0, email_content=text)
    customer_name = extract_customer_name(text)

    return {
        "status": "success",
        "decision": "email_processed",
        "result": {
            "response": response_text,
            "customer_name": customer_name,
            "request_id": payload.request_id,
            "intent": payload.intent or "email"
        }
    }
