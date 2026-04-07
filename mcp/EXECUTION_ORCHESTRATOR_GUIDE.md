# MCP Execution Orchestrator: Complete Architecture Guide

## Overview

The **MCP Execution Orchestrator** is the critical execution layer that takes decision output from the MCP Decision Engine and orchestrates actual agent invocations. It handles:

- **Multiple Execution Modes**: Sync (single agent), Async (parallel), Pipeline (sequential with data flow)
- **Error Handling & Retries**: Exponential backoff, transient failure detection, configurable retry policies
- **Distributed Tracing**: Full request tracking across agents with audit trails
- **Performance Metrics**: Per-task timing, success rates, retry counts
- **Graceful Degradation**: Partial success handling, fallback strategies

## Architecture

### Core Components

#### 1. **ExecutionOrchestrator**
Main orchestration engine that takes ExecutionPlans and executes them.

```python
orchestrator = MCPExecutionOrchestrator(
    config=ExecutionConfig(
        request_timeout_ms=30000,
        max_retries=3,
        retry_backoff_ms=1000,
        max_parallel_tasks=10,
    )
)

# Execute a plan
response = orchestrator.execute_plan(decision, registry)
```

#### 2. **ExecutionConfig**
Configures orchestrator behavior:

```python
config = ExecutionConfig(
    request_timeout_ms=30000,      # Timeout per agent invocation
    max_retries=3,                 # Max retry attempts
    retry_backoff_ms=1000,         # Initial backoff (exponential)
    max_parallel_tasks=10,         # Max concurrent agents
    enable_distributed_tracing=True # Trace across systems
)
```

#### 3. **ExecutionMetrics**
Tracks execution performance:

```python
metrics = {
    "duration_ms": 3245,           # Total execution time
    "total_tasks": 5,
    "succeeded": 4,
    "failed": 1,
    "retried": 2,
    "success_rate": 0.8,
    "task_metrics": {
        "task-1": {
            "status": "success",
            "duration_ms": 245,
            "retry_count": 0,
        },
        ...
    }
}
```

#### 4. **TaskResult**
Per-task execution result:

```python
result = TaskResult(
    task_id="task-1",
    agent_id="document-reviewer",
    status="success",              # success|error|timeout|retry
    result={"risks": ["..."]},     # Agent response
    error="",
    duration_ms=245,
    retry_count=0,
)
```

## Execution Modes

### 1. Synchronous (SYNC)

**Characteristics:**
- Single agent, blocking invocation
- Simplest execution mode
- Stop on error

**When to use:**
- Single-agent requests
- Real-time user interactions
- Simple workflows

**Example:**
```python
plan = ExecutionPlan(
    mode="sync",
    tasks=[
        ExecutionTask(
            task_id="task-1",
            agent_id="document-reviewer",
            action="document.review",
            payload={"document_id": "doc-123"},
        )
    ]
)
```

**Execution flow:**
```
Start → Task 1 (blocking) → End
```

### 2. Asynchronous (ASYNC)

**Characteristics:**
- Multiple agents in parallel
- No data dependencies
- Wait for all to complete
- Maximum throughput

**When to use:**
- Multi-agent analysis
- Independent tasks
- Maximize speed

**Example:**
```python
plan = ExecutionPlan(
    mode="async",
    tasks=[
        ExecutionTask(task_id="task-1", agent_id="agent-1", ...),
        ExecutionTask(task_id="task-2", agent_id="agent-2", ...),
        ExecutionTask(task_id="task-3", agent_id="agent-3", ...),
    ]
)
```

**Execution flow:**
```
Start → Task 1 ──┐
        Task 2 ──┼→ Wait All → End
        Task 3 ──┘
```

### 3. Pipeline (PIPELINE)

**Characteristics:**
- Sequential execution with data flow
- Each task uses previous task's output
- Stop on error
- Refinement workflows

**When to use:**
- Multi-stage processing
- Each stage refines input
- Data transformation pipelines

