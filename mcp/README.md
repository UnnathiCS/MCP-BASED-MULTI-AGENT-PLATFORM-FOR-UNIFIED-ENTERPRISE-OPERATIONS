# MCP (Model Context Protocol) Decision Engine

A production-ready orchestration layer that intelligently routes requests to multiple AI agents based on intent, policy, and context.

## Overview

The MCP Decision Engine is the central nervous system of a multi-agent AI system. Instead of agents calling each other directly, all coordination flows through MCP, ensuring:

- **Centralized Control**: All routing decisions in one place
- **Policy Enforcement**: Apply compliance, cost, and security rules globally
- **Observability**: Full audit trail of every decision
- **Flexibility**: Add/remove agents without code changes
- **Scalability**: Horizontal scaling without tight coupling

## Architecture

```
User Request
    ↓
MCP Decision Engine
    ├─ Intent Detection (rule + model + semantic)
    ├─ Agent Registry Lookup
    ├─ Candidate Scoring & Ranking
    ├─ Policy Filtering
    ├─ Plan Generation
    └─ Agent Invocation & Aggregation
    ↓
Selected Agent(s)
    ↓
Consolidated Response + Audit Trail
```

## Core Components

### 1. Models (`models.py`)
Data classes for all request/response shapes:
- `MCPRequest`: User request to MCP
- `MCPDecision`: MCP's routing decision
- `MCPResponse`: Final response with audit trail
- `AgentRecord`: Registry entry for an agent
- `ExecutionPlan`: Task execution plan
- `PolicyRule`: Policy constraints

### 2. Intent Detector (`intent_detector.py`)
Multi-stage pipeline:
1. **Rule-based matching**: Keywords, patterns, domain synonyms
2. **Model-based classification**: LLM or fine-tuned transformer
3. **Semantic fallback**: Embedding similarity with capability descriptions

Returns ranked list of intents with confidence scores and rationale.

### 3. Agent Registry (`agent_registry.py`)
Central repository for agent metadata:
- Capabilities and supported actions
- Health status and metrics
- SLA and cost estimates
- Endpoint and authentication
- Capability-based indexing for fast lookup

### 4. Policy Engine (`policy_engine.py`)
Enforces rules for:
- **Agent filtering**: Allowed/blocked agents per request
- **Data handling**: Masking, redaction, PII protection
- **Cost limits**: Cap spending per request
- **Approval requirements**: Escalation for sensitive operations
- **Compliance**: GDPR, data residency, audit logging

### 5. Decision Engine (`decision_engine.py`)
Main orchestration logic:
- **Scoring algorithm**: Intent match + capability + health + policy + cost + priority
- **Plan generation**: Sync/async/pipeline execution modes
- **Agent invocation**: Standard contract with timeout/retry
- **Result aggregation**: Consolidate multi-agent results
- **Fallback handling**: Graceful degradation on errors

## Request Flow

### Step-by-Step Decision Process

```python
1. Receive MCPRequest
   → User text, attachments, metadata, priority

2. Intent Detection
   → Top N intents with confidence scores

3. Find Candidates
   → Agents supporting detected intent

4. Score Candidates
   → intent_match (30%)
   → capability_match (25%)
   → health_score (20%)
   → policy_score (15%)
   → cost_score (5%)
   → priority_boost (variable)

5. Policy Filtering
   → Remove blocked agents
   → Check approval requirements
   → Apply data handling rules

6. Generate Plan
   → Sync vs. async vs. pipeline
   → Task decomposition
   → Cost/duration estimates

7. Invoke Agents
   → Standard contract with mcp_meta
   → Handle timeouts and retries
   → Capture structured responses

8. Aggregate Results
   → Consolidate agent outputs
   → Handle suggested actions (escalations)
   → Produce final response with audit trail
```

## Usage

### Quick Start

