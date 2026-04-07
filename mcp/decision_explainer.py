"""
Decision Explainability Module for MCP.

Provides comprehensive explanation of MCP routing decisions including:
- Why a specific agent was selected
- What context was used in the decision
- Alternative options that were considered
- Scoring breakdown for all candidates
- Decision trace logs for debugging

This module supports debug-friendly output in multiple formats:
- Structured JSON logs for machine parsing
- Human-readable text summaries
- Detailed trace reports for investigation
"""

import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


@dataclass
class ScoringFactor:
    """Individual scoring factor with explanation."""
    name: str
    value: float
    weight: float
    contribution: float
    explanation: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentScoringDetails:
    """Detailed scoring information for a single agent."""
    agent_id: str
    agent_name: str
    endpoint: str
    status: str
    
    # Scoring factors
    intent_match: ScoringFactor = field(default_factory=lambda: ScoringFactor("intent_match", 0.0, 0.30, 0.0))
    capability_match: ScoringFactor = field(default_factory=lambda: ScoringFactor("capability_match", 0.0, 0.25, 0.0))
    health_score: ScoringFactor = field(default_factory=lambda: ScoringFactor("health_score", 0.0, 0.20, 0.0))
    policy_score: ScoringFactor = field(default_factory=lambda: ScoringFactor("policy_score", 0.0, 0.15, 0.0))
    cost_score: ScoringFactor = field(default_factory=lambda: ScoringFactor("cost_score", 0.0, 0.05, 0.0))
    priority_boost: ScoringFactor = field(default_factory=lambda: ScoringFactor("priority_boost", 0.0, 1.0, 0.0))
    
    # Overall result
    overall_score: float = 0.0
    rank: int = 0
    included_in_selection: bool = False
    exclusion_reason: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "endpoint": self.endpoint,
            "status": self.status,
            "scoring_factors": {
                "intent_match": self.intent_match.to_dict(),
                "capability_match": self.capability_match.to_dict(),
                "health_score": self.health_score.to_dict(),
                "policy_score": self.policy_score.to_dict(),
                "cost_score": self.cost_score.to_dict(),
                "priority_boost": self.priority_boost.to_dict(),
            },
            "overall_score": self.overall_score,
            "rank": self.rank,
            "included_in_selection": self.included_in_selection,
            "exclusion_reason": self.exclusion_reason,
        }


@dataclass
class ContextUsed:
    """Context information used in the decision."""
    user_id: str
    session_id: str
    request_priority: str
    attachments_count: int
    metadata_keys: List[str] = field(default_factory=list)
    intent_hints_provided: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DecisionExplanation:
    """Complete explanation of an MCP decision."""
    request_id: str
    decision_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Intent detection
    detected_intent: str = ""
    intent_confidence: float = 0.0
    intent_method: str = ""  # "rule", "model", "semantic"
    intent_rationale: str = ""
    
    # Context used
    context_used: ContextUsed = field(default_factory=ContextUsed)
    
    # Scoring details
    candidate_agents: List[AgentScoringDetails] = field(default_factory=list)
    
    # Selection
    primary_agent_id: str = ""
    primary_agent_name: str = ""
    selection_reason: str = ""
    
    # Alternatives
    alternative_agents: List[Dict[str, Any]] = field(default_factory=list)
    
    # Filters applied
    policies_applied: List[str] = field(default_factory=list)
    blocked_agents: List[Tuple[str, str]] = field(default_factory=list)  # (agent_id, reason)
    
    # Metadata
    processing_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "decision_id": self.decision_id,
            "timestamp": self.timestamp,
            "intent": {
                "detected": self.detected_intent,
                "confidence": self.intent_confidence,
                "method": self.intent_method,
                "rationale": self.intent_rationale,
            },
            "context_used": self.context_used.to_dict(),
            "scoring": {
                "candidates": [c.to_dict() for c in self.candidate_agents],
            },
            "selection": {
                "primary_agent_id": self.primary_agent_id,
                "primary_agent_name": self.primary_agent_name,
                "reason": self.selection_reason,
            },
            "alternatives": self.alternative_agents,
            "filters": {
                "policies_applied": self.policies_applied,
                "blocked_agents": [{"agent_id": a[0], "reason": a[1]} for a in self.blocked_agents],
            },
            "metadata": {
                "processing_time_ms": self.processing_time_ms,
            },
        }


