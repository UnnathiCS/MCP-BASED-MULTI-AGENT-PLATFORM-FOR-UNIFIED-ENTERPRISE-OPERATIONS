# Agent Registry System Documentation

## Overview

The **Agent Registry System** is a critical component of the MCP Decision Engine. It enables:

- **Dynamic agent discovery**: Agents self-register or are discovered automatically
- **Capability-based matching**: MCP finds agents by what they can do
- **Input/Output schema validation**: Type-safe agent interactions
- **Health monitoring**: Track agent availability and performance
- **Extensibility**: Easy to add new agents without code changes

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│  Agent Registry System                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ AgentRegistry (agent_registry.py)                   │   │
│  │ - Store agent metadata                              │   │
│  │ - Index capabilities for fast lookup                │   │
│  │ - Track health and metrics                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↑                                   │
│                          │ uses                              │
│                          ↓                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ AgentRegistrationAPI (agent_registration_api.py)    │   │
│  │ - Register/deregister agents                        │   │
│  │ - Check agent health                                │   │
│  │ - Find agents by capability or name                 │   │
│  │ - Get agent info and statistics                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↑                                   │
│           ┌──────────────┼──────────────┐                   │
│           │              │              │                   │
│           ↓              ↓              ↓                   │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────┐        │
│  │ AgentRecord  │ │ Capability   │ │JsonSchema   │        │
│  │ - agent_id   │ │ - action     │ │ (input/out) │        │
│  │ - endpoint   │ │ - description│ │             │        │
│  │ - metadata   │ │ - samples    │ │             │        │
│  │ - sla        │ │              │ │             │        │
│  └──────────────┘ └──────────────┘ └─────────────┘        │
│      (models.py)   (models.py)    (agent_schemas.py)       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Data Models

#### AgentRecord

```python
@dataclass
class AgentRecord:
    agent_id: str                      # Unique identifier (e.g., "document-review-agent")
    name: str                          # Human-readable name
    endpoint: str                      # Base URL (e.g., "http://127.0.0.1:8001")
    capabilities: List[Capability]     # What this agent can do
    allowed_tenants: List[str]        # Multi-tenant isolation
    status: str                        # "registered", "degraded", "offline"
    sla: Dict[str, Any]               # Timeout (ms), concurrency limits
    health_check_path: str            # Path to /health endpoint
    auth: Dict[str, str]              # Authentication details
    priority: int                      # Priority (0-100)
    version: str                       # Agent version
    metadata: Dict[str, Any]           # Cost, team, region, etc.
    last_healthcheck: str             # ISO timestamp
    error_count: int                   # Failure tracking
    success_count: int                # Success tracking
```

#### Capability

```python
@dataclass
class Capability:
    action: str                  # Unique action ID (e.g., "document.review")
    description: str            # Human description
    sample_inputs: List[str]    # Example inputs
    required_fields: List[str]  # Required fields in payload
    embedding: Optional[List]   # Semantic embedding (for matching)
```

#### Schema Objects

```python
@dataclass
class JsonSchema:
    type: str                   # "string", "number", "array", "object"
    description: str
    required: bool
    enum: List[Any]            # Allowed values
    properties: Dict[...]       # For object types
    items: JsonSchema          # For array types
    pattern: str               # Regex for validation
    min_length, max_length     # String constraints
    min_items, max_items       # Array constraints

@dataclass
class InputSchema:
    action: str                # Which action this schema is for
    required_fields: List[str] # Must be present in payload
    schema: Dict[str, JsonSchema]  # Field definitions

@dataclass
class OutputSchema:
    action: str                    # Which action
    status_codes: Dict[int, str]   # Expected HTTP codes
    schema: Dict[str, JsonSchema]  # Response fields
```

---

## Usage Patterns

### Pattern 1: Initialize Registry with Pre-configured Agents

