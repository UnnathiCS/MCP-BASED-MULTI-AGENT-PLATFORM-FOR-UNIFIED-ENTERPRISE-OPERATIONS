from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from models import ITSupportRequest, ITSupportResponse
from agent import decide_action
import shutil
import logging
from datetime import datetime
import time
import os
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Enterprise IT Support Agent - Optimized")

# Lazy-load voice_processor to speed up startup
voice_processor = None

def get_voice_processor():
    global voice_processor
    if voice_processor is None:
        from voice import VoiceProcessor
        voice_processor = VoiceProcessor()
    return voice_processor

start_time = time.time()

# Optimization: Use thread pool for async operations with timeout
executor = ThreadPoolExecutor(max_workers=5)
REQUEST_TIMEOUT = 5  # 5 second timeout for operations

# Try to load LangGraph, but don't fail if unavailable
TRY_LANGGRAPH = False
try:
    from support_agent_graph import decide_action_with_graph, get_graph_visualization, get_graph_mermaid
    if os.getenv("GROQ_API_KEY"):
        TRY_LANGGRAPH = True
        logger.info("LangGraph available with Groq API key")
    else:
        logger.info("Groq API key not set - using lightweight agent")
except Exception as e:
    logger.warning(f"LangGraph not available: {e}. Using lightweight agent instead.")
    TRY_LANGGRAPH = False

# ============================================================================
# LEGACY ENDPOINTS (backward compatible)
# ============================================================================

@app.post("/it-support/text", response_model=ITSupportResponse)
def handle_text(req: ITSupportRequest):
    """Handle text support request - Fast, lightweight, timeout-safe"""
    
    try:
        # Try LangGraph with timeout
        if TRY_LANGGRAPH:
            try:
                # Run with timeout using executor
                future = executor.submit(decide_action_with_graph, req.message, req.ticket_id)
                result = future.result(timeout=REQUEST_TIMEOUT)
                logger.info(f"LangGraph success: {result.get('decision')}")
            except (FutureTimeoutError, TimeoutError):
                logger.warning("LangGraph timeout - using lightweight agent")
                result = decide_action(req.message)
            except Exception as e:
                logger.warning(f"LangGraph error: {e} - using lightweight agent")
                result = decide_action(req.message)
        else:
            # Use lightweight agent directly
            result = decide_action(req.message)
        
        # Build response
        return ITSupportResponse(
            ticket_id=req.ticket_id,
            decision=result.get("decision", "RAISE_TICKET"),
            reason=result.get("reason", "Processing completed"),
            answer=result.get("answer"),
            severity=result.get("severity", "P3")
        )
        
    except Exception as e:
        logger.error(f"Handler error: {e}")
        # Failsafe response
        return ITSupportResponse(
            ticket_id=req.ticket_id,
            decision="RAISE_TICKET",
            reason="System processing error",
            answer="Your IT support ticket has been created. Our team will assist you shortly.",
            severity="P3"
        )