class DecisionExplainer:
    """
    Explains MCP decisions in detail.
    
    Usage:
        explainer = DecisionExplainer()
        explanation = explainer.explain(
            request=request,
            intent_match=intent_match,
            candidates_with_scores=[...],
            selected_agent=selected_agent,
            policies_applied=[...],
            processing_time_ms=100.0
        )
        
        # Log explanation
        explainer.log_explanation(explanation, level="info")
        
        # Get human-readable format
        text = explainer.get_text_explanation(explanation)
        print(text)
        
        # Get JSON format
        json_str = explainer.get_json_explanation(explanation)
    """
    
    def __init__(self, log_level: str = "info"):
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
    
    def explain(
        self,
        request: Any,
        intent_match: Any,
        candidates_with_scores: List[Tuple[Any, float]],
        selected_agent: Any,
        policies_applied: List[str] = None,
        blocked_agents: List[Tuple[str, str]] = None,
        processing_time_ms: float = 0.0,
    ) -> DecisionExplanation:
        """
        Create a detailed explanation of the decision.
        
        Args:
            request: MCPRequest object
            intent_match: IntentMatch object
            candidates_with_scores: List of (agent, score) tuples
            selected_agent: The selected agent
            policies_applied: List of policy names applied
            blocked_agents: List of (agent_id, reason) tuples for blocked agents
            processing_time_ms: Time spent on decision making
        
        Returns:
            DecisionExplanation object with full details
        """
        policies_applied = policies_applied or []
        blocked_agents = blocked_agents or []
        
        explanation = DecisionExplanation(
            request_id=request.request_id,
            detected_intent=intent_match.name,
            intent_confidence=intent_match.confidence,
            intent_method=intent_match.method,
            intent_rationale=intent_match.rationale,
            context_used=ContextUsed(
                user_id=request.user_id,
                session_id=request.session_id,
                request_priority=request.priority,
                attachments_count=len(request.attachments),
                metadata_keys=list(request.metadata.keys()),
                intent_hints_provided=len(request.intent_hints) > 0,
            ),
            policies_applied=policies_applied,
            blocked_agents=blocked_agents,
            processing_time_ms=processing_time_ms,
        )
        
        # Add scoring details for all candidates
        for rank, (agent, score) in enumerate(candidates_with_scores, 1):
            scoring_details = self._create_scoring_details(agent, score, rank)
            
            if agent.agent_id == selected_agent.agent_id:
                scoring_details.included_in_selection = True
                scoring_details.rank = rank
                explanation.primary_agent_id = agent.agent_id
                explanation.primary_agent_name = agent.name
                explanation.selection_reason = (
                    f"Agent selected based on highest overall score ({score:.4f}) "
                    f"from {len(candidates_with_scores)} candidates"
                )
            else:
                scoring_details.rank = rank
                scoring_details.included_in_selection = False
            
            explanation.candidate_agents.append(scoring_details)
        
        # Add alternative agents (top 2 alternatives)
        for i, (agent, score) in enumerate(candidates_with_scores[1:3], 1):
            explanation.alternative_agents.append({
                "rank": i + 1,
                "agent_id": agent.agent_id,
                "agent_name": agent.name,
                "score": score,
                "reason": f"Alternative option with score {score:.4f}",
            })
        
        return explanation
    
    def _create_scoring_details(self, agent: Any, overall_score: float, rank: int) -> AgentScoringDetails:
        """Create detailed scoring information for an agent."""
        details = AgentScoringDetails(
            agent_id=agent.agent_id,
            agent_name=agent.name,
            endpoint=agent.endpoint,
            status=agent.status,
            overall_score=overall_score,
            rank=rank,
        )
        
        # Note: In practice, we'd get these values from the actual scoring
        # For now, we're showing the structure; the decision engine would
        # populate these with actual values
        
        return details
    
    def log_explanation(
        self,
        explanation: DecisionExplanation,
        level: str = "info",
        include_scoring: bool = True,
    ) -> None:
        """
        Log the explanation in structured format.
        
        Args:
            explanation: The DecisionExplanation object
            level: Logging level ("debug", "info", "warning", "error")
            include_scoring: Whether to include detailed scoring breakdown
        """
        log_level = getattr(logging, level.upper(), logging.INFO)
        
        # Build log entry
        log_entry = {
            "event": "decision_made",
            "request_id": explanation.request_id,
            "decision_id": explanation.decision_id,
            "timestamp": explanation.timestamp,
            "intent": explanation.detected_intent,
            "intent_confidence": explanation.intent_confidence,
            "selected_agent": explanation.primary_agent_id,
            "num_candidates": len(explanation.candidate_agents),
            "num_alternatives": len(explanation.alternative_agents),
            "processing_time_ms": explanation.processing_time_ms,
        }
        
        if include_scoring:
            log_entry["scoring"] = {
                agent.agent_id: {
                    "score": agent.overall_score,
                    "rank": agent.rank,
                    "status": agent.status,
                }
                for agent in explanation.candidate_agents
            }
        
        logger.log(log_level, json.dumps(log_entry))
    
    def get_text_explanation(self, explanation: DecisionExplanation, verbose: bool = False) -> str:
        """
        Get human-readable text explanation.
        
        Args:
            explanation: The DecisionExplanation object
            verbose: Whether to include detailed scoring breakdown
        
        Returns:
            Formatted text explanation
        """
        lines = []
        
        lines.append("=" * 80)
        lines.append("MCP DECISION EXPLANATION")
        lines.append("=" * 80)
        lines.append("")
        
        # Header
        lines.append(f"Request ID:        {explanation.request_id}")
        lines.append(f"Decision ID:       {explanation.decision_id}")
        lines.append(f"Timestamp:         {explanation.timestamp}")
        lines.append(f"Processing Time:   {explanation.processing_time_ms:.2f}ms")
        lines.append("")
        
        # Intent Detection
        lines.append("INTENT DETECTION")
        lines.append("-" * 80)
        lines.append(f"Detected Intent:   {explanation.detected_intent}")
        lines.append(f"Confidence:        {explanation.intent_confidence:.2%}")
        lines.append(f"Method:            {explanation.intent_method}")
        if explanation.intent_rationale:
            lines.append(f"Rationale:         {explanation.intent_rationale}")
        lines.append("")
        
        # Context Used
        lines.append("CONTEXT USED")
        lines.append("-" * 80)
        ctx = explanation.context_used
        lines.append(f"User ID:           {ctx.user_id}")
        lines.append(f"Session ID:        {ctx.session_id}")
        lines.append(f"Request Priority:  {ctx.request_priority}")
        lines.append(f"Attachments:       {ctx.attachments_count}")
        if ctx.metadata_keys:
            lines.append(f"Metadata Keys:     {', '.join(ctx.metadata_keys)}")
        lines.append(f"Intent Hints:      {'Yes' if ctx.intent_hints_provided else 'No'}")
        lines.append("")
        
        # Selection Decision
        lines.append("SELECTION DECISION")
        lines.append("-" * 80)
        lines.append(f"Selected Agent:    {explanation.primary_agent_id} ({explanation.primary_agent_name})")
        lines.append(f"Reason:            {explanation.selection_reason}")
        lines.append("")
        
        # Alternative Options
        if explanation.alternative_agents:
            lines.append("ALTERNATIVE OPTIONS CONSIDERED")
            lines.append("-" * 80)
            for alt in explanation.alternative_agents:
                lines.append(
                    f"  {alt['rank']}. {alt['agent_id']} ({alt['agent_name']}) "
                    f"- Score: {alt['score']:.4f}"
                )
            lines.append("")
        
        # Scoring Breakdown
        if verbose and explanation.candidate_agents:
            lines.append("DETAILED SCORING BREAKDOWN")
            lines.append("-" * 80)
            for agent in sorted(explanation.candidate_agents, key=lambda a: a.rank):
                lines.append(f"\n  {agent.rank}. {agent.agent_id} ({agent.agent_name})")
                lines.append(f"     Status: {agent.status}")
                lines.append(f"     Overall Score: {agent.overall_score:.4f}")
                
                if agent.included_in_selection:
                    lines.append(f"     ✓ SELECTED")
                else:
                    if agent.exclusion_reason:
                        lines.append(f"     Excluded: {agent.exclusion_reason}")
                    else:
                        lines.append(f"     Not selected (lower score)")
                
                # Scoring factors
                lines.append(f"     Scoring Factors:")
                for factor in [
                    agent.intent_match,
                    agent.capability_match,
                    agent.health_score,
                    agent.policy_score,
                    agent.cost_score,
                    agent.priority_boost,
                ]:
                    lines.append(
                        f"       • {factor.name:20s}: {factor.value:.4f} "
                        f"(weight {factor.weight:.0%}, contrib {factor.contribution:.4f})"
                    )
                    if factor.explanation:
                        lines.append(f"         → {factor.explanation}")
            lines.append("")
        
        # Policies Applied
        if explanation.policies_applied:
            lines.append("POLICIES APPLIED")
            lines.append("-" * 80)
            for policy in explanation.policies_applied:
                lines.append(f"  • {policy}")
            lines.append("")
        
        # Blocked Agents
        if explanation.blocked_agents:
            lines.append("AGENTS BLOCKED BY POLICY")
            lines.append("-" * 80)
            for agent_id, reason in explanation.blocked_agents:
                lines.append(f"  • {agent_id}: {reason}")
            lines.append("")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def get_json_explanation(self, explanation: DecisionExplanation) -> str:
        """
        Get JSON-formatted explanation suitable for logging/APIs.
        
        Args:
            explanation: The DecisionExplanation object
        
        Returns:
            JSON string with full explanation
        """
        return json.dumps(explanation.to_dict(), indent=2)
    
    def get_debug_report(self, explanation: DecisionExplanation) -> Dict[str, Any]:
        """
        Get explanation as structured dict for debugging tools.
        
        Args:
            explanation: The DecisionExplanation object
        
        Returns:
            Dictionary with complete explanation data
        """
        return explanation.to_dict()
    
    def log_decision_trace(
        self,
        explanation: DecisionExplanation,
        include_alternatives: bool = True,
    ) -> None:
        """
        Log a complete decision trace for audit/debugging.
        
        Args:
            explanation: The DecisionExplanation object
            include_alternatives: Whether to log alternative options
        """
        # Log main decision
        logger.info(
            f"DECISION: Request {explanation.request_id} → "
            f"Agent {explanation.primary_agent_id} "
            f"(Intent: {explanation.detected_intent} @ {explanation.intent_confidence:.0%})"
        )
        
        # Log context
        ctx = explanation.context_used
        logger.debug(
            f"CONTEXT: User {ctx.user_id}, Priority {ctx.request_priority}, "
            f"Attachments {ctx.attachments_count}, Metadata keys {len(ctx.metadata_keys)}"
        )
        
        # Log scoring
        for agent in explanation.candidate_agents:
            logger.debug(
                f"SCORE: {agent.agent_id:30s} → {agent.overall_score:.4f} "
                f"(rank {agent.rank}/{len(explanation.candidate_agents)})"
            )
        
        # Log alternatives
        if include_alternatives and explanation.alternative_agents:
            for alt in explanation.alternative_agents:
                logger.debug(
                    f"ALT: {alt['agent_id']:30s} → {alt['score']:.4f} ({alt['reason']})"
                )
        
        # Log policies
        if explanation.policies_applied:
            logger.debug(f"POLICIES: {', '.join(explanation.policies_applied)}")
        
        if explanation.blocked_agents:
            for agent_id, reason in explanation.blocked_agents:
                logger.warning(f"BLOCKED: {agent_id} - {reason}")


