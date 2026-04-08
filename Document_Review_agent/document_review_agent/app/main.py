from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import time
import sys
import os

# Add app directory to path to fix imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import router from api module
from api.routes import router

app = FastAPI(title="Enterprise Document Review Agent")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include router
app.include_router(router)

# Track startup time for uptime calculation
start_time = time.time()

# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@app.get("/health")
def health_check():
    """
    Health check endpoint for MCP monitoring.
    
    Returns agent health status and metrics.
    """
    uptime_seconds = int(time.time() - start_time)
    
    return {
        "status": "healthy",
        "agent_id": "document-review-agent",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": uptime_seconds,
        "version": "1.0.0",
        "endpoints": {
            "review": "/review",
            "mcp": "/invoke",
            "health": "/health"
        }
    }

# Include API routes
app.include_router(router)