```python
from mcp.agent_registry import AgentRegistry
from mcp.registry_config import get_default_registry_config
from mcp.models import AgentRecord

# Create registry
registry = AgentRegistry()

# Load pre-configured agents from config
config = get_default_registry_config()
for agent_dict in config.get("agents", {}).values():
    agent = AgentRecord.from_dict(agent_dict)
    registry.register_agent(agent)

# Check what we have
print(f"Registered {len(registry.agents)} agents")
```

**Output:**
```
Registered 2 agents
```

### Pattern 2: Programmatic Agent Registration

```python
from mcp.agent_registration_api import AgentRegistrationAPI

# Create API
api = AgentRegistrationAPI(registry)

# Register a new agent
success, message = api.register_agent(
    agent_id="analytics-agent",
    name="Analytics Agent",
    endpoint="http://127.0.0.1:8003",
    capabilities=[
        {
            "action": "analytics.query",
            "description": "Query analytics database",
            "sample_inputs": ["How many users last week?"],
            "required_fields": ["text"],
        }
    ],
    metadata={
        "cost_estimate": 0.25,
        "team": "analytics",
        "region": "us-west-2",
    },
    priority=60,
)

print(f"{message}")  # ✅ Agent analytics-agent registered successfully
```

### Pattern 3: Find Agents by Capability

```python
# Find all agents that can review documents
agents = api.find_agents_by_capability("document.review")
for agent in agents:
    print(f"- {agent.name} ({agent.agent_id})")

# Output:
# - Document Review Agent (document-review-agent)
```

### Pattern 4: Check Agent Health

```python
# Check one agent
is_healthy, status = api.check_agent_health("document-review-agent")
print(f"Document Review: {status}")

# Check all agents
results = api.health_check_all()
for agent_id, is_healthy in results.items():
    icon = "✅" if is_healthy else "❌"
    print(f"{icon} {agent_id}")

# Output:
# ✅ document-review-agent
# ✅ support-agent
```

### Pattern 5: Get Detailed Agent Info

```python
info = api.get_agent_info("document-review-agent")

print(f"Agent: {info['name']}")
print(f"Endpoint: {info['endpoint']}")
print(f"Capabilities:")
for cap in info['capabilities']:
    print(f"  - {cap['action']}: {cap['description']}")
    if 'input_schema' in cap:
        print(f"    Input schema: {cap['input_schema']}")
    if 'output_schema' in cap:
        print(f"    Output schema: {cap['output_schema']}")

print(f"Health: {info['health']}")
```

**Output:**
```
Agent: Document Review Agent
Endpoint: http://127.0.0.1:8001
Capabilities:
  - document.review: Reviews uploaded PDFs for compliance risk, clause analysis, and suggestions
    Input schema: {...}
    Output schema: {...}
  - document.analyze: Extract and summarize document information
    Input schema: {...}
    Output schema: {...}
Health: {'status': 'registered', 'error_count': 0, 'success_count': 42, 'last_check': '2026-03-30T12:34:56Z'}
```

### Pattern 6: List All Capabilities

```python
capabilities = api.list_all_capabilities()

for action, agents in capabilities.items():
    print(f"{action}:")
    for agent_info in agents:
        print(f"  - {agent_info['agent_name']} (priority: {agent_info['priority']})")

# Output:
# document.review:
#   - Document Review Agent (priority: 80)
# document.analyze:
#   - Document Review Agent (priority: 80)
# it.support.text:
#   - Enterprise IT Support Agent (priority: 70)
# it.support.voice:
#   - Enterprise IT Support Agent (priority: 70)
# it.support.ticket:
#   - Enterprise IT Support Agent (priority: 70)
```

### Pattern 7: Validate Input Against Schema

