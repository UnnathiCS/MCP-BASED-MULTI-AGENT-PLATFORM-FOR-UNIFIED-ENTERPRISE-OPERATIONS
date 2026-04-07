from fastapi import FastAPI
from app.api.routes import router
from datetime import datetime
import time

app = FastAPI(title="Enterprise Document Review Agent")

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