class DecisionTracer:
    """
    Real-time tracing of decision-making process.
    
    Captures each step of the decision process for debugging and auditing.
    """
    
    def __init__(self):
        self.events: List[Dict[str, Any]] = []
        self.start_time = datetime.utcnow()
    
    def record_event(
        self,
        event_type: str,
        description: str,
        details: Dict[str, Any] = None,
    ) -> None:
        """
        Record a decision process event.
        
        Args:
            event_type: Type of event (e.g., "intent_detected", "agent_scored")
            description: Human-readable description
            details: Additional event details
        """
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "elapsed_ms": (datetime.utcnow() - self.start_time).total_seconds() * 1000,
            "type": event_type,
            "description": description,
        }
        
        if details:
            event["details"] = details
        
        self.events.append(event)
        logger.debug(f"[{event_type}] {description}")
    
    def get_trace(self) -> List[Dict[str, Any]]:
        """Get the complete event trace."""
        return self.events
    
    def get_trace_text(self) -> str:
        """Get formatted trace as text."""
        lines = []
        lines.append("=" * 80)
        lines.append("DECISION TRACE")
        lines.append("=" * 80)
        
        for event in self.events:
            elapsed = event.get("elapsed_ms", 0)
            lines.append(f"[{elapsed:8.2f}ms] {event['type']:20s} - {event['description']}")
            
            if "details" in event:
                for key, value in event["details"].items():
                    if isinstance(value, (dict, list)):
                        value_str = json.dumps(value, indent=2)
                    else:
                        value_str = str(value)
                    lines.append(f"            {key}: {value_str}")
        
        lines.append("=" * 80)
        return "\n".join(lines)
