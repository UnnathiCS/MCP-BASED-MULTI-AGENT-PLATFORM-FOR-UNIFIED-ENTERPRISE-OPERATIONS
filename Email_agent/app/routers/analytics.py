from fastapi import APIRouter, Request, Query

from app.middleware.auth import require_admin
from app.core.security import rate_limit_check
from app.services.analytics_service import (
    get_ticket_statistics, get_recent_tickets, get_performance_metrics, get_trends
)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/statistics")
def get_statistics(request: Request, days: int = Query(30)):
    rate_limit_check(request, max_requests=60, window=60)
    require_admin(request)
    return get_ticket_statistics(days=days)


@router.get("/recent-tickets")
def get_recent_tickets_endpoint(request: Request, limit: int = Query(10)):
    rate_limit_check(request, max_requests=60, window=60)
    require_admin(request)
    return {"tickets": get_recent_tickets(limit=limit)}


@router.get("/performance")
def get_performance(request: Request, days: int = Query(30)):
    rate_limit_check(request, max_requests=60, window=60)
    require_admin(request)
    return get_performance_metrics(days=days)


@router.get("/trends")
def get_trends_endpoint(request: Request, days: int = Query(30)):
    rate_limit_check(request, max_requests=60, window=60)
    require_admin(request)
    return get_trends(days=days)
