"""
MCP Decision Explainability Examples

This module demonstrates how to use the MCP decision explainability system
to understand, debug, and audit MCP routing decisions.

Examples include:
1. Basic explanation generation
2. Human-readable output
3. JSON export for logging
4. Decision trace analysis
5. Debugging low-confidence decisions
6. Audit trail generation
7. Scoring analysis
8. Policy impact analysis
"""

import json
from datetime import datetime
from typing import Dict, List, Tuple
from mcp.models import MCPRequest, MCPResponse
from mcp.decision_explainer import (
    DecisionExplainer,
    DecisionExplanation,
    DecisionTracer,
    ScoringFactor,
    AgentScoringDetails,
    ContextUsed
)

# ============================================================================
# EXAMPLE 1: Basic Explanation Generation
# ============================================================================

def example_1_basic_explanation():
    """Generate a basic explanation for a routing decision."""
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Explanation Generation")
    print("="*80)
    
    # Create explainer
    explainer = DecisionExplainer()
    
    # Create a request
    request = MCPRequest(
        request_id="ex1-001",
        user_id="user-001",
        text="I need help with my billing account",
        priority="normal"
    )
    
    print(f"✓ Example setup complete")
    print(f"  Request ID: {request.request_id}")
    print(f"  User ID: {request.user_id}")
    print(f"  Text: {request.text}")
    print(f"  Priority: {request.priority}")
    print(f"\n✓ DecisionExplainer is ready to use!")
    print(f"  To use: engine = MCPDecisionEngine(..., enable_explainability=True)")

# ============================================================================
# EXAMPLE 2: Tracer - Event Recording
# ============================================================================

def example_2_tracer_events():
    """Demonstrate real-time event tracing."""
    print("\n" + "="*80)
    print("EXAMPLE 2: Tracer - Real-Time Event Recording")
    print("="*80)
    
    tracer = DecisionTracer()
    
    print("✓ Recording decision events...")
    
    tracer.record_event(
        event_type="request_received",
        description="Request received from user-123"
    )
    
    tracer.record_event(
        event_type="intent_detection_start",
        description="Starting intent detection"
    )
    
    tracer.record_event(
        event_type="intent_detected",
        description="Detected intent: account_access (95% confidence)"
    )
    
    tracer.record_event(
        event_type="scoring_complete",
        description="Scoring complete - top: account-agent (0.94)"
    )
    
    tracer.record_event(
        event_type="agent_invocation_complete",
        description="Agent invocation complete"
    )
    
    # Get trace
    trace_text = tracer.get_trace_text()
    print("\n✓ Event Trace:\n")
    print(trace_text)

# ============================================================================
# EXAMPLE 3: JSON Export for Logging
# ============================================================================

def example_3_json_export():
    """Export explanation as JSON for logging systems."""
    print("\n" + "="*80)
    print("EXAMPLE 3: JSON Export for Logging")
    print("="*80)
    
    explainer = DecisionExplainer()
    
    request = MCPRequest(
        request_id="ex3-001",
        user_id="user-456",
        text="Can you help me with a refund?",
        priority="normal"
    )
    
    explanation = explainer.explain(
        request=request,
        intent_match=("refund_request", 0.88, "model"),
        candidates_with_scores=[
            ("finance-agent", 0.91),
            ("support-agent", 0.76),
        ],
        selected_agent="finance-agent",
        policies_applied=[],
        processing_time_ms=110.0
    )
    
    # Export as JSON
    json_exp = explainer.get_json_explanation(explanation)
    print("JSON Export (first 500 chars):")
    print(json.dumps(json.loads(json_exp), indent=2)[:500] + "...")
    
    print("\n✓ Full JSON saved, ready for logging systems")

# ============================================================================
# EXAMPLE 4: Decision Trace Analysis
# ============================================================================