```python
from mcp.agent_schemas import validate_input

# Valid input
payload = {
    "text": "Please review this contract",
    "review_type": "compliance"
}
is_valid, errors = validate_input("document.review", payload)
print(f"Valid: {is_valid}, Errors: {errors}")
# Output: Valid: True, Errors: []

# Invalid input (missing required field)
payload = {"review_type": "compliance"}
is_valid, errors = validate_input("document.review", payload)
print(f"Valid: {is_valid}, Errors: {errors}")
# Output: Valid: False, Errors: ['Missing required field: text']

# Invalid input (wrong type)
payload = {"text": 123}
is_valid, errors = validate_input("document.review", payload)
print(f"Valid: {is_valid}, Errors: {errors}")
# Output: Valid: False, Errors: ["Field 'text' must be string, got int"]
```

### Pattern 8: Get Agent Statistics

```python
stats = api.get_agent_statistics()

print(f"Total agents: {stats['total_agents']}")
print(f"Online: {stats['online_agents']}")
print(f"Degraded: {stats['degraded_agents']}")
print(f"Offline: {stats['offline_agents']}")
print(f"Total capabilities: {stats['total_capabilities']}")
print(f"Success rate: {stats['total_requests']} requests, {stats['total_errors']} errors")

for agent_id, agent_stats in stats['agents'].items():
    print(f"\n{agent_id}:")
    print(f"  Status: {agent_stats['status']}")
    print(f"  Success rate: {agent_stats['success_rate']:.1%}")

# Output:
# Total agents: 2
# Online: 2
# Degraded: 0
# Offline: 0
# Total capabilities: 5
# Success rate: 127 requests, 3 errors
#
# document-review-agent:
#   Status: registered
#   Success rate: 95.2%
#
# support-agent:
#   Status: registered
#   Success rate: 97.1%
```

---

## Input/Output Schema Definitions

### Document Review Agent

#### Input: `document.review`

```python
{
    "text": str,                          # Document text (required, 10-50000 chars)
    "attachments": [
        {
            "filename": str,              # e.g., "contract.pdf"
            "content_type": str,          # e.g., "application/pdf"
            "size_bytes": int,
        }
    ],
    "review_type": str,                   # "full" | "quick" | "compliance" (optional)
}
```

#### Output: `document.review`

```python
{
    "status": str,                        # "success" | "error"
    "risk_score": float,                  # 0-100
    "risk_level": str,                    # "Low" | "Moderate" | "High" | "Critical"
    "clauses": [
        {
            "name": str,
            "status": str,                # "Present" | "Missing" | "Partial"
            "coverage": str,              # "✔" | "⚠" | "✖"
        }
    ],
    "suggestions": [
        {
            "clause": str,
            "suggestion": str,
            "priority": str,              # "low" | "medium" | "high"
        }
    ],
}
```

### IT Support Agent

#### Input: `it.support.text`

```python
{
    "text": str,                          # Support request (required, 5-5000 chars)
    "category_hint": str,                 # Optional hint (optional)
                                          # "Network" | "Email" | "Access" |
                                          # "Hardware" | "Security" | "General"
}
```

#### Output: `it.support.text`

```python
{
    "status": str,                        # "ok" | "error"
    "decision": str,                      # "auto_resolved" | "escalated" | "ticket_created"
    "category": str,                      # Detected category
    "priority": str,                      # "low" | "medium" | "high" | "critical"
    "answer": str,                        # Resolution or response
    "ticket_id": str,                     # Created ticket ID (if escalated)
}
```

#### Input: `it.support.voice`

```python
{
    "audio_file": {
        "filename": str,                  # e.g., "support_call.wav"
        "content_type": str,              # "audio/wav" | "audio/mp3" | "audio/ogg"
        "size_bytes": int,
    },
    "language": str,                      # ISO language code (optional, default "en")
}
```

#### Output: `it.support.voice`

```python
{
    "status": str,                        # "ok" | "error"
    "transcription": str,                 # Transcribed audio text
    "decision": str,                      # Support decision
    "answer": str,                        # Resolution
}
```

---

## Agent Registration Flow

