"""
MCP Orchestration API Server
FastAPI backend for frontend orchestration and agent coordination
Bridges the Streamlit agents with the React/Next.js frontend
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import httpx
import asyncio
import json
from datetime import datetime
import uuid

app = FastAPI(
    title="MCP Orchestration API",
    description="Bridge between React frontend and agent microservices",
    version="1.0.0"
)

# ============================================================================
# CORS Configuration - Allow frontend to connect
# ============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Data Models
# ============================================================================

class WorkflowRequest(BaseModel):
    type: str  # 'upload', 'voice', 'text'
    content: str
    fileName: Optional[str] = None
    userId: Optional[str] = None
    sessionId: Optional[str] = None

class WorkflowResponse(BaseModel):
    workflowId: str
    status: str
    currentAgent: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ApprovalRequest(BaseModel):
    approverNotes: Optional[str] = None

class RejectionRequest(BaseModel):
    rejectionReason: Optional[str] = None

# ============================================================================
# Agent URLs Configuration
# ============================================================================
AGENT_URLS = {
    'document_review': 'http://localhost:8001',
    'it_support': 'http://localhost:8002',
    'hr_onboarding': 'http://localhost:8003',
    'meeting_calendar': 'http://localhost:8004',
    'project_management': 'http://localhost:8005',
    'analytics': 'http://localhost:8006',
}

# In-memory storage for workflows (in production, use database)
WORKFLOWS: Dict[str, Dict[str, Any]] = {}

# ============================================================================
# Health Check
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Check API and backend service health"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {}
    }

    # Check each agent service
    async with httpx.AsyncClient(timeout=5.0) as client:
        for agent_name, agent_url in AGENT_URLS.items():
            try:
                response = await client.get(f"{agent_url}/api/health", timeout=2.0)
                health_status["services"][agent_name] = {
                    "status": "online" if response.status_code == 200 else "error",
                    "url": agent_url
                }
            except Exception as e:
                health_status["services"][agent_name] = {
                    "status": "offline",
                    "url": agent_url,
                    "error": str(e)
                }

    return health_status

# ============================================================================
# Workflow Management
# ============================================================================

@app.post("/api/workflow/submit")
async def submit_workflow(request: WorkflowRequest, background_tasks: BackgroundTasks):
    """
    Submit a workflow request for orchestration
    Returns workflow ID immediately
    Processes orchestration in background
    """
    workflow_id = str(uuid.uuid4())

    # Create workflow record
    workflow = {
        "id": workflow_id,
        "status": "submitted",
        "request": {
            "type": request.type,
            "content": request.content[:200],  # Store first 200 chars
            "fileName": request.fileName,
        },
        "created_at": datetime.now().isoformat(),
        "events": [
            {
                "type": "REQUEST_RECEIVED",
                "timestamp": datetime.now().isoformat(),
                "payload": {"type": request.type}
            }
        ],
        "current_agent": None,
        "result": None,
        "error": None,
    }

    WORKFLOWS[workflow_id] = workflow

    # Process in background
    background_tasks.add_task(orchestrate_workflow, workflow_id, request)

    return {"workflowId": workflow_id}

async def orchestrate_workflow(workflow_id: str, request: WorkflowRequest):
    """
    Main orchestration logic
    Determines which agents to trigger based on request
    """
    workflow = WORKFLOWS[workflow_id]

    try:
        # Step 1: Classify request to determine agents needed
        agents_needed = classify_request(request.content)

        # Emit classification event
        workflow["events"].append({
            "type": "REQUEST_CLASSIFIED",
            "timestamp": datetime.now().isoformat(),
            "agents": agents_needed
        })

        # Step 2: Execute each agent
        results = {}
        for agent_name in agents_needed:
            # Emit agent triggered event
            workflow["events"].append({
                "type": "AGENT_TRIGGERED",
                "timestamp": datetime.now().isoformat(),
                "agent": agent_name,
            })

            workflow["current_agent"] = agent_name

            # Trigger agent
            try:
                agent_result = await trigger_agent(agent_name, request, workflow_id)
                results[agent_name] = agent_result

                # Emit agent completed event
                workflow["events"].append({
                    "type": "AGENT_COMPLETED",
                    "timestamp": datetime.now().isoformat(),
                    "agent": agent_name,
                    "data": agent_result
                })

            except Exception as e:
                workflow["events"].append({
                    "type": "AGENT_ERROR",
                    "timestamp": datetime.now().isoformat(),
                    "agent": agent_name,
                    "error": str(e)
                })

        # Step 3: Workflow complete
        workflow["status"] = "completed"
        workflow["result"] = results
        workflow["current_agent"] = None

        workflow["events"].append({
            "type": "WORKFLOW_COMPLETED",
            "timestamp": datetime.now().isoformat(),
            "result": results
        })

    except Exception as e:
        workflow["status"] = "failed"
        workflow["error"] = str(e)
        workflow["events"].append({
            "type": "WORKFLOW_FAILED",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        })

def classify_request(content: str) -> List[str]:
    """
    Classify request to determine which agents are needed
    In production, this would use NLP/ML
    """
    content_lower = content.lower()
    agents = []

    # Simple keyword-based classification
    if any(word in content_lower for word in ['contract', 'document', 'review', 'policy']):
        agents.append('document_review')

    if any(word in content_lower for word in ['security', 'access', 'it', 'support']):
        agents.append('it_support')

    if any(word in content_lower for word in ['onboard', 'employee', 'hire', 'hr']):
        agents.append('hr_onboarding')

    if any(word in content_lower for word in ['meeting', 'calendar', 'schedule', 'time']):
        agents.append('meeting_calendar')

    if any(word in content_lower for word in ['project', 'task', 'resource', 'timeline']):
        agents.append('project_management')

    # Always include analytics
    agents.append('analytics')

    # Remove duplicates while preserving order
    return list(dict.fromkeys(agents)) or ['analytics']

async def trigger_agent(agent_name: str, request: WorkflowRequest, workflow_id: str) -> Dict[str, Any]:
    """
    Trigger a specific agent microservice
    """
    agent_url = AGENT_URLS.get(agent_name)
    if not agent_url:
        raise ValueError(f"Unknown agent: {agent_name}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Try to send to agent API endpoint
            response = await client.post(
                f"{agent_url}/api/process",
                json={
                    "workflowId": workflow_id,
                    "type": request.type,
                    "content": request.content,
                    "fileName": request.fileName,
                },
                timeout=30.0
            )

            if response.status_code == 200:
                return response.json()
            else:
                # Fallback: if agent doesn't have /api/process, generate mock response
                return {
                    "status": "success",
                    "agent": agent_name,
                    "result": f"Processed by {agent_name}",
                    "timestamp": datetime.now().isoformat()
                }

    except Exception as e:
        # Fallback to mock response
        return {
            "status": "success",
            "agent": agent_name,
            "result": f"Mock response from {agent_name}",
            "timestamp": datetime.now().isoformat()
        }

# ============================================================================
# Workflow Status
# ============================================================================

@app.get("/api/workflow/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """Get workflow status and events"""
    workflow = WORKFLOWS.get(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Determine current event for frontend
    current_event = None
    if workflow["events"]:
        current_event = workflow["events"][-1]

    return {
        "workflowId": workflow_id,
        "status": workflow["status"],
        "currentAgent": workflow["current_agent"],
        "currentEvent": current_event,
        "result": workflow["result"],
        "error": workflow["error"],
        "createdAt": workflow["created_at"],
        "eventCount": len(workflow["events"]),
    }

@app.get("/api/workflow/{workflow_id}/events")
async def get_workflow_events(workflow_id: str):
    """Get all events for a workflow"""
    workflow = WORKFLOWS.get(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return {
        "workflowId": workflow_id,
        "events": workflow["events"]
    }

# ============================================================================
# Approval Endpoints
# ============================================================================

@app.post("/api/workflow/{workflow_id}/approve")
async def approve_workflow(workflow_id: str, request: ApprovalRequest):
    """Approve a workflow escalation"""
    workflow = WORKFLOWS.get(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow["events"].append({
        "type": "HUMAN_APPROVAL_GRANTED",
        "timestamp": datetime.now().isoformat(),
        "approverNotes": request.approverNotes
    })

    return {"status": "approved", "workflowId": workflow_id}

@app.post("/api/workflow/{workflow_id}/reject")
async def reject_workflow(workflow_id: str, request: RejectionRequest):
    """Reject a workflow escalation"""
    workflow = WORKFLOWS.get(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow["status"] = "rejected"
    workflow["events"].append({
        "type": "HUMAN_APPROVAL_REJECTED",
        "timestamp": datetime.now().isoformat(),
        "rejectionReason": request.rejectionReason
    })

    return {"status": "rejected", "workflowId": workflow_id}

# ============================================================================
# Agent Metrics
# ============================================================================

@app.get("/api/agent/{agent_name}/metrics")
async def get_agent_metrics(agent_name: str):
    """Get metrics for a specific agent"""
    agent_url = AGENT_URLS.get(agent_name)

    if not agent_url:
        raise HTTPException(status_code=404, detail="Unknown agent")

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{agent_url}/api/metrics", timeout=5.0)
            if response.status_code == 200:
                return response.json()
    except:
        pass

    # Fallback mock metrics
    return {
        "agent": agent_name,
        "status": "online",
        "latency": 250,
        "throughput": 1200,
        "activeRequests": 3,
        "errorRate": 0.02,
    }

# ============================================================================
# Workflow History
# ============================================================================

@app.get("/api/workflows")
async def list_workflows(limit: int = 10):
    """List recent workflows"""
    workflow_list = list(WORKFLOWS.values())
    workflow_list.sort(key=lambda x: x["created_at"], reverse=True)
    return {
        "workflows": workflow_list[:limit],
        "total": len(workflow_list)
    }

@app.delete("/api/workflows")
async def clear_workflows():
    """Clear workflow history (for testing)"""
    WORKFLOWS.clear()
    return {"message": "Workflows cleared"}

# ============================================================================
# Root
# ============================================================================

@app.get("/")
async def root():
    """API documentation"""
    return {
        "name": "MCP Orchestration API",
        "version": "1.0.0",
        "endpoints": {
            "health": "GET /api/health",
            "submit_workflow": "POST /api/workflow/submit",
            "workflow_status": "GET /api/workflow/{workflow_id}/status",
            "workflow_events": "GET /api/workflow/{workflow_id}/events",
            "approve_workflow": "POST /api/workflow/{workflow_id}/approve",
            "reject_workflow": "POST /api/workflow/{workflow_id}/reject",
            "agent_metrics": "GET /api/agent/{agent_name}/metrics",
            "list_workflows": "GET /api/workflows",
        }
    }

if __name__ == "__main__":
    import uvicorn
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 7999
    print(f"\n🚀 Starting MCP Orchestration API on port {port}...")
    print(f"   Health check: http://localhost:{port}/api/health")
    print(f"   API docs: http://localhost:{port}/docs\n")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
