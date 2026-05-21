from fastapi import APIRouter, Request

from app.core.security import rate_limit_check
from app.services.email_service import fetch_unread_emails
from app.utils.helpers import retry_function

router = APIRouter(prefix="/emails", tags=["emails"])


@router.post("/fetch")
def fetch_emails(request: Request):
    rate_limit_check(request, max_requests=30, window=60)
    emails = retry_function(fetch_unread_emails, max_retries=2, initial_delay=1.0)
    return {"emails": emails}