**Example:**
```python
plan = ExecutionPlan(
    mode="pipeline",
    tasks=[
        ExecutionTask(
            task_id="stage-1",
            agent_id="document-reviewer",
            action="document.review",
            payload={"document": "..."},
        ),
        ExecutionTask(
            task_id="stage-2",
            agent_id="analytics-agent",
            action="analytics.report",
            depends_on=["stage-1"],
            payload={"analysis_type": "summary"},
        ),
    ]
)
```

**Execution flow:**
```
Start → Task 1 → (extract output) → Task 2 → End
         [output injected as _pipeline_input in Task 2]
```

## Error Handling & Retry Logic

### Retry Strategy

The orchestrator automatically retries on **transient failures**:

**Retried (Transient):**
- Connection errors (cannot reach agent)
- Timeouts (agent slow/unresponsive)
- 5xx errors (server errors, temporary)

**Not Retried (Permanent):**
- 4xx errors (client/input errors, won't change)
- Invalid payloads
- Missing agents

### Exponential Backoff

```
Attempt 1: Immediate
Attempt 2: backoff_ms * 2^1 = 1000 * 2 = 2s
Attempt 3: backoff_ms * 2^2 = 1000 * 4 = 4s
Attempt 4: backoff_ms * 2^3 = 1000 * 8 = 8s
(max 60s)
```

**Configuration:**
```python
config = ExecutionConfig(
    max_retries=3,           # Max attempts
    retry_backoff_ms=1000,   # Initial delay
)
```

**Example trace:**
```
Task: task-1
Attempt 1: Failed (connection error)
  ↓ Wait 1000ms
Attempt 2: Failed (timeout)
  ↓ Wait 2000ms
Attempt 3: Failed (5xx error)
  ↓ Wait 4000ms
Attempt 4: SUCCESS ✓
Final: Succeeded after 3 retries, 7000ms total backoff
```

## Agent Invocation Contract

### Request Format

```python
{
    "request_id": "uuid-xxx",
    "trace_id": "trace-xyz",
    "user_id": "system",
    "mcp_meta": {
        "agent_id": "document-reviewer",
        "action": "document.review",
    },
    "payload": {
        "document_id": "doc-123",
        "document_text": "...",
    },
    "idempotency_key": "task-1-uuid",
    "timeout_ms": 30000,
}
```

### Response Format

```python
{
    "request_id": "uuid-xxx",
    "agent_id": "document-reviewer",
    "status": "ok",
    "result": {
        "risks": ["ambiguous_clause"],
        "confidence": 0.95,
        "recommendations": [...]
    },
    "error": None,
    "suggested_actions": [
        {"action": "review_clause", "priority": "high"}
    ]
}
```

## Distributed Tracing

Every execution generates a **trace_id** for cross-system tracking:

```
User Request
  ↓
trace-id: trace-abc123
  ↓
MCP Decision Engine
  ├─ Creates ExecutionPlan
  └─ trace_id: trace-abc123
  ↓
Execution Orchestrator
  ├─ Task 1: invocation_id-1 (includes trace-abc123)
  ├─ Task 2: invocation_id-2 (includes trace-abc123)
  └─ trace_id: trace-abc123
  ↓
Agent Logs (searchable by trace-abc123)
  ├─ [trace-abc123] Processing document...
  ├─ [trace-abc123] Identified 3 risks...
  └─ [trace-abc123] Response sent

Dashboard
  └─ Can reconstruct full flow with single trace-id
```

**Usage:**
```python
# In logs
logger.info(f"[{trace_id}] Processing task {task_id}")

# In monitoring
metrics.find_by_trace(trace_id)

# In dashboards
timeline = trace_service.get_timeline(trace_id)
```

## Integration Pattern

### With Decision Engine

```python
from mcp.decision_engine import MCPDecisionEngine
from mcp.execution_orchestrator import MCPExecutionOrchestrator
from mcp.agent_registry_api import AgentRegistrationAPI

# Initialize
registry = AgentRegistrationAPI()
decision_engine = MCPDecisionEngine(registry)
orchestrator = MCPExecutionOrchestrator()

# Process request
request = MCPRequest(text="Review this document...")

# Get decision
decision = decision_engine.decide(request)

# Execute plan
response = orchestrator.execute_plan(decision, registry)

# Return to user
return response
```

### With FastAPI

```python
from fastapi import FastAPI
from mcp.execution_orchestrator import MCPExecutionOrchestrator

app = FastAPI()
orchestrator = MCPExecutionOrchestrator()

@app.post("/mcp/route")
async def route_request(request: MCPRequest):
    # Decision phase (by decision engine)
    decision = decision_engine.decide(request)
    
    # Execution phase
    response = orchestrator.execute_plan(decision, registry)
    
    return response.to_dict()

@app.get("/execution/trace/{trace_id}")
async def get_trace(trace_id: str):
    """Retrieve execution trace for debugging."""
    return traces[trace_id]
```

## Performance Characteristics

### Throughput

**Sync Mode:**
- Sequential: Limited by slowest agent
- Example: 3 agents × 100ms = 300ms total

**Async Mode:**
- Parallel: Limited by slowest agent
- Example: 3 agents × 100ms = 100ms total (3x speedup)

**Pipeline Mode:**
- Sequential but with data flow
- Example: 3 agents × 100ms = 300ms total
- But output flows through stages

### Latency

```
Sync:     ████████░ (3 agents, 100ms each)
Async:    ████░░░░░ (3 agents parallel, 100ms max)
Pipeline: ████████░ (3 agents sequential, 100ms each)
```

### Resource Usage

**Thread Pool:**
- Default: 10 concurrent tasks max
- Can be configured per ExecutionConfig
- Prevents overwhelming system

**Memory:**
- Per-task: ~5KB (metadata + result)
- Thread overhead: ~2MB per thread
- Typical: <50MB for 100 concurrent tasks

## Production Deployment

### 1. Configuration

```python
config = ExecutionConfig(
    request_timeout_ms=30000,      # 30s per agent
    max_retries=3,                 # Retry up to 3 times
    retry_backoff_ms=2000,         # Start with 2s backoff
    max_parallel_tasks=20,         # Max 20 concurrent
)

orchestrator = MCPExecutionOrchestrator(config)
```

### 2. Monitoring

```python
# Track metrics
response = orchestrator.execute_plan(decision, registry)
metrics = response.audit['metrics']

# Log to monitoring system
monitoring.record_execution(
    trace_id=response.audit['trace_id'],
    duration_ms=metrics['duration_ms'],
    success_rate=metrics['success_rate'],
    failed_tasks=metrics['failed'],
)

# Alert on issues
if metrics['failed'] > 0:
    alerting.send(
        level="warning",
        message=f"Execution {trace_id} had {metrics['failed']} failures"
    )
```

### 3. Scaling

**Vertical Scaling:**
```python
# Increase timeouts for slower agents
config.request_timeout_ms = 60000

# More retries for unreliable infrastructure
config.max_retries = 5
```

**Horizontal Scaling:**
```python
# Multiple orchestrator instances
orchestrators = [
    MCPExecutionOrchestrator(config)
    for _ in range(4)
]

# Load balance requests
for request in requests:
    orchestrator = orchestrators[hash(request.id) % 4]
    response = orchestrator.execute_plan(decision, registry)
```

## Code Examples

### Example 1: Simple Document Review

```python
# Create execution plan
plan = ExecutionPlan(
    mode="sync",
    tasks=[
        ExecutionTask(
            task_id="review",
            agent_id="document-reviewer",
            action="document.review",
            payload={
                "document_id": "contract-2024",
                "review_type": "legal",
            }
        )
    ]
)

# Execute
response = orchestrator.execute_plan(decision, registry)

# Check result
if response.status == "ok":
    risks = response.result['task_results'][0]['result']['risks']
    print(f"Found {len(risks)} risks")
```

### Example 2: Parallel Multi-Agent Analysis

```python
plan = ExecutionPlan(
    mode="async",
    tasks=[
        ExecutionTask(
            task_id="doc-review",
            agent_id="document-reviewer",
            action="document.review",
            payload={"document_id": "doc-1"},
        ),
        ExecutionTask(
            task_id="support-check",
            agent_id="support-agent",
            action="it.support.text",
            payload={"query": "support requirements"},
        ),
        ExecutionTask(
            task_id="analytics",
            agent_id="analytics-agent",
            action="analytics.report",
            payload={"report_type": "summary"},
        ),
    ]
)

response = orchestrator.execute_plan(decision, registry)

# All 3 execute in parallel
# Total time ≈ max(task1, task2, task3) not sum
```

### Example 3: Multi-Stage Pipeline

```python
plan = ExecutionPlan(
    mode="pipeline",
    tasks=[
        ExecutionTask(
            task_id="extract",
            agent_id="document-reviewer",
            action="document.analyze",
            payload={"document_id": "doc-1"},
        ),
        ExecutionTask(
            task_id="summarize",
            agent_id="analytics-agent",
            action="analytics.summarize",
            depends_on=["extract"],
            payload={"summary_length": "brief"},
        ),
        ExecutionTask(
            task_id="classify",
            agent_id="analytics-agent",
            action="analytics.classify",
            depends_on=["summarize"],
            payload={"categories": ["risk", "importance"]},
        ),
    ]
)

response = orchestrator.execute_plan(decision, registry)

# Stage 1 extracts document
# Stage 2 uses Stage 1 output to summarize
# Stage 3 uses Stage 2 output to classify
```

## Troubleshooting

### Issue: All tasks failing with connection errors

**Cause:** Agents not running or wrong endpoints

**Fix:**
```python
# Verify agent endpoints
for agent_id in decision.selected_agents:
    agent = registry.get_agent(agent_id)
    print(f"{agent.name}: {agent.endpoint}")

# Test connectivity
requests.get(f"{agent.endpoint}/health", timeout=5)

# Check logs
tail -f agent.log | grep "trace-xyz"
```

### Issue: Tasks timing out

**Cause:** Agents too slow or network latency

**Fix:**
```python
# Increase timeout
config.request_timeout_ms = 60000

# Check agent performance
response.audit['metrics']['task_metrics']
```

### Issue: Too many retries

**Cause:** Transient failures or unreliable agents

**Fix:**
```python
# Reduce retry backoff for faster recovery
config.retry_backoff_ms = 500

# Monitor retry patterns
retries = sum(
    m.get('retry_count', 0)
    for m in metrics['task_metrics'].values()
)
```

## API Reference

### MCPExecutionOrchestrator

```python
class MCPExecutionOrchestrator:
    def __init__(config: ExecutionConfig = None)
    def execute_plan(decision: MCPDecision, registry: Any) -> MCPResponse
```

### ExecutionConfig

```python
@dataclass
class ExecutionConfig:
    request_timeout_ms: int = 30000
    max_retries: int = 3
    retry_backoff_ms: int = 1000
    max_parallel_tasks: int = 10
    enable_distributed_tracing: bool = True
```

### ExecutionMetrics

```python
@dataclass
class ExecutionMetrics:
    duration_ms: int
    total_tasks: int
    succeeded: int
    failed: int
    retried: int
    success_rate: float
    task_metrics: Dict[str, Dict]
```

## Next Steps

1. **Integration**: Wire orchestrator into decision_engine
2. **Monitoring**: Build dashboard for execution metrics
3. **Testing**: Load test with multiple concurrent requests
4. **Optimization**: Profile slow agents and optimize
5. **Scaling**: Deploy multiple orchestrators with load balancing

