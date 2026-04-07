"""
Unit Tests for MCP Decision Explainability

Tests for the decision explainer and tracer modules.
"""

import unittest
import json
from datetime import datetime
from mcp.decision_explainer import (
    DecisionExplainer,
    DecisionTracer,
    ScoringFactor,
    AgentScoringDetails,
    ContextUsed,
    DecisionExplanation
)
from mcp.models import MCPRequest


class TestDecisionTracer(unittest.TestCase):
    """Tests for DecisionTracer class."""
    
    def test_tracer_initialization(self):
        """Test tracer initialization."""
        tracer = DecisionTracer()
        self.assertIsNotNone(tracer)
        self.assertEqual(len(tracer.get_trace()), 0)
    
    def test_record_event(self):
        """Test recording a single event."""
        tracer = DecisionTracer()
        tracer.record_event(
            event_type="test_event",
            description="Test description"
        )
        trace = tracer.get_trace()
        self.assertEqual(len(trace), 1)
        self.assertEqual(trace[0]['event_type'], "test_event")
        self.assertEqual(trace[0]['description'], "Test description")
    
    def test_multiple_events(self):
        """Test recording multiple events."""
        tracer = DecisionTracer()
        for i in range(5):
            tracer.record_event(
                event_type=f"event_{i}",
                description=f"Description {i}"
            )
        trace = tracer.get_trace()
        self.assertEqual(len(trace), 5)
    
    def test_event_timestamp(self):
        """Test that events have timestamps."""
        tracer = DecisionTracer()
        tracer.record_event("test", "Test event")
        trace = tracer.get_trace()
        self.assertIn('elapsed_ms', trace[0])
        self.assertGreaterEqual(trace[0]['elapsed_ms'], 0)
    
    def test_event_details(self):
        """Test recording event with details."""
        tracer = DecisionTracer()
        details = {"key": "value", "number": 42}
        tracer.record_event(
            event_type="test",
            description="Test",
            details=details
        )
        trace = tracer.get_trace()
        self.assertEqual(trace[0]['details'], details)
    
    def test_trace_text_output(self):
        """Test trace text output format."""
        tracer = DecisionTracer()
        tracer.record_event("event1", "First event")
        tracer.record_event("event2", "Second event")
        trace_text = tracer.get_trace_text()
        
        self.assertIn("event1", trace_text)
        self.assertIn("event2", trace_text)
        self.assertIn("ms", trace_text)
    
    def test_elapsed_time_progression(self):
        """Test that elapsed time increases with each event."""
        import time
        tracer = DecisionTracer()
        
        tracer.record_event("event1", "First")
        time.sleep(0.01)
        tracer.record_event("event2", "Second")
        
        trace = tracer.get_trace()
        self.assertLess(trace[0]['elapsed_ms'], trace[1]['elapsed_ms'])


class TestScoringFactor(unittest.TestCase):
    """Tests for ScoringFactor dataclass."""
    
    def test_scoring_factor_creation(self):
        """Test creating a scoring factor."""
        factor = ScoringFactor(
            name="test_factor",
            value=0.85,
            weight=0.30,
            contribution=0.255,
            explanation="Test explanation"
        )
        self.assertEqual(factor.name, "test_factor")
        self.assertEqual(factor.value, 0.85)
        self.assertEqual(factor.weight, 0.30)
    
    def test_scoring_factor_dict_conversion(self):
        """Test converting factor to dict."""
        factor = ScoringFactor(
            name="test",
            value=0.9,
            weight=0.5,
            contribution=0.45,
            explanation="Test"
        )
        factor_dict = factor.__dict__
        self.assertIn('name', factor_dict)
        self.assertIn('value', factor_dict)