def example_4_decision_trace():
    """Analyze the step-by-step decision trace."""
    print("\n" + "="*80)
    print("EXAMPLE 4: Decision Trace Analysis")
    print("="*80)
    
    tracer = DecisionTracer()
    
    # Simulate decision steps
    tracer.record_event(
        event_type="request_received",
        description="Received support request",
        details={"user_id": "user-789", "priority": "high"}
    )
    
    tracer.record_event(
        event_type="intent_detection_start",
        description="Starting intent detection"
    )
    
    tracer.record_event(
        event_type="intent_detected",
        description="Intent: support with 87% confidence",
        details={"intent": "support", "confidence": 0.87}
    )
    
    tracer.record_event(
        event_type="candidate_search_start",
        description="Searching for candidate agents"
    )
    
    tracer.record_event(
        event_type="candidates_found",
        description="Found 5 candidates",
        details={"count": 5}
    )
    
    tracer.record_event(
        event_type="scoring_complete",
        description="Scoring complete",
        details={"top_score": 0.91, "agent": "support-agent"}
    )
    
    tracer.record_event(
        event_type="agent_invocation_complete",
        description="Agent invocation complete"
    )
    
    # Get trace
    trace_text = tracer.get_trace_text()
    print(trace_text)

# ============================================================================
# EXAMPLE 5: Debugging Low-Confidence Decisions
# ============================================================================

def example_5_debug_low_confidence():
    """Debug decisions with low intent confidence."""
    print("\n" + "="*80)
    print("EXAMPLE 5: Debugging Low-Confidence Decisions")
    print("="*80)
    
    explainer = DecisionExplainer()
    
    # Scenario: Ambiguous request
    request = MCPRequest(
        request_id="ex5-001",
        user_id="user-999",
        text="help",  # Very vague request
        priority="normal"
    )
    
    explanation = explainer.explain(
        request=request,
        intent_match=("general_support", 0.62, "model"),  # Low confidence!
        candidates_with_scores=[
            ("support-agent", 0.70),
            ("billing-agent", 0.58),
            ("account-agent", 0.55),
        ],
        selected_agent="support-agent",
        policies_applied=[],
        processing_time_ms=180.0
    )
    
    # Debug output
    print(f"⚠️  Low Confidence Decision Detected!")
    print(f"   Intent Confidence: {explanation.intent_confidence:.1%}")
    print(f"   Intent: {explanation.detected_intent}")
    print(f"   Method: {explanation.intent_method}")
    print(f"   Rationale: {explanation.intent_rationale}")
    
    print(f"\n📊 Scoring Breakdown:")
    for agent in explanation.candidate_agents[:3]:
        print(f"   {agent.agent_id}: {agent.overall_score:.4f}")
    
    print(f"\n💡 Recommendations:")
    print(f"   1. Request text is too vague: '{request.text}'")
    print(f"   2. All agent scores are low (0.70 max)")
    print(f"   3. Consider asking user for clarification")
    print(f"   4. Or enable intent hints feature")

# ============================================================================
# EXAMPLE 6: Audit Trail Generation
# ============================================================================

def example_6_audit_trail():
    """Generate audit trail for compliance."""
    print("\n" + "="*80)
    print("EXAMPLE 6: Audit Trail Generation")
    print("="*80)
    
    explainer = DecisionExplainer()
    
    # Scenario: Premium customer request (for audit purposes)
    request = MCPRequest(
        request_id="ex6-001",
        user_id="premium-customer-001",
        text="I need priority support",
        priority="high",
        metadata={"customer_type": "premium", "contract_id": "CTR-2024-001"}
    )
    
    explanation = explainer.explain(
        request=request,
        intent_match=("support_request", 0.91, "model"),
        candidates_with_scores=[
            ("premium-support-agent", 0.98),
            ("support-agent", 0.75),
        ],
        selected_agent="premium-support-agent",
        policies_applied=["premium_customer_policy", "priority_routing"],
        processing_time_ms=85.3
    )
    
    # Create audit record
    audit_record = {
        "audit_timestamp": datetime.now().isoformat(),
        "request_id": explanation.request_id,
        "decision_id": explanation.decision_id,
        "user_id": request.user_id,
        "selected_agent": explanation.primary_agent_id,
        "policies_applied": explanation.policies_applied,
        "intent": explanation.detected_intent,
        "intent_confidence": explanation.intent_confidence,
        "processing_time_ms": explanation.processing_time_ms,
        "metadata": request.metadata
    }
    
    print("✓ Audit Record Created:")
    print(json.dumps(audit_record, indent=2))
    
    print("\n✓ Ready to save to audit database/file")

# ============================================================================
# EXAMPLE 7: Scoring Factor Analysis
# ============================================================================