```python
from mcp import (
    MCPDecisionEngine,
    AgentRegistry,
    IntentDetector,
    PolicyEngine,
    MCPRequest,
)
from mcp.registry_config import get_default_registry_config
from mcp.policy_config import get_default_policies

# Initialize components
registry = AgentRegistry()
intent_detector = IntentDetector()
policy_engine = PolicyEngine()

# Register agents from config
config = get_default_registry_config()
for agent_dict in config.get("agents", {}).values():
    registry.register_agent(AgentRecord.from_dict(agent_dict))

# Register policies
for policy in get_default_policies():
    policy_engine.register_policy(policy)

# Create decision engine
engine = MCPDecisionEngine(registry, intent_detector, policy_engine)

# Process a request
request = MCPRequest(
    user_id="user-123",
    text="Please review this contract for data protection clauses",
    priority="high"
)

response = engine.process_request(request)

# Response includes:
# - mcp_decision: routing decision with reasoning
# - result: consolidated agent output
# - audit: trace_id, matched_policies, timestamp
# - agent_responses: raw responses from agents
```

### Registering a New Agent

```python
from mcp.models import AgentRecord, Capability

agent = AgentRecord(
    agent_id="email-agent",
    name="Email Triage Agent",
    endpoint="http://localhost:9000",
    capabilities=[
        Capability(
            action="email.triage",
            description="Classifies and routes emails",
            sample_inputs=["Spam detection", "Auto-reply"]
        )
    ],
    sla={"timeout_ms": 5000, "concurrency_limit": 20},
    priority=60,
    metadata={"cost_estimate": 0.05}
)

registry.register_agent(agent)
```

### Adding a Custom Policy

```python
from mcp.models import PolicyRule

policy = PolicyRule(
    rule_id="gdpr-compliance",
    name="GDPR Compliance",
    condition={"user_role": ["eu_resident"]},
    allowed_agents=["document-review-agent"],
    blocked_agents=["external-vendor"],
    requires_approval=True,
    data_handling={"mask_fields": ["email", "phone"]},
    enabled=True
)

policy_engine.register_policy(policy)
```

## Intent Detection

The intent detector uses a three-tier approach for robustness:

### 1. Rule-Based Matching
Fast keyword patterns for high-confidence cases:
```python
intent_detector.register_intent_rule(
    "email.urgent",
    keywords=["urgent", "asap", "critical"],
    confidence=0.85
)
```

### 2. Model-Based Classification
(Placeholder in this implementation; plug in real LLM):
```python
# Example: use HuggingFace zero-shot classification
from transformers import pipeline

classifier = pipeline("zero-shot-classification")
result = classifier(text, candidate_labels=["intent1", "intent2", ...])
```

### 3. Semantic Fallback
Compare request embedding with capability descriptions:
```python
# Compute embedding of request
request_embedding = embed_text(request.text)

# Find closest capability
agent = find_agent_by_semantic_similarity(request_embedding)
```

## Scoring Algorithm

Agents are scored on multiple dimensions:

```python
overall_score = (
    0.30 * intent_match            # How well intent aligns with agent
    + 0.25 * capability_match      # Does agent have the capability?
    + 0.20 * health_score          # Is agent healthy? (0 if offline)
    + 0.15 * policy_score          # Passes policy filters?
    + 0.05 * cost_score            # Cost efficiency
    + priority_boost               # Request urgency
)
```

Only agents with score > 0 and health_score > 0 are considered.

## Execution Plans

MCP supports three execution modes:

### 1. Sync (Default)
Single agent, synchronous, blocking:
```python
plan = ExecutionPlan(mode="sync")
```

### 2. Async
Single or multiple agents in parallel:
```python
plan = ExecutionPlan(mode="async")
# Tasks executed in parallel
```

### 3. Pipeline
Sequential task chain (output of task N feeds task N+1):
```python
plan = ExecutionPlan(mode="pipeline")
# Task 1 -> Task 2 -> Task 3
# Task 2 depends on Task 1 output
```

## Policy Engine

Policies are declarative rules that constrain routing:

### Example Policies

**High-Priority Escalation**
```python
PolicyRule(
    rule_id="critical-escalation",
    name="Critical Priority Escalation",
    condition={"request_priority": ["critical"]},
    allowed_agents=["support-agent"],
    requires_approval=True
)
```