### Step 1: Agent Self-Registration (Push Model)

```
Agent Startup
    ↓
POST /mcp/agents/register
    {
        "agent_id": "my-agent",
        "name": "My Agent",
        "endpoint": "http://...",
        "capabilities": [...]
    }
    ↓
AgentRegistrationAPI.register_agent()
    ↓
Add to AgentRegistry
    ↓
Index capabilities
    ↓
200 OK: {"message": "Registered"}
```

### Step 2: MCP Discovery (Pull Model)

```
MCP Startup
    ↓
AgentRegistrationAPI.health_check_all()
    ↓
For each agent:
    GET {endpoint}/health
    ↓
    200 OK → status = "registered"
    5xx or timeout → status = "degraded" or "offline"
    ↓
Update AgentRegistry
    ↓
Index capabilities for fast lookup
    ↓
Ready for routing
```

### Step 3: Capability-Based Routing

```
User Request: "Please review this contract"
    ↓
MCP: Detect Intent → intent = "document.review"
    ↓
MCP: api.find_agents_by_capability("document.review")
    ↓
Registry: Lookup capability_index["document.review"]
    → Returns: [document-review-agent]
    ↓
MCP: Score candidates (health, capability, policy, etc.)
    ↓
Selected: document-review-agent (score 0.92)
    ↓
Validate input against agent schema
    ↓
Invoke: POST {endpoint}/invoke
    {
        "request_id": "...",
        "trace_id": "...",
        "payload": {...}
    }
    ↓
200 OK: {"result": {...}}
```

---

## Adding a New Agent

### Step 1: Define Agent Record

```python
# In registry_config.py
new_agent = {
    "agent_id": "email-agent",
    "name": "Email Management Agent",
    "endpoint": "http://127.0.0.1:8004",
    "capabilities": [
        {
            "action": "email.send",
            "description": "Send emails",
            "sample_inputs": ["Send password reset email"],
            "required_fields": ["to", "subject", "body"],
        },
        {
            "action": "email.search",
            "description": "Search emails",
            "sample_inputs": ["Find emails from john@company.com"],
            "required_fields": ["query"],
        },
    ],
    "metadata": {
        "cost_estimate": 0.05,
        "team": "communications",
    }
}
```

### Step 2: Define Input/Output Schemas

```python
# In agent_schemas.py

EMAIL_SEND_INPUT = InputSchema(
    action="email.send",
    required_fields=["to", "subject", "body"],
    schema={
        "to": JsonSchema(type="string", required=True, description="Email recipient"),
        "subject": JsonSchema(type="string", required=True, description="Email subject"),
        "body": JsonSchema(type="string", required=True, description="Email body"),
        "cc": JsonSchema(type="array", required=False, description="CC recipients"),
    }
)

EMAIL_SEND_OUTPUT = OutputSchema(
    action="email.send",
    status_codes={200: "Sent", 400: "Invalid", 500: "Error"},
    schema={
        "status": JsonSchema(type="string", enum=["ok", "error"]),
        "message_id": JsonSchema(type="string", description="Email message ID"),
        "timestamp": JsonSchema(type="string", description="Sent time"),
    }
)
```

### Step 3: Register Agent

```python
from mcp.agent_registration_api import AgentRegistrationAPI

api = AgentRegistrationAPI(registry)

success, msg = api.register_agent(
    agent_id="email-agent",
    name="Email Management Agent",
    endpoint="http://127.0.0.1:8004",
    capabilities=[...],
    metadata={...}
)

print(msg)  # ✅ Agent email-agent registered successfully
```

### Step 4: Agent Provides `/invoke` Endpoint

Agent must handle MCP invocation envelope:

```python
# In agent's FastAPI app
@app.post("/invoke")
def invoke(payload: dict):
    """
    Standard MCP invocation contract.
    
    Request:
    {
        "request_id": "uuid",
        "trace_id": "trace-xyz",
        "mcp_meta": {"policies": [...]},
        "payload": {...},  # Agent-specific
        "timeout_ms": 30000
    }
    
    Response:
    {
        "request_id": "uuid",
        "agent_id": "email-agent",
        "status": "ok",
        "result": {...},
        "suggested_actions": []
    }
    """
    request_id = payload.get("request_id")
    mcp_payload = payload.get("payload", {})
    
    # Process request
    result = process_email_send(mcp_payload)
    
    # Return standard response
    return {
        "request_id": request_id,
        "agent_id": "email-agent",
        "status": "ok",
        "result": result,
        "suggested_actions": []
    }
```

---

## Best Practices

### 1. Define Schemas Early

Always define input/output schemas before implementation. This enables:
- Client validation before sending requests
- Type checking in MCP
- Auto-generated documentation
- Better error messages

### 2. Use Capability Actions as Namespaces

```
✅ GOOD:
  document.review
  document.analyze
  email.send
  email.search

❌ BAD:
  review
  analyze
  send
  search
```

### 3. Track Agent Health

Implement `/health` endpoint returning:

```python
{
    "status": "healthy",  # or "degraded"
    "timestamp": "2026-03-30T12:34:56Z",
    "uptime_seconds": 3600,
    "requests_processed": 1000,
    "error_rate": 0.01
}
```

### 4. Include Sample Inputs

Help users understand what queries work:

```python
{
    "action": "document.review",
    "description": "Reviews documents for compliance risks",
    "sample_inputs": [
        "Please review this NDA",
        "Analyze contract for data protection clauses",
        "Quick compliance check",
    ]
}
```

### 5. Version Your Agents

```python
{
    "agent_id": "email-agent-v2",
    "version": "2.0.0",
    "metadata": {
        "previous_version": "1.5.2",
        "deprecation_date": "2026-06-30",
    }
}
```

### 6. Document Tenants

Use `allowed_tenants` for multi-tenancy:

```python
{
    "agent_id": "financial-agent",
    "allowed_tenants": ["acme-corp", "widgets-inc"],  # Restrict to specific tenants
    # or
    "allowed_tenants": ["*"],  # Available to all tenants
}
```

---

## Monitoring & Observability

### Metrics to Track

```python
stats = api.get_agent_statistics()

# Per-agent metrics
- success_rate: Percentage of successful requests
- error_count: Number of failures
- avg_response_time: Average latency
- uptime: Percentage of time available
- concurrency: Current request count

# Registry-level metrics
- total_agents: Count of registered agents
- online_agents: Count in "registered" status
- degraded_agents: Count in "degraded" status
- offline_agents: Count in "offline" status
- total_capabilities: Count of unique actions
```

### Health Check Patterns

```python
# Periodic health checks (every 5 minutes)
async def periodic_health_check():
    while True:
        results = api.health_check_all()
        for agent_id, is_healthy in results.items():
            log_health_metric(agent_id, is_healthy)
        await asyncio.sleep(300)  # 5 minutes

# On-demand health check before routing
def route_request(request):
    agents = api.find_agents_by_capability(intent.action)
    agents = [a for a in agents if a.status == "registered"]
    if not agents:
        api.health_check_all()  # Force refresh
        agents = api.find_agents_by_capability(intent.action)
    # Continue with routing...
```

---

## Summary

The **Agent Registry System** provides:

✅ **Dynamic discovery**: Agents self-register, MCP discovers them  
✅ **Capability-based routing**: Find agents by what they do  
✅ **Schema validation**: Type-safe inputs/outputs  
✅ **Health monitoring**: Track availability and performance  
✅ **Extensibility**: Easy to add new agents  
✅ **Multi-tenancy**: Tenant isolation via allowed_tenants  
✅ **Observability**: Metrics and statistics  

This is the foundation for intelligent, scalable multi-agent systems! 🚀