def example_7_scoring_analysis():
    """Analyze individual scoring factors."""
    print("\n" + "="*80)
    print("EXAMPLE 7: Scoring Factor Analysis")
    print("="*80)
    
    explainer = DecisionExplainer()
    
    request = MCPRequest(
        request_id="ex7-001",
        user_id="user-111",
        text="I need technical support for my account",
        priority="normal"
    )
    
    explanation = explainer.explain(
        request=request,
        intent_match=("technical_support", 0.89, "model"),
        candidates_with_scores=[
            ("technical-agent", 0.93),
            ("support-agent", 0.81),
        ],
        selected_agent="technical-agent",
        policies_applied=[],
        processing_time_ms=92.5
    )
    
    # Analyze top candidate
    if explanation.candidate_agents:
        top_agent = explanation.candidate_agents[0]
        print(f"Agent: {top_agent.agent_name} ({top_agent.agent_id})")
        print(f"Overall Score: {top_agent.overall_score:.4f}")
        print(f"\nScoring Factors:")
        
        for factor in top_agent.scoring_factors:
            contribution_pct = factor.contribution * 100
            print(f"  {factor.name:20s} | Value: {factor.value:.4f} | "
                  f"Weight: {factor.weight*100:5.1f}% | "
                  f"Contrib: {contribution_pct:5.2f}% | {factor.explanation}")
        
        # Find strongest and weakest factors
        if top_agent.scoring_factors:
            strongest = max(top_agent.scoring_factors, 
                          key=lambda f: f.contribution)
            weakest = min(top_agent.scoring_factors, 
                         key=lambda f: f.contribution)
            
            print(f"\n💪 Strongest Factor: {strongest.name} ({strongest.value:.4f})")
            print(f"   Contributes {strongest.contribution*100:.2f}% to final score")
            
            print(f"\n⚠️  Weakest Factor: {weakest.name} ({weakest.value:.4f})")
            print(f"   Contributes {weakest.contribution*100:.2f}% to final score")

# ============================================================================
# EXAMPLE 8: Policy Impact Analysis
# ============================================================================

def example_8_policy_impact():
    """Analyze how policies affect decisions."""
    print("\n" + "="*80)
    print("EXAMPLE 8: Policy Impact Analysis")
    print("="*80)
    
    explainer = DecisionExplainer()
    
    request = MCPRequest(
        request_id="ex8-001",
        user_id="enterprise-customer",
        text="Need enterprise support",
        priority="high",
        metadata={"account_type": "enterprise", "sla_level": "24/7"}
    )
    
    explanation = explainer.explain(
        request=request,
        intent_match=("enterprise_support", 0.96, "model"),
        candidates_with_scores=[
            ("enterprise-agent", 0.95),
            ("premium-agent", 0.82),
            ("standard-agent", 0.60),
        ],
        selected_agent="enterprise-agent",
        policies_applied=[
            "enterprise_account_policy",
            "high_priority_routing",
            "sla_compliance_policy"
        ],
        blocked_agents=[
            ("standard-agent", "Enterprise customers cannot use standard agents"),
            ("free-tier-agent", "Not available for enterprise accounts")
        ],
        processing_time_ms=72.1
    )
    
    print(f"✓ Policies Applied: {len(explanation.policies_applied)}")
    for policy in explanation.policies_applied:
        print(f"  • {policy}")
    
    print(f"\n✓ Agents Blocked by Policy: {len(explanation.blocked_agents)}")
    for agent_id, reason in explanation.blocked_agents:
        print(f"  • {agent_id}: {reason}")
    
    print(f"\n📊 Decision Impact:")
    print(f"  Without policies: {explanation.candidate_agents[1].agent_id} "
          f"(score: {explanation.candidate_agents[1].overall_score:.4f})")
    print(f"  With policies: {explanation.primary_agent_id} "
          f"(score: {explanation.candidate_agents[0].overall_score:.4f})")
    print(f"  Policy ensured: Correct tier matching for enterprise customer")

# ============================================================================
# EXAMPLE 9: Comparison Analysis
# ============================================================================

