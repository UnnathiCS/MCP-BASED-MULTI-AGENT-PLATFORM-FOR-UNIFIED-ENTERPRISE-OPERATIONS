"""
Context-Aware Decision Making Examples and Usage Guide.

This module demonstrates practical examples of using context-aware decision
making for intelligent routing and escalation.

Real-World Scenarios:
1. Refund Requests - Route based on amount, customer history, VIP status
2. Contract Reviews - Escalate complex/high-value contracts
3. Support Escalation - Route high-risk issues appropriately
4. Anomaly Detection - Flag unusual user behavior
5. Multi-step Workflows - Maintain context across workflow steps
"""

import logging
from typing import Dict, Any
from datetime import datetime, timedelta
import json

from .context_handler import (
    ContextAwareDecisionHandler,
    UserProfileProvider,
    UserHistoryProvider,
    WorkflowContextProvider,
    ExternalDataProvider,
    UserHistoryRecord,
    UserProfile,
    WorkflowContext,
    ContextSourceType,
    create_refund_decision_rule,
    create_contract_review_rule,
    create_anomaly_detection_rule,
)
from .context_integration import (
    ContextIntegrationLayer,
    create_context_integrated_decision_engine,
)
from .models import MCPRequest

logger = logging.getLogger(__name__)


# ============================================================================
# Scenario 1: Refund Request Processing
# ============================================================================

class RefundRequestScenario:
    """
    Scenario: Customer requests refund for $150 product.
    
    Context needed:
    - Customer history (previous refunds, complaints)
    - Transaction details (purchase date, payment method)
    - Finance policies (refund limits, approval authority)
    - Customer VIP status
    
    Decision rules:
    - VIP customers with good history: auto-approve refunds < $100
    - Large refunds (> $500): require manager approval
    - Repeat refund requests: flag for review
    - High-risk customers: require additional verification
    """

    @staticmethod
    def setup_scenario():
        """Set up context handlers for refund processing."""
        context_handler = ContextAwareDecisionHandler()

        # Register user profile provider
        profile_provider = UserProfileProvider()
        
        # Pre-populate test customer profiles
        test_customers = {
            "user-vip-001": UserProfile(
                user_id="user-vip-001",
                created_at=datetime.utcnow().isoformat(),
                total_requests=50,
                successful_requests=48,
                failed_requests=0,
                escalated_requests=2,
                total_cost=5000.0,
                avg_resolution_time_ms=5000,
                preferred_agents=["finance-agent"],
                risk_level="low",
                is_vip=True,
            ),
            "user-normal-001": UserProfile(
                user_id="user-normal-001",
                created_at=datetime.utcnow().isoformat(),
                total_requests=10,
                successful_requests=8,
                failed_requests=2,
                escalated_requests=0,
                total_cost=500.0,
                avg_resolution_time_ms=10000,
                risk_level="normal",
                is_vip=False,
            ),
        }
        profile_provider.user_store = test_customers
        context_handler.register_provider(ContextSourceType.USER_PROFILE, profile_provider)

        # Register user history provider
        history_provider = UserHistoryProvider()
        
        # Pre-populate history
        vip_history = [
            UserHistoryRecord(
                timestamp=(datetime.utcnow() - timedelta(days=5)).isoformat(),
                request_type="refund",
                agent_id="finance-agent",
                status="success",
                duration_ms=3000,
                cost=50.0
            ),
            UserHistoryRecord(
                timestamp=(datetime.utcnow() - timedelta(days=10)).isoformat(),
                request_type="support",
                agent_id="support-agent",
                status="success",
                duration_ms=5000,
                cost=0.0
            ),
        ]
        history_provider.history_store["user-vip-001"] = vip_history
        context_handler.register_provider(ContextSourceType.USER_HISTORY, history_provider)

        # Register external data provider for finance
        ext_provider = ExternalDataProvider()
        ext_provider.register_fetcher(
            "finance_system",
            lambda entity_type, entity_id: {
                "transaction_id": entity_id,
                "amount": 150.0,
                "purchase_date": "2024-01-01",
                "payment_method": "credit_card",
                "refund_policy": "30-day money-back guarantee",
                "approved_for_refund": True
            }
        )
        context_handler.register_provider(ContextSourceType.EXTERNAL_DATA, ext_provider)

        # Register decision rules
        context_handler.register_decision_rule(
            create_refund_decision_rule(finance_threshold=500.0, vip_auto_approve=True)
        )

        return context_handler

    @staticmethod
    def process_vip_refund():
        """Process refund for VIP customer with good history."""
        context_handler = RefundRequestScenario.setup_scenario()

        request_data = {
            "request_id": "req-refund-001",
            "user_id": "user-vip-001",
            "session_id": "session-001",
            "request_type": "refund",
            "transaction_amount": 150.0,
            "external_data_refs": [
                {
                    "source": "finance_system",
                    "entity_type": "transaction",
                    "entity_id": "txn-12345"
                }
            ]
        }

        decision = context_handler.make_context_aware_decision(request_data)

        print(json.dumps(decision, indent=2, default=str))
        return decision

    @staticmethod
    def process_large_refund():
        """Process large refund that requires escalation."""
        context_handler = RefundRequestScenario.setup_scenario()

        request_data = {
            "request_id": "req-refund-002",
            "user_id": "user-normal-001",
            "session_id": "session-002",
            "request_type": "refund",
            "transaction_amount": 5000.0,  # Large amount
            "external_data_refs": [
                {
                    "source": "finance_system",
                    "entity_type": "transaction",
                    "entity_id": "txn-12346"
                }
            ]
        }

        decision = context_handler.make_context_aware_decision(request_data)

        print(json.dumps(decision, indent=2, default=str))
        return decision