class TestDecisionExplainer(unittest.TestCase):
    """Tests for DecisionExplainer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.explainer = DecisionExplainer()
        self.request = MCPRequest(
            request_id="test-001",
            user_id="user-001",
            text="Test request",
            priority="normal"
        )
    
    def test_explainer_initialization(self):
        """Test explainer initialization."""
        explainer = DecisionExplainer()
        self.assertIsNotNone(explainer)
    
    def test_explain_generates_explanation(self):
        """Test that explain() generates an explanation."""
        explanation = self.explainer.explain(
            request=self.request,
            intent_match=("test_intent", 0.95, "model"),
            candidates_with_scores=[
                ("agent1", 0.90),
                ("agent2", 0.85)
            ],
            selected_agent="agent1",
            policies_applied=[],
            processing_time_ms=100.0
        )
        
        self.assertIsNotNone(explanation)
        self.assertEqual(explanation.request_id, "test-001")
        self.assertEqual(explanation.detected_intent, "test_intent")
        self.assertEqual(explanation.primary_agent_id, "agent1")
    
    def test_explanation_has_request_id(self):
        """Test explanation contains request ID."""
        explanation = self.explainer.explain(
            request=self.request,
            intent_match=("test", 0.9, "model"),
            candidates_with_scores=[("agent1", 0.9)],
            selected_agent="agent1",
            policies_applied=[],
            processing_time_ms=50.0
        )
        self.assertEqual(explanation.request_id, "test-001")
    
    def test_explanation_has_decision_id(self):
        """Test explanation has unique decision ID."""
        explanation = self.explainer.explain(
            request=self.request,
            intent_match=("test", 0.9, "model"),
            candidates_with_scores=[("agent1", 0.9)],
            selected_agent="agent1",
            policies_applied=[],
            processing_time_ms=50.0
        )
        self.assertIsNotNone(explanation.decision_id)
        self.assertTrue(len(explanation.decision_id) > 0)
    
    def test_get_text_explanation_format(self):
        """Test text explanation format."""
        explanation = self.explainer.explain(
            request=self.request,
            intent_match=("test_intent", 0.85, "model"),
            candidates_with_scores=[("agent1", 0.90)],
            selected_agent="agent1",
            policies_applied=[],
            processing_time_ms=75.0
        )
        
        text = self.explainer.get_text_explanation(explanation, verbose=False)
        self.assertIsInstance(text, str)
        self.assertIn("test-001", text)
        self.assertIn("agent1", text)
    
    def test_get_json_explanation_format(self):
        """Test JSON explanation format."""
        explanation = self.explainer.explain(
            request=self.request,
            intent_match=("test", 0.9, "model"),
            candidates_with_scores=[("agent1", 0.9)],
            selected_agent="agent1",
            policies_applied=[],
            processing_time_ms=50.0
        )
        
        json_str = self.explainer.get_json_explanation(explanation)
        self.assertIsInstance(json_str, str)
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        self.assertIsInstance(parsed, dict)
        self.assertEqual(parsed['request_id'], "test-001")
    
    def test_get_debug_report_format(self):
        """Test debug report format."""
        explanation = self.explainer.explain(
            request=self.request,
            intent_match=("test", 0.9, "model"),
            candidates_with_scores=[("agent1", 0.9)],
            selected_agent="agent1",
            policies_applied=[],
            processing_time_ms=50.0
        )
        
        report = self.explainer.get_debug_report(explanation)
        self.assertIsInstance(report, dict)
        self.assertEqual(report['request_id'], "test-001")
    
    def test_explanation_with_policies(self):
        """Test explanation with policies applied."""
        explanation = self.explainer.explain(
            request=self.request,
            intent_match=("test", 0.9, "model"),
            candidates_with_scores=[("agent1", 0.9)],
            selected_agent="agent1",
            policies_applied=["policy1", "policy2"],
            processing_time_ms=50.0
        )
        
        self.assertEqual(len(explanation.policies_applied), 2)
        self.assertIn("policy1", explanation.policies_applied)
    
    def test_explanation_with_blocked_agents(self):
        """Test explanation with blocked agents."""
        explanation = self.explainer.explain(
            request=self.request,
            intent_match=("test", 0.9, "model"),
            candidates_with_scores=[
                ("agent1", 0.9),
                ("agent2", 0.8)
            ],
            selected_agent="agent1",
            policies_applied=[],
            blocked_agents=[("agent2", "Blocked by policy")],
            processing_time_ms=50.0
        )
        
        self.assertEqual(len(explanation.blocked_agents), 1)
        self.assertEqual(explanation.blocked_agents[0][0], "agent2")
    
    def test_intent_confidence_captured(self):
        """Test intent confidence is captured."""
        explanation = self.explainer.explain(
            request=self.request,
            intent_match=("test", 0.75, "model"),
            candidates_with_scores=[("agent1", 0.9)],
            selected_agent="agent1",
            policies_applied=[],
            processing_time_ms=50.0
        )
        
        self.assertAlmostEqual(explanation.intent_confidence, 0.75)
    
    def test_processing_time_captured(self):
        """Test processing time is captured."""
        explanation = self.explainer.explain(
            request=self.request,
            intent_match=("test", 0.9, "model"),
            candidates_with_scores=[("agent1", 0.9)],
            selected_agent="agent1",
            policies_applied=[],
            processing_time_ms=123.45
        )
        
        self.assertAlmostEqual(explanation.processing_time_ms, 123.45)
    
    def test_candidate_agents_captured(self):
        """Test that candidate agents are captured."""
        explanation = self.explainer.explain(
            request=self.request,
            intent_match=("test", 0.9, "model"),
            candidates_with_scores=[
                ("agent1", 0.95),
                ("agent2", 0.87),
                ("agent3", 0.65)
            ],
            selected_agent="agent1",
            policies_applied=[],
            processing_time_ms=50.0
        )
        
        self.assertGreaterEqual(len(explanation.candidate_agents), 1)
        # First agent should be top scorer
        self.assertEqual(explanation.candidate_agents[0].agent_id, "agent1")
    
    def test_verbose_vs_concise_text(self):
        """Test verbose vs concise text output."""
        explanation = self.explainer.explain(
            request=self.request,
            intent_match=("test", 0.9, "model"),
            candidates_with_scores=[("agent1", 0.9)],
            selected_agent="agent1",
            policies_applied=[],
            processing_time_ms=50.0
        )
        
        verbose = self.explainer.get_text_explanation(explanation, verbose=True)
        concise = self.explainer.get_text_explanation(explanation, verbose=False)
        
        # Verbose should generally be longer
        self.assertGreater(len(verbose), len(concise))


class TestDecisionExplanationDataModel(unittest.TestCase):
    """Tests for DecisionExplanation dataclass."""
    
    def test_context_used_creation(self):
        """Test creating ContextUsed object."""
        context = ContextUsed(
            user_id="user-001",
            session_id="sess-001",
            request_priority="high",
            attachments_count=2,
            metadata_keys=["key1", "key2"],
            intent_hints_provided=True
        )
        self.assertEqual(context.user_id, "user-001")
        self.assertEqual(context.request_priority, "high")
        self.assertEqual(context.attachments_count, 2)
    
    def test_agent_scoring_details_creation(self):
        """Test creating AgentScoringDetails."""
        factors = [
            ScoringFactor("factor1", 0.9, 0.3, 0.27, "Test"),
            ScoringFactor("factor2", 0.8, 0.7, 0.56, "Test"),
        ]
        
        agent = AgentScoringDetails(
            agent_id="agent-001",
            agent_name="Test Agent",
            endpoint="http://test:8000",
            status="registered",
            scoring_factors=factors,
            overall_score=0.83,
            rank=1
        )
        
        self.assertEqual(agent.agent_id, "agent-001")
        self.assertEqual(agent.overall_score, 0.83)
        self.assertEqual(len(agent.scoring_factors), 2)


class TestIntegration(unittest.TestCase):
    """Integration tests."""
    
    def test_end_to_end_explanation_flow(self):
        """Test complete explanation generation flow."""
        explainer = DecisionExplainer()
        tracer = DecisionTracer()
        
        # Simulate request
        request = MCPRequest(
            request_id="integration-001",
            user_id="user-001",
            text="Test request",
            priority="normal"
        )
        
        # Record events
        tracer.record_event("request_received", "Request received")
        tracer.record_event("intent_detected", "Intent detected")
        tracer.record_event("scoring_complete", "Scoring complete")
        
        # Generate explanation
        explanation = explainer.explain(
            request=request,
            intent_match=("test", 0.9, "model"),
            candidates_with_scores=[("agent1", 0.9), ("agent2", 0.8)],
            selected_agent="agent1",
            policies_applied=[],
            processing_time_ms=75.0
        )
        
        # Get outputs
        text = explainer.get_text_explanation(explanation)
        json_str = explainer.get_json_explanation(explanation)
        debug = explainer.get_debug_report(explanation)
        trace = tracer.get_trace_text()
        
        # Verify all outputs are non-empty
        self.assertGreater(len(text), 0)
        self.assertGreater(len(json_str), 0)
        self.assertGreater(len(debug), 0)
        self.assertGreater(len(trace), 0)
        
        # Verify content consistency
        self.assertIn("integration-001", text)
        self.assertIn("integration-001", json_str)


class TestErrorHandling(unittest.TestCase):
    """Tests for error handling."""
    
    def test_explanation_with_empty_candidates(self):
        """Test explanation with no candidates."""
        explainer = DecisionExplainer()
        request = MCPRequest(
            request_id="test-001",
            user_id="user-001",
            text="Test",
            priority="normal"
        )
        
        # Should not raise error even with empty candidates
        explanation = explainer.explain(
            request=request,
            intent_match=("test", 0.9, "model"),
            candidates_with_scores=[],
            selected_agent="",
            policies_applied=[],
            processing_time_ms=50.0
        )
        
        self.assertIsNotNone(explanation)
    
    def test_json_serialization(self):
        """Test that explanations are JSON serializable."""
        explainer = DecisionExplainer()
        request = MCPRequest(
            request_id="test-001",
            user_id="user-001",
            text="Test",
            priority="normal"
        )
        
        explanation = explainer.explain(
            request=request,
            intent_match=("test", 0.9, "model"),
            candidates_with_scores=[("agent1", 0.9)],
            selected_agent="agent1",
            policies_applied=[],
            processing_time_ms=50.0
        )
        
        # Should be serializable to JSON
        json_str = explainer.get_json_explanation(explanation)
        parsed = json.loads(json_str)
        self.assertIsInstance(parsed, dict)


def run_tests():
    """Run all tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDecisionTracer))
    suite.addTests(loader.loadTestsFromTestCase(TestScoringFactor))
    suite.addTests(loader.loadTestsFromTestCase(TestDecisionExplainer))
    suite.addTests(loader.loadTestsFromTestCase(TestDecisionExplanationDataModel))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success/failure
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