def example_9_comparison_analysis():
    """Compare multiple decision explanations."""
    print("\n" + "="*80)
    print("EXAMPLE 9: Comparison Analysis (Same Request, Different Scenarios)")
    print("="*80)
    
    explainer = DecisionExplainer()
    
    # Scenario A: Normal priority
    request_normal = MCPRequest(
        request_id="ex9-001a",
        user_id="user-normal",
        text="Can you help me?",
        priority="normal"
    )
    
    explanation_normal = explainer.explain(
        request=request_normal,
        intent_match=("general_support", 0.80, "model"),
        candidates_with_scores=[
            ("general-agent", 0.80),
            ("support-agent", 0.75),
        ],
        selected_agent="general-agent",
        policies_applied=[],
        processing_time_ms=95.0
    )
    
    # Scenario B: High priority
    request_high = MCPRequest(
        request_id="ex9-001b",
        user_id="user-vip",
        text="Can you help me?",
        priority="high"
    )
    
    explanation_high = explainer.explain(
        request=request_high,
        intent_match=("general_support", 0.80, "model"),
        candidates_with_scores=[
            ("vip-agent", 0.85),
            ("support-agent", 0.75),
        ],
        selected_agent="vip-agent",
        policies_applied=["vip_customer_routing"],
        processing_time_ms=92.0
    )
    
    print("Comparison: Same request text, different priority\n")
    
    print("SCENARIO A: Normal Priority")
    print(f"  Selected: {explanation_normal.primary_agent_id}")
    print(f"  Confidence: {explanation_normal.intent_confidence:.1%}")
    print(f"  Policies: {len(explanation_normal.policies_applied)}")
    
    print("\nSCENARIO B: High Priority")
    print(f"  Selected: {explanation_high.primary_agent_id}")
    print(f"  Confidence: {explanation_high.intent_confidence:.1%}")
    print(f"  Policies: {len(explanation_high.policies_applied)}")
    
    print("\n📊 Analysis:")
    print(f"  Priority change → Different agent selected")
    print(f"  Normal:  {explanation_normal.primary_agent_id}")
    print(f"  High:    {explanation_high.primary_agent_id}")
    print(f"  Policy impact: {explanation_high.policies_applied[0]}")

# ============================================================================
# EXAMPLE 10: Integration with Logging
# ============================================================================

def example_10_logging_integration():
    """Integrate explanations with application logging."""
    print("\n" + "="*80)
    print("EXAMPLE 10: Logging Integration")
    print("="*80)
    
    import logging
    
    # Setup logging
    logger = logging.getLogger("mcp.decisions")
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    explainer = DecisionExplainer(log_level="info")
    
    request = MCPRequest(
        request_id="ex10-001",
        user_id="user-logging",
        text="Test logging integration",
        priority="normal"
    )
    
    explanation = explainer.explain(
        request=request,
        intent_match=("test", 0.90, "model"),
        candidates_with_scores=[("test-agent", 0.90)],
        selected_agent="test-agent",
        policies_applied=[],
        processing_time_ms=50.0
    )
    
    print("✓ Logging explanation...")
    explainer.log_explanation(explanation, level="info")
    
    print("\n✓ Explanation logged to logger")
    print("   Check logs for:")
    print("   - Decision ID")
    print("   - Selected agent")
    print("   - Intent and confidence")
    print("   - Processing time")

# ============================================================================
# Main: Run All Examples
# ============================================================================

def main():
    """Run all examples."""
    print("\n" + "="*80)
    print("MCP DECISION EXPLAINABILITY - EXAMPLES")
    print("="*80)
    
    example_1_basic_explanation()
    example_2_tracer_events()
    
    print("\n" + "="*80)
    print("✓ Examples completed!")
    print("="*80)
    print("\nNext steps:")
    print("1. The DecisionExplainer is integrated with MCPDecisionEngine")
    print("2. Enable with: enable_explainability=True")
    print("3. Process requests normally - explanations are automatic")
    print("4. Get explanation from: response.metadata['decision_explanation']")
    print("\nDocumentation:")
    print("- Quick Start: MCP_DECISION_EXPLAINABILITY_README.md")
    print("- Full Guide: MCP_DECISION_EXPLAINABILITY_GUIDE.md")
    print("- Navigation: MCP_DECISION_EXPLAINABILITY_MASTER_INDEX.md")

if __name__ == "__main__":
    main()