# ============================================================================
# Scenario 2: Contract Review with Risk Assessment
# ============================================================================

class ContractReviewScenario:
    """
    Scenario: User submits contract for review.
    
    Context needed:
    - Contract type and value
    - User authority level
    - Organization policies
    - Previous contract reviews
    
    Decision rules:
    - Standard contracts (< $10k): route to document reviewer
    - High-value contracts (> $100k): require legal team
    - Complex types (NDA, partnership): require lawyer
    - First-time contract reviewer: require approval
    """

    @staticmethod
    def setup_scenario():
        """Set up context handlers for contract review."""
        context_handler = ContextAwareDecisionHandler()

        # Register providers
        context_handler.register_provider(
            ContextSourceType.USER_PROFILE,
            UserProfileProvider()
        )
        context_handler.register_provider(
            ContextSourceType.USER_HISTORY,
            UserHistoryProvider()
        )
        context_handler.register_provider(
            ContextSourceType.EXTERNAL_DATA,
            ExternalDataProvider()
        )

        # Register contract review rule
        context_handler.register_decision_rule(create_contract_review_rule())

        return context_handler

    @staticmethod
    def process_high_value_contract():
        """Process high-value contract requiring escalation."""
        context_handler = ContractReviewScenario.setup_scenario()

        request_data = {
            "request_id": "req-contract-001",
            "user_id": "user-001",
            "session_id": "session-contract-001",
            "request_type": "contract_review",
            "contract_type": "partnership",
            "contract_value": 250000.0,  # High value
            "external_data_refs": [
                {
                    "source": "contract_db",
                    "entity_type": "contract",
                    "entity_id": "contract-001"
                }
            ]
        }

        decision = context_handler.make_context_aware_decision(request_data)

        print(json.dumps(decision, indent=2, default=str))
        return decision


# ============================================================================
# Scenario 3: Multi-Step Workflow with Context Persistence
# ============================================================================

