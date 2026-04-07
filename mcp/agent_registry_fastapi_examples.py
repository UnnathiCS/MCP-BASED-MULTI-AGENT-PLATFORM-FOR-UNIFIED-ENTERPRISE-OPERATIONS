"""
FastAPI integration examples for Agent Registry System.

Shows how to:
1. Initialize registry in FastAPI app
2. Expose registry API endpoints
3. Add health check endpoint
4. Implement /invoke endpoint for agents
5. Integrate with MCP router
"""

# ============================================================================
# EXAMPLE 1: MCP Router with Agent Registry
# ============================================================================

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
import logging
from mcp import MCPDecisionEngine, AgentRegistry, AgentRegistrationAPI
from mcp import IntentDetector, PolicyEngine
from mcp import MCPRequest, validate_input
from mcp.registry_config import get_default_registry_config
from mcp.policy_config import get_default_policies
from mcp.models import AgentRecord
import uvicorn

logger = logging.getLogger(__name__)

# Global instances
registry: AgentRegistry = None
api: AgentRegistrationAPI = None
engine: MCPDecisionEngine = None


def init_mcp_system():
    """Initialize MCP system on startup."""
    global registry, api, engine

    # Initialize registry
    registry = AgentRegistry()
    config = get_default_registry_config()
    for agent_dict in config.get("agents", {}).values():
        agent = AgentRecord.from_dict(agent_dict)
        registry.register_agent(agent)

    # Initialize APIs
    api = AgentRegistrationAPI(registry)

    # Initialize intent detector
    intent_detector = IntentDetector()

    # Initialize policy engine
    policy_engine = PolicyEngine()
    for policy in get_default_policies():
        policy_engine.register_policy(policy)

    # Initialize decision engine
    engine = MCPDecisionEngine(registry, intent_detector, policy_engine)

    logger.info("✅ MCP system initialized")


# Create FastAPI app
app = FastAPI(
    title="MCP Router",
    description="Multi-Agent Orchestration via Model Context Protocol",
    version="1.0.0"
)


@app.on_event("startup")
async def startup():
    """Initialize on startup."""
    init_mcp_system()


# ============================================================================
# ENDPOINTS: Agent Registry API
# ============================================================================

@app.get("/agents")
def list_agents():
    """
    List all registered agents.
    
    Returns:
        List of agent information
    """
    agents = api.list_all_agents()
    return {
        "count": len(agents),
        "agents": agents,
    }


@app.get("/agents/{agent_id}")
def get_agent(agent_id: str):
    """
    Get detailed information about an agent.
    
    Args:
        agent_id: Agent identifier
    """
    info = api.get_agent_info(agent_id)
    if not info:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return info


@app.get("/agents/{agent_id}/health")
def check_agent_health(agent_id: str):
    """
    Check if an agent is healthy.
    
    Args:
        agent_id: Agent identifier
    """
    is_healthy, status = api.check_agent_health(agent_id)
    return {
        "agent_id": agent_id,
        "is_healthy": is_healthy,
        "status": status,
    }


@app.post("/agents/health/check-all")
def check_all_health():
    """Check health of all agents."""
    results = api.health_check_all()
    healthy = sum(1 for v in results.values() if v)
    return {
        "total": len(results),
        "healthy": healthy,
        "unhealthy": len(results) - healthy,
        "results": results,
    }


@app.get("/capabilities")
def list_capabilities():
    """
    List all capabilities across all agents.
    
    Returns:
        Dict mapping action -> list of agents supporting it
    """
    capabilities = api.list_all_capabilities()
    return {
        "count": len(capabilities),
        "capabilities": capabilities,
    }


@app.get("/capabilities/{action}")
def get_agents_for_capability(action: str):
    """
    Get all agents that support a specific capability.
    
    Args:
        action: Capability action (e.g., "document.review")
    """
    agents = api.find_agents_by_capability(action)
    return {
        "action": action,
        "count": len(agents),
        "agents": [
            {
                "agent_id": a.agent_id,
                "name": a.name,
                "priority": a.priority,
                "status": a.status,
            }
            for a in agents
        ],
    }


@app.get("/statistics")
def get_statistics():
    """Get registry statistics and monitoring metrics."""
    stats = api.get_agent_statistics()
    return stats


@app.post("/agents/register")
def register_agent(
    agent_id: str,
    name: str,
    endpoint: str,
    capabilities: list,
    metadata: dict = None,
    priority: int = 50,
):
    """
    Register a new agent.
    
    Args:
        agent_id: Unique identifier
        name: Human-readable name
        endpoint: Base URL
        capabilities: List of capability dicts
        metadata: Optional metadata
        priority: Priority (0-100)
    """
    success, message = api.register_agent(
        agent_id=agent_id,
        name=name,
        endpoint=endpoint,
        capabilities=capabilities,
        metadata=metadata or {},
        priority=priority,
    )

    if success:
        return {
            "status": "success",
            "message": message,
            "agent_id": agent_id,
        }
    else:
        raise HTTPException(status_code=400, detail=message)


# ============================================================================
# ENDPOINTS: MCP Decision Engine
# ============================================================================

