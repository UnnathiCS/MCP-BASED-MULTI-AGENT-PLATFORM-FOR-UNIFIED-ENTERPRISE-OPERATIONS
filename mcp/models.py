"""
Data models for MCP Decision Engine.

Defines request/response shapes, agent registry, execution plans, and policies.
"""

from typing import Optional, List, Dict, Any, Literal
from dataclasses import dataclass, asdict, field
from datetime import datetime
import uuid
import json


@dataclass
class MCPRequest:
    """User request to MCP for processing."""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    attachments: List[Dict[str, str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    intent_hints: List[str] = field(default_factory=list)
    priority: Literal["low", "normal", "high", "critical"] = "normal"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "MCPRequest":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class IntentMatch:
    """Represents a detected intent with confidence and rationale."""
    name: str
    confidence: float
    method: Literal["rule", "model", "semantic"] = "model"
    rationale: str = ""
    supporting_tokens: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CapabilityScore:
    """Scoring breakdown for a candidate agent."""
    agent_id: str
    intent_match: float = 0.0
    capability_match: float = 0.0
    health_score: float = 1.0
    policy_score: float = 1.0
    cost_score: float = 1.0
    priority_boost: float = 0.0
    overall_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Capability:
    """An agent's declared capability."""
    action: str
    description: str
    sample_inputs: List[str] = field(default_factory=list)
    required_fields: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if d.get("embedding") and isinstance(d["embedding"], list) and len(d["embedding"]) > 100:
            d["embedding"] = f"[embedding len={len(d['embedding'])}]"
        return d


@dataclass
class AgentRecord:
    """Registry entry for an agent."""
    agent_id: str
    name: str
    endpoint: str
    capabilities: List[Capability] = field(default_factory=list)
    allowed_tenants: List[str] = field(default_factory=lambda: ["*"])
    status: Literal["discovered", "registered", "degraded", "offline"] = "registered"
    sla: Dict[str, Any] = field(default_factory=lambda: {"timeout_ms": 30000, "concurrency_limit": 10})
    health_check_path: str = "/health"
    auth: Dict[str, str] = field(default_factory=dict)
    priority: int = 50
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_healthcheck: str = ""
    error_count: int = 0
    success_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AgentRecord":
        d["capabilities"] = [Capability(**c) if isinstance(c, dict) else c for c in d.get("capabilities", [])]
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class ExecutionTask:
    """A single task in an execution plan."""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    action: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    priority: Literal["low", "normal", "high"] = "normal"
    timeout_ms: int = 30000
    idempotency_key: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutionPlan:
    """Execution plan for one or more agents."""
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    mode: Literal["sync", "async", "pipeline"] = "sync"
    tasks: List[ExecutionTask] = field(default_factory=list)
    requires_approval: bool = False
    estimated_cost: float = 0.0
    estimated_duration_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MCPDecision:
    """MCP's decision about which agent(s) to invoke."""
    request_id: str
    intent: str
    confidence: float
    selected_agents: List[Dict[str, Any]] = field(default_factory=list)
    plan: ExecutionPlan = field(default_factory=ExecutionPlan)
    fallback_agents: List[str] = field(default_factory=list)
    confidence_sufficient: bool = True
    reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["plan"] = self.plan.to_dict() if self.plan else {}
        return d


@dataclass
class AgentInvocation:
    """Request sent to an agent from MCP."""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = ""
    user_id: str = ""
    mcp_meta: Dict[str, Any] = field(default_factory=dict)
    payload: Dict[str, Any] = field(default_factory=dict)
    idempotency_key: str = ""
    timeout_ms: int = 30000

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentResponse:
    """Response from an agent."""
    request_id: str
    agent_id: str
    status: Literal["ok", "error", "timeout"]
    result: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    suggested_actions: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AgentResponse":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class MCPResponse:
    """Final response from MCP to the caller."""
    request_id: str
    status: Literal["ok", "error", "partial", "degraded"]
    mcp_decision: MCPDecision = field(default_factory=MCPDecision)
    result: Dict[str, Any] = field(default_factory=dict)
    selected_agents: List[str] = field(default_factory=list)
    agent_responses: List[AgentResponse] = field(default_factory=list)
    audit: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "status": self.status,
            "mcp_decision": self.mcp_decision.to_dict(),
            "result": self.result,
            "selected_agents": self.selected_agents,
            "agent_responses": [r.to_dict() for r in self.agent_responses],
            "audit": self.audit,
            "error": self.error,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class PolicyRule:
    """A policy rule that constrains routing and execution."""
    rule_id: str
    name: str
    condition: Dict[str, Any]  # e.g. {"request_priority": "high"}
    allowed_agents: List[str] = field(default_factory=list)
    blocked_agents: List[str] = field(default_factory=list)
    requires_approval: bool = False
    data_handling: Dict[str, str] = field(default_factory=dict)  # e.g. {"mask_fields": ["ssn", "credit_card"]}
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
