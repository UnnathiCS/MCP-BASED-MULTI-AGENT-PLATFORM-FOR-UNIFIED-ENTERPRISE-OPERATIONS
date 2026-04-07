"""
MCP Decision Engine: core orchestration and routing logic.

Responsibilities:
- Accept user requests
- Perform intent detection
- Select optimal agent(s)
- Compose execution plans
- Invoke agents and aggregate results
- Handle fallbacks and error recovery
"""

import logging
import requests
import time
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from .models import (
    MCPRequest,
    MCPDecision,
    MCPResponse,
    AgentResponse,
    ExecutionPlan,
    ExecutionTask,
    CapabilityScore,
    AgentInvocation,
)
from .agent_registry import AgentRegistry
from .intent_detector import IntentDetector
from .policy_engine import PolicyEngine
from .decision_explainer import DecisionExplainer, DecisionTracer

logger = logging.getLogger(__name__)


class MCPDecisionEngine:
    """
    Main orchestration engine for the MCP system.
    
    Decision flow:
    1. Receive MCPRequest
    2. Authenticate & authorize user
    3. Detect intent (rule + model + semantic)
    4. Query agent registry for candidates
    5. Score candidates (capability, health, policy, cost, priority)
    6. Apply policy constraints
    7. Generate execution plan (sync/async/pipeline)
    8. Invoke agent(s) with standard contract
    9. Aggregate results with audit trail
    10. Fallback if needed
    """

    def __init__(
        self,
        agent_registry: AgentRegistry,
        intent_detector: IntentDetector,
        policy_engine: PolicyEngine,
        enable_explainability: bool = True,
    ):
        self.registry = agent_registry
        self.intent_detector = intent_detector
        self.policy_engine = policy_engine
        
        self.confidence_threshold_high = 0.80
        self.confidence_threshold_medium = 0.60
        self.confidence_threshold_low = 0.40
        self.enable_fallbacks = True
        
        # Explainability features
        self.enable_explainability = enable_explainability
        self.explainer = DecisionExplainer() if enable_explainability else None

    def process_request(self, request: MCPRequest) -> MCPResponse:
        """
        Main entry point: process a user request end-to-end.
        
        Returns an MCPResponse with:
        - Decision (intent + selected agents + plan)
        - Results from agent invocations
        - Audit trail
        - Detailed explanation (if explainability enabled)
        """
        logger.info(f"Processing request {request.request_id}: {request.text[:50]}...")
        
        # Initialize tracing if enabled
        tracer = DecisionTracer() if self.enable_explainability else None
        start_time = time.time()
        
        if tracer:
            tracer.record_event("request_received", f"Received request: {request.text[:50]}...", {
                "request_id": request.request_id,
                "user_id": request.user_id,
                "priority": request.priority,
            })

        try:
            # Step 1: Intent detection
            if tracer:
                tracer.record_event("intent_detection_start", "Starting intent detection")
            
            intent_matches = self.intent_detector.detect(request.text, request.intent_hints)
            if not intent_matches:
                return self._error_response(request, "No intent detected", "error")

            top_intent = intent_matches[0]
            logger.info(f"Top intent: {top_intent.name} (confidence {top_intent.confidence:.2f})")
            
            if tracer:
                tracer.record_event("intent_detected", f"Intent: {top_intent.name}", {
                    "intent": top_intent.name,
                    "confidence": top_intent.confidence,
                    "method": top_intent.method,
                    "rationale": top_intent.rationale,
                })

            # Step 2: Find candidate agents
            if tracer:
                tracer.record_event("candidate_search_start", "Searching for candidate agents")
            
            candidates = self._find_candidate_agents(top_intent.name)
            if not candidates:
                return self._error_response(request, f"No agents found for intent {top_intent.name}", "error")

            logger.info(f"Candidate agents: {[a.agent_id for a in candidates]}")
            
            if tracer:
                tracer.record_event("candidates_found", f"Found {len(candidates)} candidates", {
                    "candidates": [a.agent_id for a in candidates],
                })

            # Step 3: Score and rank candidates
            if tracer:
                tracer.record_event("scoring_start", "Scoring candidate agents")
            
            scored = self._score_candidates(request, candidates, top_intent)
            if not scored:
                return self._error_response(request, "No agents met scoring threshold", "error")

            best_agents = [s[0] for s in scored[:3]]  # Top 3
            logger.info(f"Ranked agents: {[a.agent_id for a in best_agents]}")
            
            if tracer:
                tracer.record_event("scoring_complete", "Scoring complete", {
                    "ranked_agents": [(a.agent_id, float(s)) for a, s in scored[:3]],
                })

            # Step 4: Apply policy constraints
            if tracer:
                tracer.record_event("policy_filter_start", "Applying policy filters")
            
            allowed_agents = self.policy_engine.filter_agents_by_policy(request, [a.agent_id for a in best_agents])
            if not allowed_agents:
                return self._error_response(request, "Policies blocked all candidate agents", "error")

            best_agent = next((a for a in best_agents if a.agent_id in allowed_agents), best_agents[0])
            blocked_agents = [(a.agent_id, "Blocked by policy") for a in best_agents if a.agent_id not in allowed_agents]
            logger.info(f"Selected primary agent: {best_agent.agent_id}")
            
            if tracer:
                tracer.record_event("policy_filter_complete", "Policy filtering complete", {
                    "selected_agent": best_agent.agent_id,
                    "allowed_agents": allowed_agents,
                    "blocked_agents": blocked_agents,
                })

            # Step 5: Generate execution plan
            plan = self._generate_plan(request, best_agent, top_intent)

            # Step 6: Invoke agent(s)
            if tracer:
                tracer.record_event("agent_invocation_start", f"Invoking agent: {best_agent.agent_id}")
            
            agent_responses = self._invoke_agents(request, plan)
            
            if tracer:
                tracer.record_event("agent_invocation_complete", "Agent invocation complete")

            # Step 7: Aggregate results
            result = self._aggregate_results(agent_responses)

            # Step 8: Check for suggested actions (e.g., escalation)
            escalations = self._handle_suggested_actions(request, agent_responses)
            if escalations:
                result["escalations"] = escalations

            # Build MCP decision object
            mcp_decision = MCPDecision(
                request_id=request.request_id,
                intent=top_intent.name,
                confidence=top_intent.confidence,
                selected_agents=[{"agent_id": a.agent_id, "endpoint": a.endpoint} for a in best_agents],
                plan=plan,
                confidence_sufficient=top_intent.confidence >= self.confidence_threshold_high,
                reasoning=f"Intent matched with {top_intent.confidence:.2%} confidence via {top_intent.method}"
            )
            
            # Create explanation if enabled
            explanation = None
            if self.enable_explainability and self.explainer:
                processing_time = (time.time() - start_time) * 1000
                explanation = self.explainer.explain(
                    request=request,
                    intent_match=top_intent,
                    candidates_with_scores=scored,
                    selected_agent=best_agent,
                    policies_applied=self.policy_engine.evaluate_request(request).get("matched_policies", []),
                    blocked_agents=blocked_agents,
                    processing_time_ms=processing_time,
                )
                
                # Log explanation
                self.explainer.log_explanation(explanation, level="info", include_scoring=True)
                if tracer:
                    tracer.record_event("explanation_generated", "Decision explanation generated", {
                        "decision_id": explanation.decision_id,
                        "processing_time_ms": processing_time,
                    })

            # Build response with explanation
            response = MCPResponse(
                request_id=request.request_id,
                status="ok",
                mcp_decision=mcp_decision,
                result=result,
                selected_agents=[a.agent_id for a in best_agents],
                agent_responses=agent_responses,
                audit={
                    "timestamp": datetime.utcnow().isoformat(),
                    "matched_policies": self.policy_engine.evaluate_request(request).get("matched_policies", []),
                    "trace_id": request.metadata.get("trace_id", str(uuid.uuid4())),
                }
            )
            
            # Add explanation to response metadata if available
            if explanation and hasattr(response, "metadata"):
                response.metadata = response.metadata or {}
                response.metadata["decision_explanation"] = explanation.to_dict()
            
            # Log trace if available
            if tracer:
                logger.debug(tracer.get_trace_text())

            return response

        except Exception as e:
            logger.error(f"Error processing request: {e}", exc_info=True)
            if tracer:
                tracer.record_event("error", f"Exception: {str(e)}", {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                })
                logger.error(tracer.get_trace_text())
            return self._error_response(request, str(e), "error")

    def _find_candidate_agents(self, intent: str) -> List[Any]:
        """Find agents that support the given intent."""
        # Try exact action match first
        candidates = self.registry.get_agents_by_action(intent)
        
        # Fallback to all agents sorted by priority if no exact match
        if not candidates:
            all_agents = self.registry.list_agents(status_filter="registered")
            candidates = sorted(all_agents, key=lambda a: a.priority, reverse=True)
        
        return candidates

    def _score_candidates(self, request: MCPRequest, candidates: List[Any], intent_match: Any) -> List[tuple]:
        """
        Score and rank candidate agents.
        
        Scoring factors:
        - Intent match confidence
        - Capability alignment
        - Agent health and load
        - Policy score
        - Cost estimate
        - Priority boost
        
        Returns list of (agent, overall_score) tuples, sorted by score descending.
        """
        scored = []

        for agent in candidates:
            score = CapabilityScore(agent_id=agent.agent_id)

            # Intent match
            score.intent_match = intent_match.confidence

            # Capability match (simplified: 1.0 if has matching action)
            has_capability = any(cap.action == intent_match.name for cap in agent.capabilities)
            score.capability_match = 0.95 if has_capability else 0.70

            # Health score (based on error rate and status)
            if agent.status == "registered":
                score.health_score = 0.95
            elif agent.status == "degraded":
                score.health_score = 0.60
            else:
                score.health_score = 0.0  # offline, skip

            # Policy score (from policy engine)
            policy_eval = self.policy_engine.evaluate_request(request)
            if agent.agent_id in policy_eval.get("blocked_agents", []):
                score.policy_score = 0.0
            else:
                score.policy_score = policy_eval.get("policy_score", 1.0)

            # Cost score (simplified: prefer lower cost)
            estimated_cost = agent.metadata.get("cost_estimate", 0.10)
            score.cost_score = 1.0 - min(estimated_cost / 1.0, 1.0)

            # Priority boost
            priority_map = {"critical": 0.20, "high": 0.10, "normal": 0.0, "low": -0.05}
            score.priority_boost = priority_map.get(request.priority, 0.0)

            # Calculate overall score (weighted sum)
            score.overall_score = (
                0.30 * score.intent_match
                + 0.25 * score.capability_match
                + 0.20 * score.health_score
                + 0.15 * score.policy_score
                + 0.05 * score.cost_score
                + score.priority_boost
            )

            if score.overall_score > 0.0 and score.health_score > 0.0:
                scored.append((agent, score.overall_score))

        return sorted(scored, key=lambda x: x[1], reverse=True)

    def _generate_plan(self, request: MCPRequest, agent: Any, intent: Any) -> ExecutionPlan:
        """Generate an execution plan for invoking the agent."""
        plan = ExecutionPlan(mode="sync")  # Start with sync; can upgrade to async based on intent

        task = ExecutionTask(
            agent_id=agent.agent_id,
            action=intent.name,
            payload={
                "text": request.text,
                "attachments": request.attachments,
                "metadata": request.metadata,
            },
            priority=request.priority,
            timeout_ms=agent.sla.get("timeout_ms", 30000),
        )

        plan.tasks.append(task)
        plan.estimated_cost = agent.metadata.get("cost_estimate", 0.10)
        plan.estimated_duration_ms = agent.sla.get("timeout_ms", 30000)

        return plan

    def _invoke_agents(self, request: MCPRequest, plan: ExecutionPlan) -> List[AgentResponse]:
        """Invoke agents according to the execution plan."""
        responses = []

        for task in plan.tasks:
            agent = self.registry.get_agent(task.agent_id)
            if not agent:
                logger.error(f"Agent {task.agent_id} not found in registry")
                continue

            response = self._invoke_single_agent(request, agent, task)
            responses.append(response)

            # Update agent health based on response
            is_healthy = response.status == "ok"
            self.registry.update_agent_health(
                agent.agent_id,
                is_healthy,
                error_msg=response.error or ""
            )

        return responses

    def _invoke_single_agent(self, request: MCPRequest, agent: Any, task: ExecutionTask) -> AgentResponse:
        """Invoke a single agent and handle response."""
        invocation = AgentInvocation(
            request_id=request.request_id,
            trace_id=request.metadata.get("trace_id", str(uuid.uuid4())),
            user_id=request.user_id,
            payload=task.payload,
            mcp_meta={
                "trace_id": request.metadata.get("trace_id"),
                "user_id": request.user_id,
                "policies": self.policy_engine.evaluate_request(request).get("matched_policies", []),
            },
            timeout_ms=task.timeout_ms,
        )

        # Apply data handling policies to payload
        invocation.payload = self.policy_engine.apply_data_handling(request, invocation.payload)

        url = f"{agent.endpoint}/invoke" if agent.endpoint.endswith("/") else f"{agent.endpoint}/invoke"

        try:
            logger.info(f"Invoking agent {agent.agent_id} at {url}")
            resp = requests.post(
                url,
                json=invocation.to_dict(),
                headers={"Content-Type": "application/json"},
                timeout=task.timeout_ms / 1000,
            )

            if resp.status_code == 200:
                response_data = resp.json()
                return AgentResponse.from_dict(response_data)
            else:
                logger.error(f"Agent {agent.agent_id} returned status {resp.status_code}")
                return AgentResponse(
                    request_id=request.request_id,
                    agent_id=agent.agent_id,
                    status="error",
                    error=f"HTTP {resp.status_code}",
                )

        except requests.Timeout:
            logger.error(f"Agent {agent.agent_id} timed out")
            return AgentResponse(
                request_id=request.request_id,
                agent_id=agent.agent_id,
                status="timeout",
                error="Agent request timed out",
            )
        except Exception as e:
            logger.error(f"Failed to invoke agent {agent.agent_id}: {e}")
            return AgentResponse(
                request_id=request.request_id,
                agent_id=agent.agent_id,
                status="error",
                error=str(e),
            )

    def _aggregate_results(self, responses: List[AgentResponse]) -> Dict[str, Any]:
        """Aggregate results from one or more agent responses."""
        if not responses:
            return {}

        # For now, return primary agent's result
        primary = responses[0]
        return {
            "agent_results": [r.to_dict() for r in responses],
            "primary_result": primary.result,
            "status": primary.status,
        }

    def _handle_suggested_actions(self, request: MCPRequest, responses: List[AgentResponse]) -> List[Dict[str, Any]]:
        """
        Process suggested actions from agents.
        
        Agents can suggest follow-up actions (e.g., escalate, create ticket).
        MCP enforces that agents do NOT call other agents directly;
        instead, MCP processes suggestions here.
        """
        escalations = []

        for response in responses:
            for action in response.suggested_actions:
                action_type = action.get("action")
                logger.info(f"Processing suggested action: {action_type}")

                if action_type == "escalate":
                    # Create escalation (could invoke support agent)
                    escalations.append(action)
                elif action_type == "create_ticket":
                    # Create support ticket
                    escalations.append(action)

        return escalations

    def _error_response(self, request: MCPRequest, error_msg: str, status: str) -> MCPResponse:
        """Generate an error response."""
        return MCPResponse(
            request_id=request.request_id,
            status=status,
            mcp_decision=MCPDecision(
                request_id=request.request_id,
                intent="unknown",
                confidence=0.0,
            ),
            error=error_msg,
            audit={"timestamp": datetime.utcnow().isoformat()},
        )

    def get_registry_summary(self) -> Dict[str, Any]:
        """Get summary of registry status."""
        agents = self.registry.list_agents()
        return {
            "total_agents": len(agents),
            "agents": [
                {
                    "agent_id": a.agent_id,
                    "status": a.status,
                    "capabilities": [c.action for c in a.capabilities],
                }
                for a in agents
            ],
        }
