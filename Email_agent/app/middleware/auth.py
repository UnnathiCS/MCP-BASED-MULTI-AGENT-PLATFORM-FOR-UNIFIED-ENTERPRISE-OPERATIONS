from fastapi import Request, HTTPException


def is_admin(request: Request) -> bool:
    return bool(request.session.get("admin", False))


def require_admin(request: Request):
    if not is_admin(request):
        raise HTTPException(status_code=401, detail="unauthorized")
