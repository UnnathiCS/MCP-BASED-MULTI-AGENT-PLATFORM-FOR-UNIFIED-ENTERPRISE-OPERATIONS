import threading
import time
from fastapi import APIRouter, Request

from app.middleware.auth import require_admin
from app.schemas.schemas import AutoProcessRequest

router = APIRouter(prefix="/autoprocess", tags=["autoprocess"])

_auto_lock = threading.Lock()
_auto_thread = None
_auto_stop_event = threading.Event()
_auto_interval_seconds = 60


def _auto_process_loop():
    from app.services.email_processor import process_all_emails
    while not _auto_stop_event.is_set():
        try:
            process_all_emails()
        except Exception as e:
            print(f"[auto] Error: {e}")
        waited = 0
        while waited < _auto_interval_seconds and not _auto_stop_event.is_set():
            time.sleep(1)
            waited += 1


@router.post("/start")
def autoprocess_start(request: Request, data: AutoProcessRequest = AutoProcessRequest()):
    require_admin(request)
    global _auto_thread, _auto_interval_seconds
    interval = max(data.interval or 60, 10)
    with _auto_lock:
        if _auto_thread and _auto_thread.is_alive():
            _auto_interval_seconds = interval
            return {"running": True, "interval": _auto_interval_seconds}
        _auto_stop_event.clear()
        _auto_interval_seconds = interval
        _auto_thread = threading.Thread(target=_auto_process_loop, daemon=True)
        _auto_thread.start()
        return {"running": True, "interval": _auto_interval_seconds}


@router.post("/stop")
def autoprocess_stop(request: Request):
    require_admin(request)
    with _auto_lock:
        if _auto_thread and _auto_thread.is_alive():
            _auto_stop_event.set()
            return {"running": False}
    return {"running": False}


@router.get("/status")
def autoprocess_status(request: Request):
    require_admin(request)
    running = _auto_thread is not None and _auto_thread.is_alive() and not _auto_stop_event.is_set()
    return {"running": running, "interval": _auto_interval_seconds}
