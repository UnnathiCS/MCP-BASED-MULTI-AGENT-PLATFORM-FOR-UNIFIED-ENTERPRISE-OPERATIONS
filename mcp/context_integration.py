"""
Integration between Context Handler and MCP Decision Engine.

This module bridges the context-aware decision handler with the main decision engine,
enabling intelligent routing based on user history, workflow state, and external data.

Integration Points:
1. Pre-processing: Enrich MCPRequest with context before intent detection
2. Agent scoring: Boost scores for preferred agents based on history
3. Policy evaluation: Apply context-based policies
4. Post-processing: Update context after agent execution
5. Escalation: Route to escalation manager based on context

Example Flow:
1. User requests refund
2. Gather context: customer history, contract, finance policies
3. Apply rules: VIP gets auto-approval, high-risk gets escalation
4. Route to appropriate agent
5. Update context with decision and outcome
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

from .context_handler import (
    ContextAwareDecisionHandler,
    UserProfileProvider,
    UserHistoryProvider,
    WorkflowContextProvider,
    ExternalDataProvider,
    UserHistoryRecord,
    ContextSourceType,
)
from .models import MCPRequest, MCPResponse, CapabilityScore
from .decision_engine import MCPDecisionEngine

logger = logging.getLogger(__name__)


@dataclass
class ContextEnrichedRequest:
    """MCP request enriched with decision context."""
    original_request: MCPRequest
    context_data: Dict[str, Any]
    routing_recommendations: List[Dict[str, Any]]
    risk_level: str
    escalation_needed: bool
    context_confidence: float


class ContextIntegrationLayer:
    """
    Integrates context-aware decision making with the MCP Decision Engine.
    
    Responsibilities:
    - Enrich requests with context before routing
    - Boost agent scores based on user preferences and history
    - Apply context-based policy rules
    - Update context after execution
    - Handle escalations with full context
    """

    def __init__(
        self,
        decision_engine: MCPDecisionEngine,
        context_handler: ContextAwareDecisionHandler,
    ):
        self.decision_engine = decision_engine
        self.context_handler = context_handler

    def process_request_with_context(self, request: MCPRequest) -> Tuple[MCPResponse, Optional[Dict[str, Any]]]:
        """
        Process request with full context awareness.
        
        Returns:
            Tuple of (MCPResponse, context_data)
        """
        logger.info(f"Processing request {request.request_id} with context awareness")

        # Step 1: Prepare context request data
        context_request_data = {
            "request_id": request.request_id,
            "user_id": request.user_id,
            "session_id": request.session_id,
            "workflow_id": request.metadata.get("workflow_id"),
            "request_type": request.metadata.get("request_type", "general"),
            "days_back": 30,  # Look back 30 days in history
        }

        # Step 2: Gather and enrich context
        decision_context = self.context_handler.gather_context(context_request_data)
        decision_context = self.context_handler.enrich_context(decision_context)

        # Step 3: Evaluate decision rules
        decision_result = self.context_handler.evaluate_decision_rules(decision_context, context_request_data)

        logger.info(
            f"Context evaluation: risk_level={decision_result['risk_level']}, "
            f"escalation_needed={decision_result['escalation_needed']}"
        )

        # Step 4: Handle escalation or normal routing
        if decision_result.get("escalation_needed"):
            response = self._handle_escalation(request, decision_context, decision_result)
        else:
            # Step 5: Apply context-aware agent selection
            response = self._route_with_context(request, decision_context, decision_result)

        # Step 6: Update context with execution result
        if response.status == "ok" and request.user_id:
            self._update_context_post_execution(request, response, decision_context)

        return response, decision_context.to_dict()

    def _route_with_context(
        self,
        request: MCPRequest,
        context_data: Dict[str, Any],
        decision_result: Dict[str, Any]
    ) -> MCPResponse:
        """
        Route request to appropriate agent based on context.
        
        Applies context-aware recommendations to agent selection.
        """
        logger.info("Routing request with context-based recommendations")

        # Get routing recommendations from decision rules
        recommendations = decision_result.get("routing_recommendations", [])

        # If we have strong recommendations, use them to bias agent selection
        if recommendations:
            top_recommendation = recommendations[0]
            logger.info(f"Top recommendation: {top_recommendation['agent']} ({top_recommendation['reason']})")

            # Boost metadata with recommendation
            request.metadata["context_recommendation"] = top_recommendation["agent"]
            request.metadata["context_confidence"] = decision_result.get("context_confidence", 0.5)

        # Add context risk level to metadata
        request.metadata["context_risk_level"] = decision_result.get("risk_level", "normal")

        # Process through normal decision engine
        response = self.decision_engine.process_request(request)

        return response

    def _handle_escalation(
        self,
        request: MCPRequest,
        context_data: Dict[str, Any],
        decision_result: Dict[str, Any]
    ) -> MCPResponse:
        """
        Handle escalation with full context.
        
        Routes to escalation manager or human review.
        """
        logger.warning(f"Escalating request {request.request_id}")

        # Mark request for escalation
        request.metadata["escalation_required"] = True
        request.metadata["escalation_reason"] = decision_result.get("risk_level", "unknown")
        request.metadata["context_data"] = context_data.to_dict() if hasattr(context_data, 'to_dict') else context_data

        # Update priority to high or critical
        if decision_result.get("risk_level") == "high":
            request.priority = "critical"

        # Route to escalation agent
        request.metadata["target_agent"] = "escalation-manager"

        # Process through normal decision engine
        response = self.decision_engine.process_request(request)

        return response

    def _update_context_post_execution(
        self,
        request: MCPRequest,
        response: MCPResponse,
        context_data: Dict[str, Any]
    ) -> None:
        """
        Update context after agent execution.
        
        Records execution in user history for future decisions.
        """
        try:
            user_id = request.user_id
            if not user_id:
                return

            # Create history record
            selected_agent = response.selected_agents[0] if response.selected_agents else "unknown"
            
            history_record = UserHistoryRecord(
                timestamp=datetime.utcnow().isoformat(),
                request_type=request.metadata.get("request_type", "general"),
                agent_id=selected_agent,
                status=response.status,
                duration_ms=int(
                    (datetime.fromisoformat(datetime.utcnow().isoformat()) -
                     datetime.fromisoformat(request.timestamp)).total_seconds() * 1000
                ),
                cost=float(response.result.get("cost", 0.0)) if response.result else 0.0,
                notes=response.result.get("notes", "") if response.result else "",
                metadata={
                    "request_id": request.request_id,
                    "intent": response.mcp_decision.intent if response.mcp_decision else None
                }
            )

            # Get history provider and update
            if ContextSourceType.USER_HISTORY in self.context_handler.providers:
                history_provider = self.context_handler.providers[ContextSourceType.USER_HISTORY]
                history_provider.add_record(user_id, history_record)
                logger.info(f"Updated user history for {user_id}")

            # Update user profile
            if ContextSourceType.USER_PROFILE in self.context_handler.providers:
                profile_provider = self.context_handler.providers[ContextSourceType.USER_PROFILE]
                profile_provider.update_profile(user_id, history_record)
                logger.info(f"Updated user profile for {user_id}")

        except Exception as e:
            logger.error(f"Error updating context post-execution: {e}")

    def boost_agent_scores_with_context(
        self,
        request: MCPRequest,
        context_data: Dict[str, Any],
        candidate_scores: List[Tuple[Any, float]]
    ) -> List[Tuple[Any, float]]:
        """
        Boost agent scores based on user history and preferences.
        
        Preferred agents (successful in past) get higher scores.
        """
        user_profile = context_data.user_profile if hasattr(context_data, 'user_profile') else context_data.get("user_profile")
        
        if not user_profile or not user_profile.preferred_agents:
            return candidate_scores

        boosted_scores = []
        for agent, score in candidate_scores:
            boost = 0.0
            
            if agent.agent_id in user_profile.preferred_agents:
                # Boost by 10% if this agent is in user's preferred list
                boost = 0.10 * score
                logger.info(f"Boosting {agent.agent_id} by {boost:.3f} (preferred agent)")

            boosted_scores.append((agent, score + boost))

        return sorted(boosted_scores, key=lambda x: x[1], reverse=True)

    def apply_context_aware_policies(
        self,
        request: MCPRequest,
        context_data: Dict[str, Any]
    ) -> List[str]:
        """
        Apply context-aware policies to filter candidates.
        
        Example:
        - High-risk users restricted to specific agents
        - VIP users get priority routing
        - Repeated escalations trigger manual review
        """
        filtered_agents = []

        user_profile = context_data.user_profile if hasattr(context_data, 'user_profile') else context_data.get("user_profile")
        
        if not user_profile:
            return filtered_agents

        # High-risk users: only allow premium agents
        if user_profile.risk_level == "high":
            logger.info(f"User {request.user_id} is high-risk, restricting to premium agents")
            # Return premium agent list (implementation depends on agent registry)
            filtered_agents = ["premium-agent-1", "premium-agent-2"]

        # VIP users: prioritize fast track
        elif user_profile.is_vip:
            logger.info(f"User {request.user_id} is VIP, enabling fast track")
            # Return fast-track agent list
            filtered_agents = ["fast-track-agent", "vip-agent"]

        # Normal users: allow all
        else:
            filtered_agents = []

        return filtered_agents


def create_context_integrated_decision_engine(
    base_engine: MCPDecisionEngine,
    context_handler: Optional[ContextAwareDecisionHandler] = None,
) -> ContextIntegrationLayer:
    """
    Factory function to create a context-integrated decision engine.
    
    Sets up all providers and integrates with base decision engine.
    """
    if context_handler is None:
        context_handler = ContextAwareDecisionHandler()

        # Register default providers
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

    # Create integration layer
    integration = ContextIntegrationLayer(base_engine, context_handler)

    return integration


# ============================================================================
# Integration Middleware for FastAPI
# ============================================================================

def create_context_middleware(integration_layer: ContextIntegrationLayer):
    """
    Create FastAPI middleware that applies context-aware decision making.
    
    Usage:
        app = FastAPI()
        middleware = create_context_middleware(integration_layer)
        app.add_middleware(middleware)
    """
    async def context_middleware(request, call_next):
        """Apply context-aware decision making to request."""
        # Extract MCP request from body
        try:
            body = await request.json()
            mcp_request = MCPRequest.from_dict(body)

            # Process with context
            response, context_data = integration_layer.process_request_with_context(mcp_request)

            # Add context to response headers for tracking
            if context_data:
                return {
                    "mcp_response": response.to_dict(),
                    "context": context_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return response.to_dict()

        except Exception as e:
            logger.error(f"Error in context middleware: {e}")
            # Fall through to normal processing if context fails
            return await call_next(request)

    return context_middleware


# ============================================================================
# Example Usage and Documentation
# ============================================================================

def example_setup_context_system():
    """
    Example: Set up context-aware decision system.
    
    Demonstrates how to configure context handlers, providers, and rules.
    """
    from .decision_engine import MCPDecisionEngine
    from .agent_registry import AgentRegistry
    from .intent_detector import IntentDetector
    from .policy_engine import PolicyEngine
    from .context_handler import (
        create_refund_decision_rule,
        create_contract_review_rule,
        create_anomaly_detection_rule,
    )

    # Create base components
    registry = AgentRegistry()
    intent_detector = IntentDetector()
    policy_engine = PolicyEngine()

    base_engine = MCPDecisionEngine(registry, intent_detector, policy_engine)

    # Create context handler
    context_handler = ContextAwareDecisionHandler()

    # Register default providers
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

    # Register external data provider with fetchers
    ext_provider = ExternalDataProvider()
    ext_provider.register_fetcher(
        "finance_system",
        lambda entity_type, entity_id: {
            "transaction_id": entity_id,
            "amount": 150.0,
            "approved_for_refund": True
        }
    )
    context_handler.register_provider(
        ContextSourceType.EXTERNAL_DATA,
        ext_provider
    )

    # Register decision rules
    context_handler.register_decision_rule(create_refund_decision_rule())
    context_handler.register_decision_rule(create_contract_review_rule())
    context_handler.register_decision_rule(create_anomaly_detection_rule())

    # Create integration layer
    integration = ContextIntegrationLayer(base_engine, context_handler)

    return integration, base_engine, context_handler
