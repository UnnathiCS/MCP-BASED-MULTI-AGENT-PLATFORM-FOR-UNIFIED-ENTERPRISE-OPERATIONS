"""
Context-Aware Decision Making Module for MCP.

This module provides context aggregation and enrichment for intelligent decision-making:
- User history and profile
- Workflow state and session context
- External data sources (finance, contracts, policies)
- Cross-agent coordination

Context flows:
1. Collect context from multiple sources
2. Enrich MCP request with contextual data
3. Score decisions based on context
4. Route to most appropriate agent
5. Update context after agent execution

Example: Refund Request
- Detect intent: "process refund"
- Gather context: user history, purchase record, contract terms, finance policies
- Evaluate: customer lifetime value, transaction integrity, policy compliance
- Route: escalate to finance agent with full context if needed
- Update: record decision in user history for future reference
"""

import logging
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class ContextSourceType(Enum):
    """Types of context sources."""
    USER_PROFILE = "user_profile"
    USER_HISTORY = "user_history"
    WORKFLOW_STATE = "workflow_state"
    EXTERNAL_DATA = "external_data"
    AGENT_RESPONSE = "agent_response"
    SYSTEM_STATE = "system_state"


@dataclass
class UserHistoryRecord:
    """Historical record of user interactions."""
    timestamp: str
    request_type: str
    agent_id: str
    status: str  # "success", "failure", "escalated"
    duration_ms: int
    cost: float = 0.0
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class UserProfile:
    """User profile with aggregate metrics."""
    user_id: str
    created_at: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    escalated_requests: int = 0
    total_cost: float = 0.0
    avg_resolution_time_ms: float = 0.0
    preferred_agents: List[str] = field(default_factory=list)
    risk_level: str = "normal"  # "low", "normal", "high"
    trust_score: float = 0.5  # 0-1
    is_vip: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def compute_trust_score(self) -> float:
        """Compute trust score based on history."""
        if self.total_requests == 0:
            return 0.5  # neutral

        success_rate = self.successful_requests / self.total_requests
        escalation_rate = self.escalated_requests / self.total_requests
        
        # Trust = success_rate - (escalation_rate * 0.3)
        trust = success_rate - (escalation_rate * 0.3)
        return max(0.0, min(1.0, trust))


@dataclass
class WorkflowContext:
    """Current workflow state and session context."""
    workflow_id: str
    step_index: int
    total_steps: int
    current_agent: str = ""
    previous_agents: List[str] = field(default_factory=list)
    payload_hash: str = ""  # Hash of current payload for cycle detection
    variables: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExternalDataReference:
    """Reference to external data needed for decision-making."""
    source: str  # e.g., "finance_system", "contract_db", "compliance_engine"
    entity_type: str  # e.g., "transaction", "contract", "policy"
    entity_id: str
    required_fields: List[str] = field(default_factory=list)
    cached_data: Dict[str, Any] = field(default_factory=dict)
    cached_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DecisionContext:
    """Aggregated context for decision-making."""
    request_id: str
    user_id: str
    user_profile: Optional[UserProfile] = None
    user_history: List[UserHistoryRecord] = field(default_factory=list)
    workflow_context: Optional[WorkflowContext] = None
    external_data: Dict[str, ExternalDataReference] = field(default_factory=dict)
    system_state: Dict[str, Any] = field(default_factory=dict)
    enriched_metadata: Dict[str, Any] = field(default_factory=dict)
    confidence_factors: Dict[str, float] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # Serialize nested objects
        if self.user_profile:
            data['user_profile'] = self.user_profile.to_dict()
        if self.user_history:
            data['user_history'] = [h.to_dict() for h in self.user_history]
        if self.workflow_context:
            data['workflow_context'] = self.workflow_context.to_dict()
        if self.external_data:
            data['external_data'] = {k: v.to_dict() for k, v in self.external_data.items()}
        return data


# ============================================================================
# Context Provider Interface
# ============================================================================

