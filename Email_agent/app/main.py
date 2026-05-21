import os
import sqlite3
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

from app.core.config import SECRET_KEY
from app.database.connection import init_all_dbs
from app.middleware.auth import require_admin
from app.services.email_processor import process_all_emails
from app.routers import tickets, auth, analytics, emails, agent, autoprocess, audit

app = FastAPI(title="Email Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Register all routers
app.include_router(tickets.router)
app.include_router(auth.router)
app.include_router(analytics.router)
app.include_router(emails.router)
app.include_router(agent.router)
app.include_router(autoprocess.router)
app.include_router(audit.router)

# Initialize all databases on startup
init_all_dbs()


@app.get("/")
def ui_redirect():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.get("/{path:path}")
def serve_ui(path: str):
    file_path = FRONTEND_DIR / path
    if file_path.is_file():
        return FileResponse(str(file_path))
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.get("/config")
def config_info():
    return {"mailbox": os.getenv("EMAIL_ADDRESS", "")}


@app.get("/health")
def health_check():
    results = {}
    for name, db in [("database", str(BASE_DIR / "tickets.db")), ("audit_database", str(BASE_DIR / "audit.db"))]:
        try:
            conn = sqlite3.connect(db)
            conn.cursor().execute('SELECT 1')
            conn.close()
            results[name] = "healthy"
        except Exception as e:
            results[name] = f"unhealthy: {e}"
    status = "healthy" if all(v == "healthy" for v in results.values()) else "degraded"
    return JSONResponse(
        content={"status": status, **results, "timestamp": time.time()},
        status_code=200 if status == "healthy" else 503
    )


@app.post("/process-all")
def process_all(request: Request):
    require_admin(request)
    process_all_emails()
    return {"status": "all processed"}
