from typing import Optional
from fastapi import APIRouter, Request, Query

from app.middleware.auth import require_admin
from app.services.audit_service import get_audit_logs

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs")
def get_audit_logs_endpoint(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    action: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = Query(100, le=1000)
):
    require_admin(request)
    logs = get_audit_logs(start_date=start_date, end_date=end_date,
                          action=action, user_id=user_id, limit=limit)
    return {"logs": logs, "count": len(logs)}