class ContextProvider:
    """Base class for context providers."""

    def can_provide(self, source_type: ContextSourceType, request_data: Dict[str, Any]) -> bool:
        """Check if this provider can provide context for the given source."""
        raise NotImplementedError

    def fetch_context(self, source_type: ContextSourceType, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch context from source."""
        raise NotImplementedError


class UserProfileProvider(ContextProvider):
    """Provides user profile context."""

    def __init__(self, user_store: Optional[Dict[str, UserProfile]] = None):
        self.user_store = user_store or {}

    def can_provide(self, source_type: ContextSourceType, request_data: Dict[str, Any]) -> bool:
        return source_type == ContextSourceType.USER_PROFILE

    def fetch_context(self, source_type: ContextSourceType, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch or create user profile."""
        user_id = request_data.get("user_id")
        if not user_id:
            return {}

        if user_id not in self.user_store:
            self.user_store[user_id] = UserProfile(
                user_id=user_id,
                created_at=datetime.utcnow().isoformat()
            )

        profile = self.user_store[user_id]
        profile.trust_score = profile.compute_trust_score()
        return {"user_profile": profile}

    def update_profile(self, user_id: str, history_record: UserHistoryRecord) -> None:
        """Update user profile with new history record."""
        if user_id not in self.user_store:
            self.user_store[user_id] = UserProfile(
                user_id=user_id,
                created_at=datetime.utcnow().isoformat()
            )

        profile = self.user_store[user_id]
        profile.total_requests += 1
        
        if history_record.status == "success":
            profile.successful_requests += 1
        elif history_record.status == "failure":
            profile.failed_requests += 1
        elif history_record.status == "escalated":
            profile.escalated_requests += 1

        profile.total_cost += history_record.cost
        
        # Update average resolution time
        if profile.avg_resolution_time_ms == 0.0:
            profile.avg_resolution_time_ms = history_record.duration_ms
        else:
            profile.avg_resolution_time_ms = (
                (profile.avg_resolution_time_ms * (profile.total_requests - 1) + history_record.duration_ms)
                / profile.total_requests
            )

        # Track preferred agents
        if history_record.status == "success" and history_record.agent_id not in profile.preferred_agents:
            profile.preferred_agents.append(history_record.agent_id)

        profile.trust_score = profile.compute_trust_score()


class UserHistoryProvider(ContextProvider):
    """Provides user history context."""

    def __init__(self, history_store: Optional[Dict[str, List[UserHistoryRecord]]] = None):
        self.history_store = history_store or {}

    def can_provide(self, source_type: ContextSourceType, request_data: Dict[str, Any]) -> bool:
        return source_type == ContextSourceType.USER_HISTORY

    def fetch_context(self, source_type: ContextSourceType, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch user history, with optional time window."""
        user_id = request_data.get("user_id")
        days_back = request_data.get("days_back", 30)
        request_types = request_data.get("request_types", None)  # Filter by type if provided

        if user_id not in self.history_store:
            return {"user_history": []}

        all_history = self.history_store[user_id]
        
        # Filter by date
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        filtered = [
            h for h in all_history
            if datetime.fromisoformat(h.timestamp) >= cutoff_date
        ]

        # Filter by type
        if request_types:
            filtered = [h for h in filtered if h.request_type in request_types]

        return {"user_history": filtered}

    def add_record(self, user_id: str, record: UserHistoryRecord) -> None:
        """Add a history record for user."""
        if user_id not in self.history_store:
            self.history_store[user_id] = []
        self.history_store[user_id].append(record)

    def get_summary(self, user_id: str, days_back: int = 30) -> Dict[str, Any]:
        """Get summary statistics for user history."""
        history = self.fetch_context(
            ContextSourceType.USER_HISTORY,
            {"user_id": user_id, "days_back": days_back}
        ).get("user_history", [])

        if not history:
            return {}

        return {
            "total_requests": len(history),
            "successful": sum(1 for h in history if h.status == "success"),
            "failed": sum(1 for h in history if h.status == "failure"),
            "escalated": sum(1 for h in history if h.status == "escalated"),
            "total_cost": sum(h.cost for h in history),
            "avg_duration_ms": sum(h.duration_ms for h in history) / len(history) if history else 0,
            "request_types": list(set(h.request_type for h in history)),
            "agents_used": list(set(h.agent_id for h in history)),
        }


class WorkflowContextProvider(ContextProvider):
    """Provides workflow state and session context."""

    def __init__(self, workflow_store: Optional[Dict[str, WorkflowContext]] = None):
        self.workflow_store = workflow_store or {}

    def can_provide(self, source_type: ContextSourceType, request_data: Dict[str, Any]) -> bool:
        return source_type == ContextSourceType.WORKFLOW_STATE

    def fetch_context(self, source_type: ContextSourceType, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch current workflow context."""
        workflow_id = request_data.get("workflow_id")
        session_id = request_data.get("session_id")

        # Try workflow_id first, then session_id
        context = None
        if workflow_id and workflow_id in self.workflow_store:
            context = self.workflow_store[workflow_id]
        elif session_id and session_id in self.workflow_store:
            context = self.workflow_store[session_id]

        return {"workflow_context": context}

    def create_workflow(self, workflow_id: str, total_steps: int) -> WorkflowContext:
        """Create a new workflow context."""
        context = WorkflowContext(
            workflow_id=workflow_id,
            step_index=0,
            total_steps=total_steps
        )
        self.workflow_store[workflow_id] = context
        return context

    def update_workflow(self, workflow_id: str, agent_id: str, payload: Dict[str, Any]) -> WorkflowContext:
        """Update workflow with next step."""
        if workflow_id not in self.workflow_store:
            raise ValueError(f"Workflow {workflow_id} not found")

        context = self.workflow_store[workflow_id]
        context.current_agent = agent_id
        if agent_id not in context.previous_agents:
            context.previous_agents.append(agent_id)
        context.step_index += 1
        context.payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        context.updated_at = datetime.utcnow().isoformat()
        return context


class ExternalDataProvider(ContextProvider):
    """Provides external data (finance, contracts, policies)."""

    def __init__(self, data_fetchers: Optional[Dict[str, Callable]] = None):
        self.data_fetchers = data_fetchers or {}

    def can_provide(self, source_type: ContextSourceType, request_data: Dict[str, Any]) -> bool:
        return source_type == ContextSourceType.EXTERNAL_DATA

    def register_fetcher(self, source_name: str, fetcher: Callable) -> None:
        """Register a data fetcher for a source."""
        self.data_fetchers[source_name] = fetcher
        logger.info(f"Registered data fetcher for: {source_name}")

    def fetch_context(self, source_type: ContextSourceType, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch external data based on references in request."""
        references = request_data.get("external_data_refs", [])
        external_data = {}

        for ref in references:
            source = ref.get("source")
            entity_type = ref.get("entity_type")
            entity_id = ref.get("entity_id")

            if source not in self.data_fetchers:
                logger.warning(f"No fetcher registered for source: {source}")
                continue

            try:
                fetcher = self.data_fetchers[source]
                data = fetcher(entity_type, entity_id)
                
                ref_obj = ExternalDataReference(
                    source=source,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    cached_data=data,
                    cached_at=datetime.utcnow().isoformat()
                )
                external_data[f"{source}_{entity_type}_{entity_id}"] = ref_obj
            except Exception as e:
                logger.error(f"Error fetching {source}/{entity_type}/{entity_id}: {e}")

        return {"external_data": external_data}


# ============================================================================
# Context-Aware Decision Handler
# ============================================================================

class ContextAwareDecisionHandler:
    """
    Main handler for context-aware decision making.
    
    Coordinates multiple context providers and uses aggregated context
    for intelligent routing decisions.
    """

    def __init__(self):
        self.providers: Dict[ContextSourceType, ContextProvider] = {}
        self.decision_rules: List[Callable] = []
        self.context_enrichers: List[Callable] = []

    def register_provider(self, source_type: ContextSourceType, provider: ContextProvider) -> None:
        """Register a context provider."""
        self.providers[source_type] = provider
        logger.info(f"Registered context provider: {source_type.value}")

    def register_decision_rule(self, rule: Callable) -> None:
        """Register a decision rule that uses context."""
        self.decision_rules.append(rule)

    def register_enricher(self, enricher: Callable) -> None:
        """Register a context enricher function."""
        self.context_enrichers.append(enricher)

    def gather_context(self, request_data: Dict[str, Any]) -> DecisionContext:
        """
        Gather context from all registered providers.
        
        Returns aggregated DecisionContext object.
        """
        request_id = request_data.get("request_id", "unknown")
        user_id = request_data.get("user_id", "unknown")

        context = DecisionContext(
            request_id=request_id,
            user_id=user_id
        )

        # Fetch context from all available providers
        for source_type, provider in self.providers.items():
            if provider.can_provide(source_type, request_data):
                try:
                    source_context = provider.fetch_context(source_type, request_data)
                    
                    if source_type == ContextSourceType.USER_PROFILE:
                        context.user_profile = source_context.get("user_profile")
                    elif source_type == ContextSourceType.USER_HISTORY:
                        context.user_history = source_context.get("user_history", [])
                    elif source_type == ContextSourceType.WORKFLOW_STATE:
                        context.workflow_context = source_context.get("workflow_context")
                    elif source_type == ContextSourceType.EXTERNAL_DATA:
                        context.external_data = source_context.get("external_data", {})
                    elif source_type == ContextSourceType.SYSTEM_STATE:
                        context.system_state = source_context.get("system_state", {})
                except Exception as e:
                    logger.error(f"Error gathering {source_type.value}: {e}")
                    context.warnings.append(f"Failed to gather {source_type.value}: {e}")

        return context

    def enrich_context(self, context: DecisionContext) -> DecisionContext:
        """Apply context enrichers to enrich decision context."""
        for enricher in self.context_enrichers:
            try:
                context = enricher(context)
            except Exception as e:
                logger.error(f"Error in context enricher: {e}")
                context.warnings.append(f"Enricher error: {e}")

        return context

    def evaluate_decision_rules(self, context: DecisionContext, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate all registered decision rules using context.
        
        Returns a decision outcome with routing recommendations.
        """
        decisions = {
            "rules_evaluated": 0,
            "matching_rules": [],
            "routing_recommendations": [],
            "risk_level": "normal",
            "escalation_needed": False,
            "context_confidence": 0.5
        }

        for rule in self.decision_rules:
            try:
                result = rule(context, request_data)
                if result and result.get("matched", False):
                    decisions["matching_rules"].append(result)
                    decisions["rules_evaluated"] += 1
            except Exception as e:
                logger.error(f"Error evaluating rule: {e}")

        # Aggregate recommendations
        if decisions["matching_rules"]:
            decisions["context_confidence"] = min(
                1.0,
                sum(r.get("confidence", 0.5) for r in decisions["matching_rules"]) / len(decisions["matching_rules"])
            )
            
            # Determine risk level from matching rules
            risk_levels = [r.get("risk_level", "normal") for r in decisions["matching_rules"]]
            if "high" in risk_levels:
                decisions["risk_level"] = "high"
            elif "medium" in risk_levels:
                decisions["risk_level"] = "medium"

            # Check if escalation needed
            decisions["escalation_needed"] = any(r.get("escalate", False) for r in decisions["matching_rules"])

            # Collect routing recommendations
            for rule_result in decisions["matching_rules"]:
                if "recommended_agent" in rule_result:
                    decisions["routing_recommendations"].append({
                        "agent": rule_result["recommended_agent"],
                        "reason": rule_result.get("reason", "Rule matched"),
                        "confidence": rule_result.get("confidence", 0.5)
                    })

        return decisions

    def make_context_aware_decision(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point: gather context and make intelligent decision.
        
        Returns decision with context, recommendations, and routing info.
        """
        logger.info(f"Making context-aware decision for request {request_data.get('request_id')}")

        # Step 1: Gather context
        context = self.gather_context(request_data)
        
        # Step 2: Enrich context
        context = self.enrich_context(context)

        # Step 3: Evaluate decision rules
        decision = self.evaluate_decision_rules(context, request_data)

        # Step 4: Build decision response
        response = {
            "request_id": request_data.get("request_id"),
            "context": context.to_dict(),
            "decision": decision,
            "timestamp": datetime.utcnow().isoformat()
        }

        logger.info(f"Decision made: risk_level={decision['risk_level']}, escalation_needed={decision['escalation_needed']}")

        return response


# ============================================================================
# Common Decision Rules
# ============================================================================

def create_refund_decision_rule(
    finance_threshold: float = 100.0,
    vip_auto_approve: bool = True
) -> Callable:
    """
    Create a decision rule for refund requests.
    
    Checks: customer history, transaction amount, policies, VIP status
    """
    def rule(context: DecisionContext, request_data: Dict[str, Any]) -> Dict[str, Any]:
        request_type = request_data.get("request_type", "").lower()
        
        if "refund" not in request_type:
            return None

        result = {
            "matched": True,
            "confidence": 0.0,
            "risk_level": "normal",
            "escalate": False,
            "reason": ""
        }

        # Get transaction amount
        amount = request_data.get("transaction_amount", 0.0)
        
        # Check user profile
        if context.user_profile:
            profile = context.user_profile
            
            # VIP gets auto-approval on small refunds
            if profile.is_vip and amount <= finance_threshold:
                result["confidence"] = 0.95
                result["recommended_agent"] = "finance-agent"
                result["reason"] = f"VIP auto-approval (amount: ${amount})"
                return result

            # High trust users get faster approval
            if profile.trust_score > 0.8:
                result["confidence"] = 0.85
                result["recommended_agent"] = "finance-agent"
                result["reason"] = f"High-trust user (score: {profile.trust_score:.2f})"
                return result

        # Large refunds need escalation
        if amount > finance_threshold:
            result["escalate"] = True
            result["risk_level"] = "high"
            result["reason"] = f"Large refund amount: ${amount}"
            if context.external_data:
                result["recommended_agent"] = "escalation-manager"
            return result

        # Default: standard processing
        result["confidence"] = 0.7
        result["recommended_agent"] = "finance-agent"
        result["reason"] = "Standard refund processing"
        return result

    return rule


def create_contract_review_rule() -> Callable:
    """
    Create a decision rule for contract reviews.
    
    Routes based on contract type, complexity, and user authority.
    """
    def rule(context: DecisionContext, request_data: Dict[str, Any]) -> Dict[str, Any]:
        request_type = request_data.get("request_type", "").lower()
        
        if "contract" not in request_type or "review" not in request_type:
            return None

        result = {
            "matched": True,
            "confidence": 0.7,
            "risk_level": "normal",
            "escalate": False,
            "reason": ""
        }

        contract_type = request_data.get("contract_type", "standard")
        contract_value = request_data.get("contract_value", 0.0)

        # Check external data for contract terms
        contract_data = None
        for ref_key, ref in context.external_data.items():
            if "contract" in ref_key:
                contract_data = ref.cached_data
                break

        # High-value contracts need escalation
        if contract_value > 100000:
            result["escalate"] = True
            result["risk_level"] = "high"
            result["recommended_agent"] = "legal-team"
            result["reason"] = f"High-value contract: ${contract_value}"
            return result

        # Complex contract types
        complex_types = ["nda", "partnership", "licensing"]
        if contract_type.lower() in complex_types:
            result["recommended_agent"] = "legal-agent"
            result["reason"] = f"Complex contract type: {contract_type}"
            return result

        # Standard contract
        result["recommended_agent"] = "document-review-agent"
        result["reason"] = "Standard contract review"
        return result

    return rule


def create_anomaly_detection_rule() -> Callable:
    """
    Create a decision rule that detects anomalies in user behavior.
    
    Flags unusual patterns compared to user history.
    """
    def rule(context: DecisionContext, request_data: Dict[str, Any]) -> Dict[str, Any]:
        if not context.user_history or not context.user_profile:
            return None

        result = {
            "matched": False,
            "confidence": 0.0,
            "risk_level": "normal",
            "escalate": False,
            "reason": ""
        }

        # Check for unusual activity patterns
        recent_requests = context.user_history[-10:] if len(context.user_history) > 10 else context.user_history
        
        if not recent_requests:
            return None

        current_request_type = request_data.get("request_type", "")
        
        # Check if this request type is unusual for this user
        request_types = [h.request_type for h in recent_requests]
        type_frequency = sum(1 for t in request_types if t == current_request_type) / len(request_types)

        # If request type is unusual (less than 20% of history)
        if type_frequency < 0.2:
            result["matched"] = True
            result["confidence"] = 0.6
            result["risk_level"] = "medium"
            result["reason"] = f"Unusual request type: {current_request_type}"
            
            # Check user trust score
            if context.user_profile.trust_score < 0.5:
                result["escalate"] = True
                result["risk_level"] = "high"
                result["reason"] += f" (low trust score: {context.user_profile.trust_score:.2f})"

        return result if result["matched"] else None

    return rule