**Sensitive Data Protection**
```python
PolicyRule(
    rule_id="pii-protection",
    name="PII Data Protection",
    condition={"contains_sensitive_data": True},
    allowed_agents=["trusted-agent"],
    data_handling={"mask_fields": ["ssn", "credit_card"]}
)
```

**Role-Based Access**
```python
PolicyRule(
    rule_id="compliance-access",
    name="Compliance Officer Access",
    condition={"user_role": ["compliance_officer"]},
    allowed_agents=["document-review-agent", "audit-agent"]
)
```

## Agent Invocation Contract

MCP invokes agents with a standard request envelope:

```python
# Request sent to agent
{
    "request_id": "uuid",
    "trace_id": "trace-xxx",
    "user_id": "user-123",
    "mcp_meta": {
        "trace_id": "trace-xxx",
        "user_id": "user-123",
        "policies": ["sensitive_data_policy"]
    },
    "payload": { /* agent-specific content */ },
    "idempotency_key": "sha256(...)",
    "timeout_ms": 30000
}

# Agent response
{
    "request_id": "uuid",
    "agent_id": "document-review-agent",
    "status": "ok",  # or "error", "timeout"
    "result": { /* agent-specific output */ },
    "suggested_actions": [
        {"action": "escalate", "params": {...}}
    ],
    "metrics": {"processing_ms": 120},
    "error": null
}
```

**Key invariant**: Agents return suggested actions; they do NOT call other agents directly. MCP processes suggestions.

## Observability

Every MCP decision is fully auditable:

```python
response.audit = {
    "timestamp": "2026-03-30T12:34:56.789Z",
    "trace_id": "trace-xyz",
    "selected_agents": ["document-review-agent"],
    "matched_policies": ["high_priority_escalation"],
}
```

Use trace_id for distributed tracing across the entire system.

## Error Handling & Fallbacks

MCP handles failures gracefully:

1. **Agent Timeout**: Mark agent as degraded, try next candidate
2. **All Agents Fail**: Return degraded response with partial results
3. **Low Confidence**: Escalate to manual triage (create support ticket)
4. **Policy Violation**: Block request, return clear error

## Testing

Run the example usage script:

```bash
cd /path/to/mcp
python example_usage.py
```

Outputs example scenarios:
1. Document review request
2. IT support request
3. Password reset (lower confidence)
4. Multi-step workflow (escalation)
5. Registry status check

## File Structure

```
mcp/
├── __init__.py                 # Public API exports
├── models.py                   # Data classes (Request, Decision, Response, etc.)
├── agent_registry.py           # Agent repository
├── intent_detector.py          # Intent classification
├── policy_engine.py            # Policy evaluation
├── decision_engine.py          # Main orchestration logic
├── registry_config.py          # Example agent registry
├── policy_config.py            # Example policies
├── example_usage.py            # Usage examples and demo
└── README.md                   # This file
```

## Key Design Decisions

1. **No Direct Agent Calls**: Agents cannot call each other; all coordination via MCP
2. **Stateless**: Each request is independent; MCP is stateless and horizontally scalable
3. **Declarative Policies**: Policies are rules, not code; easy to audit and update
4. **Transparent Scoring**: Scoring algorithm is visible and explainable
5. **Best-Effort Invocation**: MCP is resilient; agent failures don't crash the system
6. **Audit Everything**: Every decision logged with rationale and policy info

## Next Steps

To integrate MCP into your system:

1. **Adapt Agent Contracts**: Update Document Review and Support agents to accept MCP invocation envelope
2. **Add Health Endpoints**: Each agent exposes `/health` endpoint
3. **Wire FastAPI Routes**: Create `/mcp/route` endpoint in a new FastAPI app
4. **Update Dashboard**: Streamlit dashboard calls MCP instead of agents directly
5. **Test End-to-End**: Run full workflow with multiple agents

## Future Enhancements

- Async agent invocation (non-blocking)
- Message broker integration (Kafka/RabbitMQ for async tasks)
- Cost-based agent selection (optimize for latency vs. cost)
- Multi-tenant isolation and billing
- A/B testing of routing policies
- Real LLM-based intent classification (GPT, Claude)
- Agent auto-discovery (agents register themselves)
- Circuit breaker for failing agents
- Request prioritization and queuing