@app.post("/mcp/route")
def route_request(request_data: dict):
    """
    Main MCP endpoint: route request to appropriate agent(s).
    
    Request body:
    {
        "user_id": "user-123",
        "text": "Please review this contract",
        "priority": "high",
        ...
    }
    
    Returns:
        {
            "request_id": "uuid",
            "status": "ok",
            "mcp_decision": {
                "intent": "document.review",
                "confidence": 0.92,
                "selected_agents": ["document-review-agent"]
            },
            "result": {...},
            "audit": {...}
        }
    """
    try:
        # Create MCP request
        request = MCPRequest(
            user_id=request_data.get("user_id", "anonymous"),
            text=request_data.get("text", ""),
            priority=request_data.get("priority", "normal"),
            metadata=request_data.get("metadata", {}),
        )

        # Process through MCP engine
        response = engine.process_request(request)

        return response.to_dict()

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mcp/health")
def mcp_health():
    """Health check for MCP router."""
    stats = api.get_agent_statistics()
    return {
        "status": "healthy" if stats['online_agents'] > 0 else "degraded",
        "online_agents": stats['online_agents'],
        "total_agents": stats['total_agents'],
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
    }


# ============================================================================
# EXAMPLE 2: Document Review Agent with /invoke endpoint
# ============================================================================

@app.post("/invoke")
def invoke_document_review(payload: dict):
    """
    Standard MCP invocation endpoint for Document Review Agent.
    
    Accepts MCP invocation envelope:
    {
        "request_id": "uuid",
        "trace_id": "trace-xyz",
        "mcp_meta": {"policies": [...]},
        "payload": {
            "text": "Document text to review",
            "review_type": "compliance"
        },
        "timeout_ms": 30000
    }
    
    Returns:
    {
        "request_id": "uuid",
        "agent_id": "document-review-agent",
        "status": "ok",
        "result": {...},
        "suggested_actions": []
    }
    """
    try:
        request_id = payload.get("request_id")
        trace_id = payload.get("trace_id")
        mcp_payload = payload.get("payload", {})

        # Validate input
        is_valid, errors = validate_input("document.review", mcp_payload)
        if not is_valid:
            return JSONResponse(
                status_code=400,
                content={
                    "request_id": request_id,
                    "agent_id": "document-review-agent",
                    "status": "error",
                    "error": f"Invalid input: {errors}",
                    "suggested_actions": [],
                },
            )

        # Extract fields
        text = mcp_payload.get("text", "")
        review_type = mcp_payload.get("review_type", "full")

        # Process document (call your actual logic here)
        result = {
            "status": "success",
            "risk_score": 65,
            "risk_level": "Moderate",
            "clauses": [
                {"name": "Data Protection", "status": "Present", "coverage": "✔"},
                {"name": "Liability", "status": "Missing", "coverage": "✖"},
            ],
            "suggestions": [
                {
                    "clause": "Liability",
                    "suggestion": "Add liability limitation clause",
                    "priority": "high",
                }
            ],
        }

        return {
            "request_id": request_id,
            "agent_id": "document-review-agent",
            "status": "ok",
            "result": result,
            "suggested_actions": [],
        }

    except Exception as e:
        logger.error(f"Error in invoke: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "request_id": payload.get("request_id"),
                "agent_id": "document-review-agent",
                "status": "error",
                "error": str(e),
            },
        )


# ============================================================================
# EXAMPLE 3: Support Agent with /invoke endpoint
# ============================================================================

@app.post("/support/invoke")
def invoke_support_agent(payload: dict):
    """
    MCP invocation for Support Agent.
    
    Accepts:
    {
        "request_id": "uuid",
        "trace_id": "trace-xyz",
        "payload": {
            "text": "My password isn't working"
        }
    }
    
    Returns:
    {
        "request_id": "uuid",
        "agent_id": "support-agent",
        "status": "ok",
        "result": {...},
        "suggested_actions": []
    }
    """
    try:
        request_id = payload.get("request_id")
        mcp_payload = payload.get("payload", {})

        # Validate input
        is_valid, errors = validate_input("it.support.text", mcp_payload)
        if not is_valid:
            return JSONResponse(
                status_code=400,
                content={
                    "request_id": request_id,
                    "agent_id": "support-agent",
                    "status": "error",
                    "error": f"Invalid input: {errors}",
                },
            )

        text = mcp_payload.get("text", "")

        # Process support request (call your actual logic here)
        result = {
            "status": "ok",
            "decision": "auto_resolved",
            "category": "Access",
            "priority": "high",
            "answer": "Please visit https://portal.company.com/reset-password to reset your password.",
            "ticket_id": "TKT-12345",
        }

        return {
            "request_id": request_id,
            "agent_id": "support-agent",
            "status": "ok",
            "result": result,
            "suggested_actions": [],
        }

    except Exception as e:
        logger.error(f"Error in support invoke: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "request_id": payload.get("request_id"),
                "agent_id": "support-agent",
                "status": "error",
                "error": str(e),
            },
        )


# ============================================================================
# EXAMPLE 4: Root health check
# ============================================================================

@app.get("/health")
def health():
    """Health check endpoint."""
    stats = api.get_agent_statistics()
    return {
        "status": "healthy",
        "service": "MCP Router",
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        "agents": {
            "total": stats['total_agents'],
            "online": stats['online_agents'],
            "offline": stats['offline_agents'],
        },
    }


# ============================================================================
# Running the server
# ============================================================================

if __name__ == "__main__":
    # Run: uvicorn agent_registry_fastapi_examples:app --reload --port 8002
    uvicorn.run(app, host="127.0.0.1", port=8002, reload=True)