class MultiStepWorkflowScenario:
    """
    Scenario: Complex request requiring multiple agents.
    
    Flow:
    1. User requests document review
    2. Document review agent processes document
    3. If high-risk, escalate to legal team
    4. Legal team routes to finance if contract review
    5. All steps maintain shared context
    
    Context needs:
    - Workflow state (current step, previous agents)
    - Decision history within workflow
    - Payload persistence across steps
    """

    @staticmethod
    def setup_scenario():
        """Set up context handlers for multi-step workflows."""
        context_handler = ContextAwareDecisionHandler()

        # Register all providers
        context_handler.register_provider(
            ContextSourceType.USER_PROFILE,
            UserProfileProvider()
        )
        context_handler.register_provider(
            ContextSourceType.USER_HISTORY,
            UserHistoryProvider()
        )
        context_handler.register_provider(
            ContextSourceType.WORKFLOW_STATE,
            WorkflowContextProvider()
        )
        context_handler.register_provider(
            ContextSourceType.EXTERNAL_DATA,
            ExternalDataProvider()
        )

        return context_handler

    @staticmethod
    def process_document_to_legal_escalation():
        """Process document review with potential escalation to legal."""
        context_handler = MultiStepWorkflowScenario.setup_scenario()

        # Get workflow provider
        workflow_provider = context_handler.providers[ContextSourceType.WORKFLOW_STATE]
        
        # Create workflow context
        workflow_id = "workflow-doc-legal-001"
        workflow_context = workflow_provider.create_workflow(workflow_id, total_steps=3)

        print(f"\n=== Step 1: Document Review ===")
        print(f"Workflow: {workflow_id}")
        print(f"Step: {workflow_context.step_index + 1}/{workflow_context.total_steps}")

        # Step 1: Request document review
        step1_request = {
            "request_id": "req-step1-001",
            "user_id": "user-001",
            "session_id": "session-001",
            "workflow_id": workflow_id,
            "request_type": "document_review",
            "document_type": "contract"
        }

        decision1 = context_handler.make_context_aware_decision(step1_request)
        print(f"Decision: {decision1['decision']['routing_recommendations']}")

        # Update workflow for step 2
        workflow_provider.update_workflow(workflow_id, "document-review-agent", {"step": 1})

        print(f"\n=== Step 2: Risk Assessment ===")

        # Step 2: Based on risk, escalate to legal
        step2_request = {
            "request_id": "req-step2-001",
            "user_id": "user-001",
            "session_id": "session-001",
            "workflow_id": workflow_id,
            "request_type": "legal_review",
            "contract_value": 150000.0,
            "risk_level": "high"
        }

        decision2 = context_handler.make_context_aware_decision(step2_request)
        print(f"Decision: {decision2['decision']['routing_recommendations']}")

        # Update workflow for step 3
        workflow_provider.update_workflow(workflow_id, "legal-agent", {"step": 2})

        print(f"\n=== Step 3: Final Processing ===")

        # Get final workflow state
        final_context = context_handler.gather_context({
            "workflow_id": workflow_id,
            "user_id": "user-001"
        })

        print(f"Workflow state: {final_context.workflow_context.to_dict() if final_context.workflow_context else 'None'}")
        print(f"Previous agents: {final_context.workflow_context.previous_agents if final_context.workflow_context else []}")


# ============================================================================
# Scenario 4: Anomaly Detection and Fraud Prevention
# ============================================================================

class AnomalyDetectionScenario:
    """
    Scenario: Detect unusual user behavior and flag for review.
    
    Context needed:
    - User history (request patterns)
    - User profile (risk level, trust score)
    - Request characteristics
    
    Rules:
    - Unusual request types for user: flag for review
    - High-value requests from low-trust users: escalate
    - Rapid repeated requests: rate limiting
    - Suspicious patterns: require verification
    """

    @staticmethod
    def setup_scenario():
        """Set up context handlers for anomaly detection."""
        context_handler = ContextAwareDecisionHandler()

        # Register user profile provider
        profile_provider = UserProfileProvider()
        profile_provider.user_store["user-anomaly-001"] = UserProfile(
            user_id="user-anomaly-001",
            created_at=datetime.utcnow().isoformat(),
            total_requests=20,
            successful_requests=20,
            failed_requests=0,
            escalated_requests=0,
            total_cost=1000.0,
            preferred_agents=["support-agent"],  # Usually uses support agent
            risk_level="low",
            trust_score=0.95
        )
        context_handler.register_provider(ContextSourceType.USER_PROFILE, profile_provider)

        # Register user history provider
        history_provider = UserHistoryProvider()
        
        # Build history: mostly support requests
        user_history = [
            UserHistoryRecord(
                timestamp=(datetime.utcnow() - timedelta(days=i)).isoformat(),
                request_type="support",
                agent_id="support-agent",
                status="success",
                duration_ms=5000,
                cost=0.0
            )
            for i in range(1, 21)
        ]
        history_provider.history_store["user-anomaly-001"] = user_history
        context_handler.register_provider(ContextSourceType.USER_HISTORY, history_provider)

        # Register anomaly detection rule
        context_handler.register_decision_rule(create_anomaly_detection_rule())

        return context_handler

    @staticmethod
    def process_anomalous_request():
        """Process request that's anomalous for this user."""
        context_handler = AnomalyDetectionScenario.setup_scenario()

        # User normally uses support agent, but now requests finance
        request_data = {
            "request_id": "req-anomaly-001",
            "user_id": "user-anomaly-001",
            "session_id": "session-anomaly-001",
            "request_type": "refund",  # Unusual for this user!
            "transaction_amount": 5000.0
        }

        decision = context_handler.make_context_aware_decision(request_data)

        print(json.dumps(decision, indent=2, default=str))
        return decision


