from fastapi import APIRouter, Request, HTTPException

from app.core.config import ADMIN_USERNAME, ADMIN_PASSWORD, EMAIL_ADDRESS
from app.middleware.auth import is_admin
from app.schemas.schemas import LoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def auth_login(request: Request, data: LoginRequest):
    if data.username == ADMIN_USERNAME and data.password == ADMIN_PASSWORD and ADMIN_PASSWORD:
        request.session['admin'] = True
        request.session['admin_id'] = 'legacy'
        return {"authenticated": True}
    request.session.pop('admin', None)
    raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/auto-login")
def auto_login(request: Request):
    """Auto-login using the configured EMAIL_ADDRESS from .env — no password required."""
    request.session['admin'] = True
    request.session['admin_id'] = 'auto'
    request.session['admin_email'] = EMAIL_ADDRESS
    return {"authenticated": True, "email": EMAIL_ADDRESS}


@router.post("/logout")
def auth_logout(request: Request):
    request.session.pop('admin', None)
    request.session.pop('admin_id', None)
    request.session.pop('admin_email', None)
    return {"authenticated": False}


@router.get("/status")
def auth_status(request: Request):
    return {"authenticated": is_admin(request), "admin_id": request.session.get('admin_id')}
