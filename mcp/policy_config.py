"""
Example policy rules for the MCP system.

Policies enforce constraints on routing, data handling, cost limits, and compliance.
"""

from typing import List, Dict, Any
from .models import PolicyRule


def get_default_policies() -> List[PolicyRule]:
    """Return the default set of policy rules."""
    return [
        PolicyRule(
            rule_id="high-priority-escalation",
            name="High Priority Escalation",
            condition={"request_priority": ["high", "critical"]},
            allowed_agents=["support-agent"],
            blocked_agents=[],
            requires_approval=False,
            data_handling={},
            enabled=True,
        ),
        PolicyRule(
            rule_id="sensitive-data-policy",
            name="Sensitive Data Protection",
            condition={"contains_sensitive_data": True},
            allowed_agents=["support-agent"],  # Only trust support agent with sensitive data
            blocked_agents=[],
            requires_approval=True,
            data_handling={
                "mask_fields": ["ssn", "credit_card", "password", "api_key"],
            },
            enabled=True,
        ),
        PolicyRule(
            rule_id="document-review-policy",
            name="Document Review Access",
            condition={"user_role": ["admin", "compliance_officer", "legal"]},
            allowed_agents=["document-review-agent"],
            blocked_agents=[],
            requires_approval=False,
            data_handling={},
            enabled=True,
        ),
        PolicyRule(
            rule_id="fallback-policy",
            name="Default Fallback",
            condition={},  # Matches all requests (no condition)
            allowed_agents=["support-agent", "document-review-agent"],
            blocked_agents=[],
            requires_approval=False,
            data_handling={},
            enabled=True,
        ),
    ]


def get_policy_by_name(name: str) -> PolicyRule:
    """Get a specific policy by name."""
    policies = get_default_policies()
    for p in policies:
        if p.name == name:
            return p
    raise ValueError(f"Policy not found: {name}")


def describe_policies() -> Dict[str, Any]:
    """Get a human-readable description of all policies."""
    policies = get_default_policies()
    return {
        "total_policies": len(policies),
        "policies": [
            {
                "rule_id": p.rule_id,
                "name": p.name,
                "condition": p.condition,
                "allowed_agents": p.allowed_agents,
                "blocked_agents": p.blocked_agents,
                "requires_approval": p.requires_approval,
            }
            for p in policies
        ]
    }
