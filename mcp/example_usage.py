"""
Example usage of the MCP Decision Engine.

Demonstrates:
- Initializing the MCP system
- Registering agents
- Processing requests
- Observing routing decisions
"""

import logging
import json
from typing import Dict, Any

from mcp.models import MCPRequest, Capability, AgentRecord
from mcp.agent_registry import AgentRegistry
from mcp.intent_detector import IntentDetector
from mcp.policy_engine import PolicyEngine
from mcp.decision_engine import MCPDecisionEngine
from mcp.registry_config import get_default_registry_config
from mcp.policy_config import get_default_policies

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def setup_mcp_system() -> MCPDecisionEngine:
    """
    Initialize the MCP system with agents, policies, and detectors.
    
    Returns:
        Initialized MCPDecisionEngine
    """
    # 1. Initialize components
    registry = AgentRegistry()
    intent_detector = IntentDetector()
    policy_engine = PolicyEngine()

    # 2. Register agents from config
    config = get_default_registry_config()
    for agent_dict in config.get("agents", {}).values():
        agent_record = AgentRecord.from_dict(agent_dict)
        registry.register_agent(agent_record)

    logger.info(f"Registered {len(registry.agents)} agents")

    # 3. Register policies
    for policy in get_default_policies():
        policy_engine.register_policy(policy)

    logger.info(f"Registered {len(policy_engine.policies)} policies")

    # 4. Initialize decision engine
    engine = MCPDecisionEngine(registry, intent_detector, policy_engine)

    logger.info("MCP system initialized successfully")
    return engine


def example_document_review_request(engine: MCPDecisionEngine):
    """Example: User submits a document for review."""
    logger.info("\n" + "=" * 80)
    logger.info("Example 1: Document Review Request")
    logger.info("=" * 80)

    request = MCPRequest(
        user_id="user-123",
        session_id="session-abc",
        text="Please review this NDA contract for compliance with data protection regulations",
        attachments=[{"name": "nda.pdf", "url": "s3://bucket/nda.pdf"}],
        metadata={"source": "dashboard", "role": "legal"},
        priority="high"
    )

    response = engine.process_request(request)

    print_response(response)


def example_support_ticket_request(engine: MCPDecisionEngine):
    """Example: User submits an IT support request."""
    logger.info("\n" + "=" * 80)
    logger.info("Example 2: IT Support Request")
    logger.info("=" * 80)

    request = MCPRequest(
        user_id="user-456",
        session_id="session-def",
        text="My VPN connection is not working. I need to access the internal network urgently.",
        metadata={"source": "dashboard", "role": "employee"},
        priority="high"
    )

    response = engine.process_request(request)

    print_response(response)


def example_password_reset_request(engine: MCPDecisionEngine):
    """Example: User requests password reset (low confidence intent)."""
    logger.info("\n" + "=" * 80)
    logger.info("Example 3: Password Reset Request")
    logger.info("=" * 80)

    request = MCPRequest(
        user_id="user-789",
        text="I forgot my password and can't log in",
        metadata={"source": "dashboard", "role": "employee"},
        priority="normal"
    )

    response = engine.process_request(request)

    print_response(response)


def example_multi_step_workflow(engine: MCPDecisionEngine):
    """Example: High-risk document triggers multi-step workflow (review -> escalate to support)."""
    logger.info("\n" + "=" * 80)
    logger.info("Example 4: High-Risk Document Escalation Workflow")
    logger.info("=" * 80)

    request = MCPRequest(
        user_id="user-legal",
        text="Review this vendor contract urgently - potential data breach clause detected",
        attachments=[{"name": "vendor_contract.pdf", "url": "s3://bucket/vendor.pdf"}],
        metadata={"source": "email", "role": "legal"},
        priority="critical"
    )

    response = engine.process_request(request)

    print_response(response)

    # If document agent detected high risk, MCP would have escalated to support
    if response.result.get("escalations"):
        logger.info("Escalation triggered for support team!")


def example_registry_status(engine: MCPDecisionEngine):
    """Example: Check registry and agent status."""
    logger.info("\n" + "=" * 80)
    logger.info("Example 5: Registry and Agent Status")
    logger.info("=" * 80)

    summary = engine.get_registry_summary()
    print(json.dumps(summary, indent=2))


def print_response(response) -> None:
    """Pretty-print an MCP response."""
    print("\nMCP Response:")
    print(f"  Request ID: {response.request_id}")
    print(f"  Status: {response.status}")
    print(f"  Intent: {response.mcp_decision.intent}")
    print(f"  Confidence: {response.mcp_decision.confidence:.2%}")
    print(f"  Selected Agents: {response.selected_agents}")
    print(f"  Error: {response.error or 'None'}")

    if response.agent_responses:
        print("\n  Agent Responses:")
        for ar in response.agent_responses:
            print(f"    - {ar.agent_id}: {ar.status}")

    if response.result.get("primary_result"):
        print(f"\n  Primary Result: {json.dumps(response.result.get('primary_result'), indent=2)[:200]}...")

    print("\nAudit Trail:")
    print(f"  Timestamp: {response.audit.get('timestamp')}")
    print(f"  Trace ID: {response.audit.get('trace_id')}")
    print(f"  Matched Policies: {response.audit.get('matched_policies')}")


if __name__ == "__main__":
    # Setup MCP system
    engine = setup_mcp_system()

    # Run examples
    try:
        example_document_review_request(engine)
        example_support_ticket_request(engine)
        example_password_reset_request(engine)
        example_multi_step_workflow(engine)
        example_registry_status(engine)

        logger.info("\n" + "=" * 80)
        logger.info("All examples completed successfully!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)
