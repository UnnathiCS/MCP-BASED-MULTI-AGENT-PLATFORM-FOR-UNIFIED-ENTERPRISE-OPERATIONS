from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from models import ITSupportRequest, ITSupportResponse
from agent import decide_action
from support_agent_graph import decide_action_with_graph, get_graph_visualization, get_graph_mermaid
from voice import VoiceProcessor
import shutil
import logging
from datetime import datetime
import time
import os

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Enterprise IT Support Agent with LangGraph")

voice_processor = VoiceProcessor()
start_time = time.time()

# Load Groq API key from environment
if not os.getenv("GROQ_API_KEY"):
    logger.warning("GROQ_API_KEY not set. LangGraph will use fallback rules.")
    
# Use LangGraph by default, fallback to original if needed
USE_LANGGRAPH = True

# ============================================================================
# LEGACY ENDPOINTS (backward compatible)
# ============================================================================

@app.post("/it-support/text", response_model=ITSupportResponse)
def handle_text(req: ITSupportRequest):
    """Handle text support request using LangGraph workflow"""
    
    if USE_LANGGRAPH:
        try:
            result = decide_action_with_graph(req.message, req.ticket_id)
            logger.info(f"LangGraph decision: {result['decision']}")
        except Exception as e:
            logger.error(f"LangGraph error: {e}. Falling back to original agent.")
            result = decide_action(req.message)
    else:
        result = decide_action(req.message)

    return ITSupportResponse(
        ticket_id=req.ticket_id,
        decision=result["decision"],
        reason=result["reason"],
        answer=result.get("answer"),
        severity=result.get("severity")
    )

@app.post("/it-support/voice", response_model=ITSupportResponse)
def handle_voice(ticket_id: str, audio: UploadFile = File(...)):
    audio_path = f"temp_{audio.filename}"

    with open(audio_path, "wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)

    text = voice_processor.transcribe(audio_path)
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
    Standard MCP invocation endpoint for Support Agent.
    
    Request format:
    {
        "request_id": "uuid",
        "trace_id": "trace-xyz",
        "mcp_meta": {"policies": [...]},
        "payload": {
            "text": "Support request text",
            "action": "it.support.text" or "it.support.voice"
        },
        "timeout_ms": 30000
    }
    
    Response format:
    {
        "request_id": "uuid",
        "agent_id": "support-agent",
        "status": "ok",
        "result": {...},
        "suggested_actions": []
    }
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
            
            # Process text request
            result = decide_action(text)
            
            # Transform to standard response
            response_result = {
                "status": "ok",
                "decision": result.get("decision", ""),
                "category": result.get("category", "General"),
                "priority": result.get("priority", "normal"),
                "answer": result.get("answer", ""),
                "severity": result.get("severity", "low"),
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
            
            # Note: In a real implementation, you would process the actual audio file
            # For now, we return a mock response
            text = audio_file.get("filename", "Audio file")
            result = decide_action(f"[Voice] {text}")
            
            response_result = {
                "status": "ok",
                "transcription": f"[Voice] {text}",
                "decision": result.get("decision", ""),
                "answer": result.get("answer", ""),
                "severity": result.get("severity", "low"),
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
        
        logger.info(f"[{trace_id}] Successfully processed request: {result.get('decision')}")
        
        # Return standard MCP response
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
# LANGGRAPH VISUALIZATION ENDPOINTS (For Evaluation)
# ============================================================================

@app.get("/graph/visualization")
def get_graph_viz():
    """
    Get ASCII art representation of the LangGraph workflow.
    Shows the multi-step decision making process.
    """
    viz = get_graph_visualization()
    return {
        "agent": "support-agent",
        "framework": "LangGraph",
        "visualization": viz,
        "description": "Multi-step workflow with LLM-based decision making"
    }


@app.get("/graph/mermaid")
def get_graph_mermaid_diagram():
    """
    Get Mermaid diagram code for visualizing the workflow.
    Can be rendered at https://mermaid.live/
    """
    mermaid_code = get_graph_mermaid()
    return {
        "agent": "support-agent",
        "framework": "LangGraph",
        "mermaid": mermaid_code,
        "render_url": "https://mermaid.live/",
        "description": "Copy the 'mermaid' field to https://mermaid.live/ to visualize"
    }

# ============================================================================
# DEBUG ENDPOINT - Test LangGraph Directly
# ============================================================================

@app.post("/debug/test-langgraph")
def debug_test_langgraph(req: ITSupportRequest):
    """
    DEBUG ENDPOINT - Test LangGraph workflow and show what LLM actually decides.
    Shows raw output from each node for debugging.
    """
    logger.info("=" * 80)
    logger.info("DEBUG: Testing LangGraph workflow")
    logger.info("=" * 80)
    
    result = decide_action_with_graph(req.message, req.ticket_id)
    
    return {
        "status": "debug_success",
        "ticket_id": req.ticket_id,
        "user_query": req.message,
        "langgraph_result": result,
        "explanation": {
            "step_1_policy_search": f"Found policy: {result.get('policy_confidence', 0) > 0.55}",
            "step_2_sentiment": result.get("sentiment", "UNKNOWN"),
            "step_3_category": result.get("category", "UNKNOWN"),
            "step_4_llm_decision": result.get("decision", "UNKNOWN"),
            "processing_steps": result.get("processing_steps", []),
            "agent_reasoning": result.get("agent_thoughts", "No reasoning available")
        }
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
