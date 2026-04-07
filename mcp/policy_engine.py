"""
Policy Engine: evaluates policies to constrain routing and enforce compliance.
"""

import logging
from typing import List, Dict, Any, Optional, Callable
from .models import PolicyRule, MCPRequest

logger = logging.getLogger(__name__)


class PolicyEngine:
    """
    Evaluates policies to enforce constraints on:
    - Agent selection (allowed/blocked agents per request)
    - Data handling (masking, redaction, residency)
    - Cost limits and priority escalation
    - Compliance and audit requirements
    """

    def __init__(self):
        self.policies: Dict[str, PolicyRule] = {}
        self.condition_evaluators: Dict[str, Callable] = {}
        self._setup_default_evaluators()

    def _setup_default_evaluators(self):
        """Register default condition evaluators."""
        self.register_evaluator(
            "priority",
            lambda req, val: req.priority in val if isinstance(val, list) else req.priority == val
        )
        self.register_evaluator(
            "user_role",
            lambda req, val: req.metadata.get("role") in val if isinstance(val, list) else req.metadata.get("role") == val
        )
        self.register_evaluator(
            "contains_sensitive_data",
            lambda req, val: self._has_sensitive_keywords(req.text) == val
        )
        self.register_evaluator(
            "request_priority",
            lambda req, val: req.priority in val if isinstance(val, list) else req.priority == val
        )

    def register_policy(self, policy: PolicyRule) -> bool:
        """Register or update a policy."""
        try:
            self.policies[policy.rule_id] = policy
            logger.info(f"Registered policy: {policy.rule_id} ({policy.name})")
            return True
        except Exception as e:
            logger.error(f"Failed to register policy: {e}")
            return False

    def register_evaluator(self, condition_type: str, evaluator: Callable) -> None:
        """Register a custom condition evaluator."""
        self.condition_evaluators[condition_type] = evaluator

    def evaluate_request(self, request: MCPRequest) -> Dict[str, Any]:
        """
        Evaluate all policies against a request.
        
        Returns:
            {
              "allowed_agents": [...],
              "blocked_agents": [...],
              "requires_approval": bool,
              "data_handling": {...},
              "policy_score": float (0-1)
            }
        """
        allowed_agents = set()
        blocked_agents = set()
        requires_approval = False
        data_handling = {}
        matched_policies = []

        for policy in self.policies.values():
            if not policy.enabled:
                continue

            if self._evaluate_condition(request, policy.condition):
                matched_policies.append(policy.rule_id)
                
                if policy.allowed_agents:
                    allowed_agents.update(policy.allowed_agents)
                
                blocked_agents.update(policy.blocked_agents)
                requires_approval = requires_approval or policy.requires_approval
                data_handling.update(policy.data_handling)

        # If no policies matched, allow all agents (open policy)
        if not matched_policies:
            logger.debug(f"No policies matched request {request.request_id}")

        policy_score = 1.0 if not blocked_agents else 0.5

        return {
            "allowed_agents": list(allowed_agents) if allowed_agents else None,
            "blocked_agents": list(blocked_agents),
            "requires_approval": requires_approval,
            "data_handling": data_handling,
            "policy_score": policy_score,
            "matched_policies": matched_policies,
        }

    def _evaluate_condition(self, request: MCPRequest, condition: Dict[str, Any]) -> bool:
        """Evaluate a condition against a request."""
        if not condition:
            return True

        for key, val in condition.items():
            if key in self.condition_evaluators:
                evaluator = self.condition_evaluators[key]
                if not evaluator(request, val):
                    return False
            else:
                logger.warning(f"Unknown condition type: {key}")
                return False

        return True

    def _has_sensitive_keywords(self, text: str) -> bool:
        """Check if text contains sensitive keywords."""
        sensitive_keywords = ["ssn", "credit card", "password", "api key", "token", "secret"]
        text_lower = text.lower()
        return any(kw in text_lower for kw in sensitive_keywords)

    def filter_agents_by_policy(self, request: MCPRequest, candidate_agents: List[str]) -> List[str]:
        """Filter candidate agents based on policies."""
        policy_result = self.evaluate_request(request)

        blocked = set(policy_result.get("blocked_agents", []))
        allowed = policy_result.get("allowed_agents")

        if allowed is not None:
            filtered = [a for a in candidate_agents if a in allowed and a not in blocked]
        else:
            filtered = [a for a in candidate_agents if a not in blocked]

        logger.info(
            f"Filtered agents for request {request.request_id}: {candidate_agents} -> {filtered}"
        )
        return filtered

    def apply_data_handling(self, request: MCPRequest, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Apply data handling policies (masking, redaction) to payload."""
        policy_result = self.evaluate_request(request)
        data_handling = policy_result.get("data_handling", {})

        if "mask_fields" in data_handling:
            for field in data_handling["mask_fields"]:
                if field in payload:
                    payload[field] = "***MASKED***"

        return payload

    def to_dict(self) -> Dict[str, Any]:
        """Serialize policies to dict."""
        return {
            policy_id: policy.to_dict()
            for policy_id, policy in self.policies.items()
        }