@app.post("/it-support/voice", response_model=ITSupportResponse)
def handle_voice(ticket_id: str, audio: UploadFile = File(...)):
    audio_path = f"temp_{audio.filename}"

    with open(audio_path, "wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)

    text = get_voice_processor().transcribe(audio_path)
    result = decide_action(text)

    return ITSupportResponse(
        ticket_id=ticket_id,
        decision=result["decision"],
        reason=f"Voice input processed → {result['reason']}",
        answer=result.get("answer"),
        severity=result.get("severity")
    )

# ============================================================================
# MCP COMPLIANT ENDPOINT
# ============================================================================

@app.post("/invoke")
def invoke_mcp(payload: dict):
    """
    Optimized MCP invocation endpoint - Fast and timeout-safe
    """
    try:
        request_id = payload.get("request_id", "unknown")
        trace_id = payload.get("trace_id", "unknown")
        mcp_payload = payload.get("payload", {})
        action = mcp_payload.get("action", "it.support.text")
        
        logger.info(f"[{trace_id}] Received MCP invocation: action={action}")
        
        # Validate payload
        if action == "it.support.text":
            text = mcp_payload.get("text", "")
            if not text:
                return JSONResponse(
                    status_code=400,
                    content={
                        "request_id": request_id,
                        "agent_id": "support-agent",
                        "status": "error",
                        "error": "Missing required field: text",
                        "suggested_actions": []
                    }
                )
            
            # Process with timeout
            try:
                future = executor.submit(decide_action, text)
                result = future.result(timeout=REQUEST_TIMEOUT)
            except FutureTimeoutError:
                logger.warning("Decision timeout - using fallback")
                result = {
                    "decision": "RAISE_TICKET",
                    "category": "General",
                    "priority": "P3",
                    "reason": "Processing timeout",
                    "answer": "Your ticket has been created",
                    "severity": "P3"
                }
            except Exception as e:
                logger.error(f"Error in decision: {e}")
                result = {
                    "decision": "RAISE_TICKET",
                    "category": "General",
                    "priority": "P3",
                    "reason": "System error",
                    "answer": "Your ticket has been created",
                    "severity": "P3"
                }
            
            response_result = {
                "status": "ok",
                "decision": result.get("decision", ""),
                "category": result.get("category", "General"),
                "priority": result.get("priority", "P3"),
                "answer": result.get("answer", ""),
                "severity": result.get("severity", "P3"),
                "reason": result.get("reason", ""),
            }
            
        elif action == "it.support.voice":
            audio_file = mcp_payload.get("audio_file", {})
            if not isinstance(audio_file, dict) or "filename" not in audio_file:
                return JSONResponse(
                    status_code=400,
                    content={
                        "request_id": request_id,
                        "agent_id": "support-agent",
                        "status": "error",
                        "error": "Invalid audio_file structure",
                        "suggested_actions": []
                    }
                )
            
            # Mock voice processing
            text = audio_file.get("filename", "Audio file")
            result = decide_action(f"[Voice] {text}")
            
            response_result = {
                "status": "ok",
                "transcription": f"[Voice] {text}",
                "decision": result.get("decision", ""),
                "answer": result.get("answer", ""),
                "severity": result.get("severity", "P3"),
            }
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "request_id": request_id,
                    "agent_id": "support-agent",
                    "status": "error",
                    "error": f"Unknown action: {action}",
                    "suggested_actions": []
                }
            )
        
        logger.info(f"[{trace_id}] Successfully processed: {result.get('decision')}")
        
        return {
            "request_id": request_id,
            "agent_id": "support-agent",
            "status": "ok",
            "result": response_result,
            "suggested_actions": []
        }
        
    except Exception as e:
        logger.error(f"Error in invoke: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "request_id": payload.get("request_id", "unknown"),
                "agent_id": "support-agent",
                "status": "error",
                "error": str(e),
                "suggested_actions": []
            }
        )

# ============================================================================
# GRAPH VISUALIZATION ENDPOINTS (Simplified - Optional)
# ============================================================================

@app.get("/graph/visualization")
def get_graph_viz():
    """Get ASCII art representation of the workflow"""
    viz = """
    ┌─────────────────┐
    │   Query Input   │
    └────────┬────────┘
             │
    ┌────────v────────┐
    │ Policy Lookup   │──────┐
    └────────┬────────┘      │
             │                │ (High Confidence)
    ┌────────v────────┐      │
    │ Sentiment Check │      │
    └────────┬────────┘      │
             │                │
    ┌────────v────────┐      │
    │  Category Det.  │      │
    └────────┬────────┘      │
             │                │
    ┌────────v────────────┐  │
    │ Decision Logic      │<─┘
    └────────┬────────────┘
             │
    ┌────────v──────────────┐
    │ Auto Resolve / Raise  │
    │ Ticket / Escalate     │
    └───────────────────────┘
    """
    return {
        "agent": "support-agent",
        "framework": "Lightweight-Optimized",
        "visualization": viz,
        "description": "Optimized workflow with <5s response time"
    }


@app.get("/graph/mermaid")
def get_graph_mermaid_diagram():
    """Get Mermaid diagram code"""
    mermaid_code = """graph TD
    A[User Query] --> B[Policy Lookup]
    B -->|Match High Conf| C[Auto Resolve]
    B -->|No Match| D[Sentiment Check]
    D -->|Negative| E[Escalate]
    D -->|Positive/Neutral| F[Category Detection]
    F --> G{Decision Logic}
    G -->|Outage| H[Escalate]
    G -->|Access| I[Auto Response]
    G -->|Default| J[Raise Ticket]
    """
    return {
        "agent": "support-agent",
        "framework": "Lightweight",
        "mermaid": mermaid_code,
        "render_url": "https://mermaid.live/",
        "description": "Lightweight workflow - fast and reliable"
    }

# ============================================================================
# DEBUG ENDPOINT - Quick Test
# ============================================================================

@app.post("/debug/test")
def debug_test(req: ITSupportRequest):
    """Quick test endpoint"""
    logger.info("=" * 60)
    logger.info("DEBUG: Testing optimized agent")
    logger.info("=" * 60)
    
    result = decide_action(req.message)
    
    return {
        "status": "debug_success",
        "ticket_id": req.ticket_id,
        "query": req.message,
        "decision_result": result,
        "performance": "optimized - <1s response"
    }

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
        "agent_id": "support-agent",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": uptime_seconds,
        "version": "1.0.0",
        "endpoints": {
            "text": "/it-support/text",
            "voice": "/it-support/voice",
            "mcp": "/invoke",
            "health": "/health"
        }
    }


# ============================================================================
# UVICORN STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