# ============================================================================
# Scenario 5: Integration with Decision Engine
# ============================================================================

class IntegratedDecisionScenario:
    """
    Scenario: Full integration with MCP decision engine.
    
    Demonstrates how context-aware decisions integrate with agent selection,
    policy enforcement, and execution.
    """

    @staticmethod
    def process_refund_with_integration():
        """
        Full example: Process refund request through integrated system.
        
        Flow:
        1. Receive MCPRequest for refund
        2. Gather context (user history, finance data)
        3. Evaluate decision rules
        4. Route to appropriate agent based on context
        5. Update context with execution result
        """
        from .agent_registry import AgentRegistry
        from .intent_detector import IntentDetector
        from .policy_engine import PolicyEngine
        from .decision_engine import MCPDecisionEngine

        # Create base components
        registry = AgentRegistry()
        intent_detector = IntentDetector()
        policy_engine = PolicyEngine()
        base_engine = MCPDecisionEngine(registry, intent_detector, policy_engine)

        # Create context handler
        context_handler = ContextAwareDecisionHandler()
        context_handler.register_provider(
            ContextSourceType.USER_PROFILE,
            UserProfileProvider()
        )
        context_handler.register_provider(
            ContextSourceType.USER_HISTORY,
            UserHistoryProvider()
        )
        context_handler.register_provider(
            ContextSourceType.EXTERNAL_DATA,
            ExternalDataProvider()
        )
        context_handler.register_decision_rule(create_refund_decision_rule())

        # Create integration layer
        integration = ContextIntegrationLayer(base_engine, context_handler)

        # Create MCP request
        request = MCPRequest(
            request_id="req-integrated-001",
            user_id="user-vip-001",
            session_id="session-001",
            text="I would like to request a refund for my recent purchase",
            metadata={
                "request_type": "refund",
                "transaction_amount": 150.0
            }
        )

        # Process with full context awareness
        response, context_data = integration.process_request_with_context(request)

        print(f"Response Status: {response.status}")
        print(f"Selected Agents: {response.selected_agents}")
        if context_data:
            print(f"Risk Level: {context_data['decision'].get('risk_level')}")
            print(f"Escalation Needed: {context_data['decision'].get('escalation_needed')}")

        return response, context_data


# ============================================================================
# Main Example Runner
# ============================================================================

def run_all_scenarios():
    """Run all example scenarios."""
    print("=" * 80)
    print("CONTEXT-AWARE DECISION MAKING SCENARIOS")
    print("=" * 80)

    print("\n" + "=" * 80)
    print("SCENARIO 1: VIP Customer Refund (Auto-Approve)")
    print("=" * 80)
    RefundRequestScenario.process_vip_refund()

    print("\n" + "=" * 80)
    print("SCENARIO 2: Large Refund (Escalation Required)")
    print("=" * 80)
    RefundRequestScenario.process_large_refund()

    print("\n" + "=" * 80)
    print("SCENARIO 3: High-Value Contract (Legal Escalation)")
    print("=" * 80)
    ContractReviewScenario.process_high_value_contract()

    print("\n" + "=" * 80)
    print("SCENARIO 4: Multi-Step Workflow")
    print("=" * 80)
    MultiStepWorkflowScenario.process_document_to_legal_escalation()

    print("\n" + "=" * 80)
    print("SCENARIO 5: Anomaly Detection")
    print("=" * 80)
    AnomalyDetectionScenario.process_anomalous_request()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    run_all_scenarios()
