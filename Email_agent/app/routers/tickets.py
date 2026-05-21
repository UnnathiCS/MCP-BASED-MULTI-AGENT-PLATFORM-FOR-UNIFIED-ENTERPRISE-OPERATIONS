from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Query

from app.middleware.auth import require_admin
from app.core.security import rate_limit_check, sanitize_input, validate_email, sanitize_sql_input
from app.services.ticket_service import (
    create_ticket, update_ticket_with_processing, get_conversation_history,
    list_tickets, get_ticket_by_id
)
from app.services.email_service import send_auto_reply, extract_customer_name
from app.services.agent_service import process_email_with_agent
from app.utils.helpers import retry_function
from app.schemas.schemas import TicketCreateRequest, TicketUpdateRequest, ReplyRequest

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("")
def create_ticket_endpoint(request: Request, data: TicketCreateRequest):
    rate_limit_check(request, max_requests=60, window=60)
    if not validate_email(data.from_email):
        raise HTTPException(status_code=400, detail="Invalid email address")
    email_data = {
        'subject': sanitize_input(data.subject, max_length=500),
        'from': sanitize_input(data.from_email, max_length=255),
        'body': sanitize_input(data.body, max_length=50000),
        'message_id': sanitize_input(data.message_id, max_length=500) if data.message_id else None,
        'in_reply_to': sanitize_input(data.in_reply_to, max_length=500) if data.in_reply_to else None,
    }
    ticket_id, conv_id = create_ticket(email_data)
    return {"ticket_id": ticket_id, "conversation_id": conv_id}


@router.get("")
def list_tickets_endpoint(
    request: Request,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    intent: Optional[str] = None
):
    rate_limit_check(request, max_requests=100, window=60)
    require_admin(request)
    if intent:
        intent = sanitize_sql_input(intent)
    tickets = list_tickets(limit=limit, offset=offset, intent=intent)
    return {"tickets": tickets, "count": len(tickets)}


@router.get("/conversation/{conversation_id}")
def get_conversation(conversation_id: str, request: Request):
    require_admin(request)
    history = get_conversation_history(conversation_id)
    return {"history": history}


@router.get("/{ticket_id}")
def get_ticket(ticket_id: str, request: Request):
    require_admin(request)
    ticket = get_ticket_by_id(ticket_id)
    return {"ticket": ticket}


@router.put("/{ticket_id}")
def update_ticket(ticket_id: str, data: TicketUpdateRequest):
    update_ticket_with_processing(ticket_id, data.assigned_agent, data.intent, data.response)
    return {"status": "updated"}


@router.post("/{ticket_id}/process")
def process_ticket(ticket_id: str):
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    full_history = get_conversation_history(ticket['conversation_id'])
    agent_response = process_email_with_agent(full_history)
    update_ticket_with_processing(ticket_id, 'Mail Agent', 'Processed by Agent', agent_response)
    return {"response": agent_response}


@router.post("/{ticket_id}/reply")
def reply_ticket(ticket_id: str, data: ReplyRequest):
    send_auto_reply(data.to_email, data.subject, data.body, data.original_message_id, data.in_reply_to)
    return {"status": "reply sent"}


@router.get("/{ticket_id}/preview")
def preview_ticket_response(ticket_id: str, request: Request):
    rate_limit_check(request, max_requests=60, window=60)
    require_admin(request)
    ticket_id = sanitize_sql_input(ticket_id)
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    full_history = get_conversation_history(ticket['conversation_id'])
    agent_response = retry_function(process_email_with_agent, max_retries=2, initial_delay=1.0, email_content=full_history)
    customer_name = extract_customer_name(ticket['sender'], ticket['body'])
    return {"ticket_id": ticket_id, "response": agent_response, "customer_name": customer_name, "preview": True}
