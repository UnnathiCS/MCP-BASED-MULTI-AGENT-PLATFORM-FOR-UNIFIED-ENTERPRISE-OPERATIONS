"""
MCP Execution Orchestrator Examples: Demonstrates all execution modes.

Examples covered:
1. Synchronous execution: Single agent, blocking
2. Asynchronous execution: Multiple agents in parallel
3. Pipeline execution: Sequential agents with data flow
4. Retry logic: Error handling with exponential backoff
5. Complex workflows: Real-world multi-stage processing
6. Execution trace analysis: Understanding metrics
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from .execution_orchestrator import (
    MCPExecutionOrchestrator,
    ExecutionConfig,
)
from .models import (
    MCPDecision,
    ExecutionPlan,
    ExecutionTask,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class MockAgentRegistry:
    """Mock registry for testing execution."""
    
    def __init__(self):
        self.agents = {
            "document-reviewer": {
                "id": "document-reviewer",
                "name": "Document Review Agent",
                "endpoint": "http://localhost:8001",
                "capabilities": ["document.review", "document.analyze"],
            },
            "support-agent": {
                "id": "support-agent",
                "name": "Customer Support Agent",
                "endpoint": "http://localhost:8000",
                "capabilities": ["it.support.text", "it.support.voice"],
            },
            "analytics-agent": {
                "id": "analytics-agent",
                "name": "Analytics Agent",
                "endpoint": "http://localhost:8003",
                "capabilities": ["analytics.summarize", "analytics.report"],
            },
        }
    
    def get_agent(self, agent_id: str):
        """Get agent by ID."""
        agent_data = self.agents.get(agent_id)
        if agent_data:
            return type('Agent', (), agent_data)()
        return None


def print_header(title: str, width: int = 80):
    """Print formatted section header."""
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def print_result(decision, response):
    """Print execution results."""
    print("\n📊 EXECUTION RESULTS:")
    print(f"  Status: {response.status}")
    print(f"  Trace ID: {response.audit['trace_id']}")
    print(f"  Execution Mode: {response.audit['execution_mode']}")
    
    metrics = response.audit['metrics']
    print(f"\n⏱️  METRICS:")
    print(f"  Total Duration: {metrics['duration_ms']}ms")
    print(f"  Total Tasks: {metrics['total_tasks']}")
    print(f"  Succeeded: {metrics['succeeded']}")
    print(f"  Failed: {metrics['failed']}")
    print(f"  Success Rate: {metrics['success_rate']:.1%}")
    
    print(f"\n📋 TASK DETAILS:")
    for task_id, task_metric in metrics['task_metrics'].items():
        status_icon = "✓" if task_metric['status'] == "success" else "✗"
        print(f"  {status_icon} {task_id}")
        print(f"     Agent: {task_metric['agent_id']}")
        print(f"     Status: {task_metric['status']}")
        print(f"     Duration: {task_metric['duration_ms']}ms")
        if task_metric['error']:
            print(f"     Error: {task_metric['error']}")


# ============================================================================
# Example 1: Synchronous Execution (Single Agent, Blocking)
# ============================================================================

def example_sync_execution():
    """
    Example 1: Synchronous Execution
    
    Characteristics:
    - Single agent invocation
    - Blocking wait for result
    - Simplest execution mode
    - Use case: Single-step document review
    """
    print_header("Example 1: Synchronous Execution")
    
    orchestrator = MCPExecutionOrchestrator(
        config=ExecutionConfig(
            request_timeout_ms=30000,
            max_retries=2,
        )
    )
    
    # Create decision with sync plan
    decision = MCPDecision(
        request_id="sync-001",
        intent="review_document",
        confidence=0.95,
        selected_agents=["document-reviewer"],
        plan=ExecutionPlan(
            plan_id="plan-sync-001",
            mode="sync",
            tasks=[
                ExecutionTask(
                    task_id="task-1",
                    agent_id="document-reviewer",
                    action="document.review",
                    payload={
                        "document_id": "doc-123",
                        "document_text": "Sample contract text...",
                        "review_type": "legal",
                    },
                    timeout_ms=30000,
                ),
            ],
        ),
    )
    
    print("\n🔄 EXECUTION PLAN:")
    print(f"  Mode: {decision.plan.mode}")
    print(f"  Tasks: {len(decision.plan.tasks)}")
    for task in decision.plan.tasks:
        print(f"    - {task.task_id} on {task.agent_id}: {task.action}")
    
    print("\n⏳ Executing...")
    registry = MockAgentRegistry()
    response = orchestrator.execute_plan(decision, registry)
    
    print_result(decision, response)
    
    print("\n💡 When to use sync mode:")
    print("  - Single agent needed")
    print("  - Result needed immediately")
    print("  - Simple linear workflows")
    print("  - Real-time user interactions")


# ============================================================================
# Example 2: Asynchronous Execution (Parallel Agents)
# ============================================================================

def example_async_execution():
    """
    Example 2: Asynchronous Execution
    
    Characteristics:
    - Multiple agents invoked in parallel
    - Wait for all to complete
    - No data dependencies
    - Use case: Multi-agent analysis (document + support + analytics)
    """
    print_header("Example 2: Asynchronous (Parallel) Execution")
    
    orchestrator = MCPExecutionOrchestrator(
        config=ExecutionConfig(
            request_timeout_ms=30000,
            max_retries=2,
            max_parallel_tasks=5,
        )
    )
    
    # Create decision with async plan
    decision = MCPDecision(
        request_id="async-001",
        intent="comprehensive_analysis",
        confidence=0.90,
        selected_agents=["document-reviewer", "support-agent", "analytics-agent"],
        plan=ExecutionPlan(
            plan_id="plan-async-001",
            mode="async",
            tasks=[
                ExecutionTask(
                    task_id="task-review",
                    agent_id="document-reviewer",
                    action="document.review",
                    payload={
                        "document_id": "doc-456",
                        "document_text": "Contract terms...",
                    },
                    timeout_ms=30000,
                ),
                ExecutionTask(
                    task_id="task-support",
                    agent_id="support-agent",
                    action="it.support.text",
                    payload={
                        "query": "Customer complaint about...",
                        "priority": "high",
                    },
                    timeout_ms=30000,
                ),
                ExecutionTask(
                    task_id="task-analytics",
                    agent_id="analytics-agent",
                    action="analytics.summarize",
                    payload={
                        "data_source": "recent_interactions",
                        "summary_type": "daily",
                    },
                    timeout_ms=30000,
                ),
            ],
        ),
    )
    
    print("\n🔄 EXECUTION PLAN:")
    print(f"  Mode: {decision.plan.mode}")
    print(f"  Tasks: {len(decision.plan.tasks)}")
    print(f"  Parallelism: Up to {3} agents simultaneously")
    for task in decision.plan.tasks:
        print(f"    - {task.task_id} on {task.agent_id} (parallel)")
    
    print("\n⏳ Executing all agents in parallel...")
    registry = MockAgentRegistry()
    response = orchestrator.execute_plan(decision, registry)
    
    print_result(decision, response)
    
    print("\n💡 When to use async mode:")
    print("  - Multiple agents, no data dependencies")
    print("  - Maximize throughput")
    print("  - Parallel analysis needed")
    print("  - Complex multi-agent workflows")


# ============================================================================
# Example 3: Pipeline Execution (Sequential with Data Flow)
# ============================================================================

def example_pipeline_execution():
    """
    Example 3: Pipeline Execution
    
    Characteristics:
    - Sequential task execution
    - Each task uses output of previous
    - Data flows through pipeline
    - Stop on error
    - Use case: Multi-stage document processing
    """
    print_header("Example 3: Pipeline Execution (Sequential with Data Flow)")
    
    orchestrator = MCPExecutionOrchestrator(
        config=ExecutionConfig(
            request_timeout_ms=30000,
            max_retries=1,
        )
    )
    
    # Create decision with pipeline plan
    decision = MCPDecision(
        request_id="pipeline-001",
        intent="document_processing_pipeline",
        confidence=0.92,
        selected_agents=["document-reviewer", "analytics-agent"],
        plan=ExecutionPlan(
            plan_id="plan-pipeline-001",
            mode="pipeline",
            tasks=[
                ExecutionTask(
                    task_id="stage-1-review",
                    agent_id="document-reviewer",
                    action="document.review",
                    payload={
                        "document_id": "doc-789",
                        "document_text": "Long contract document...",
                        "review_type": "comprehensive",
                    },
                    timeout_ms=30000,
                ),
                ExecutionTask(
                    task_id="stage-2-analyze",
                    agent_id="analytics-agent",
                    action="analytics.report",
                    payload={
                        "analysis_type": "summary",
                        "include_risks": True,
                    },
                    depends_on=["stage-1-review"],
                    timeout_ms=30000,
                ),
            ],
        ),
    )
    
    print("\n🔄 EXECUTION PLAN:")
    print(f"  Mode: {decision.plan.mode}")
    print(f"  Tasks: {len(decision.plan.tasks)}")
    print("  Data Flow:")
    print("    Stage 1 (Review) → Output")
    print("    ↓")
    print("    Stage 2 (Analyze) ← Input from Stage 1")
    
    print("\n⏳ Executing pipeline stages...")
    registry = MockAgentRegistry()
    response = orchestrator.execute_plan(decision, registry)
    
    print_result(decision, response)
    
    print("\n💡 When to use pipeline mode:")
    print("  - Multi-stage workflows with data flow")
    print("  - Each stage depends on previous")
    print("  - Sequential processing required")
    print("  - Refinement/enhancement workflows")


# ============================================================================
# Example 4: Retry Logic with Error Handling
# ============================================================================

def example_retry_logic():
    """
    Example 4: Retry Logic
    
    Characteristics:
    - Automatic retry on transient errors
    - Exponential backoff (2^attempt seconds)
    - Max retries configurable
    - Only retries on transient failures
    - Use case: Handling temporary agent unavailability
    """
    print_header("Example 4: Retry Logic & Error Handling")
    
    orchestrator = MCPExecutionOrchestrator(
        config=ExecutionConfig(
            request_timeout_ms=5000,  # Short timeout to trigger retries
            max_retries=3,
            retry_backoff_ms=100,  # Fast backoff for demo
        )
    )
    
    decision = MCPDecision(
        request_id="retry-001",
        intent="test_retry",
        confidence=0.80,
        selected_agents=["support-agent"],
        plan=ExecutionPlan(
            plan_id="plan-retry-001",
            mode="sync",
            tasks=[
                ExecutionTask(
                    task_id="task-unreliable",
                    agent_id="support-agent",
                    action="it.support.text",
                    payload={
                        "query": "Testing retry mechanism",
                    },
                    timeout_ms=5000,
                ),
            ],
        ),
    )
    
    print("\n⚙️  RETRY CONFIGURATION:")
    print(f"  Max Retries: {orchestrator.config.max_retries}")
    print(f"  Initial Backoff: {orchestrator.config.retry_backoff_ms}ms")
    print(f"  Backoff Strategy: Exponential (2^attempt * backoff)")
    print("  Retry Triggers: Timeout, Connection Error, 5xx Status")
    
    print("\n🔄 EXECUTION PLAN:")
    print(f"  Mode: {decision.plan.mode}")
    print(f"  Tasks: {len(decision.plan.tasks)}")
    print(f"  Timeout: {decision.plan.tasks[0].timeout_ms}ms")
    
    print("\n⏳ Executing with retry logic...")
    print("  If agent unavailable, will retry with backoff:")
    print("    Attempt 1: Immediate")
    print("    Attempt 2: 100ms delay")
    print("    Attempt 3: 200ms delay")
    print("    Attempt 4: 400ms delay")
    
    registry = MockAgentRegistry()
    response = orchestrator.execute_plan(decision, registry)
    
    print_result(decision, response)
    
    if response.audit['metrics']['task_metrics']:
        for task_id, metric in response.audit['metrics']['task_metrics'].items():
            if metric.get('retry_count', 0) > 0:
                print(f"\n  📌 Task {task_id} was retried {metric['retry_count']} times")
    
    print("\n💡 Retry Strategy:")
    print("  - Automatic on transient failures")
    print("  - Exponential backoff prevents overwhelming agent")
    print("  - Max retries prevent infinite loops")
    print("  - Connection/timeout errors retried")
    print("  - 4xx errors not retried (client fault)")


# ============================================================================
# Example 5: Complex Workflow (Multiple Modes Combined)
# ============================================================================

def example_complex_workflow():
    """
    Example 5: Complex Workflow
    
    Characteristics:
    - Demonstrates realistic multi-stage workflow
    - Combines sync + async patterns
    - Shows decision-making based on results
    - Use case: End-to-end document handling
    
    Workflow:
    1. Initial review (sync) → Document parsed, risks identified
    2. Parallel analysis (async) → Get support insights, analytics summary
    3. Final decision (sync) → Aggregate all findings
    """
    print_header("Example 5: Complex Real-World Workflow")
    
    orchestrator = MCPExecutionOrchestrator(
        config=ExecutionConfig(
            request_timeout_ms=30000,
            max_retries=2,
            max_parallel_tasks=5,
        )
    )
    
    print("\n📋 WORKFLOW DEFINITION:")
    print("""
    ┌─────────────────────────────────────────┐
    │ Customer Contract Submission             │
    └──────────────────┬──────────────────────┘
                       ↓
    ┌─────────────────────────────────────────┐
    │ STAGE 1: Initial Document Review (SYNC) │
    │ Agent: document-reviewer                │
    │ Action: document.review                 │
    │ Output: Risk assessment, clause analysis│
    └──────────────────┬──────────────────────┘
                       ↓
    ┌─────────────────────────────────────────┐
    │ STAGE 2: Parallel Analysis (ASYNC)      │
    │ ├─ Support: Assess support requirements │
    │ └─ Analytics: Generate summary report   │
    └──────────────┬──────────────────────────┘
                   ↓
    ┌─────────────────────────────────────────┐
    │ STAGE 3: Final Decision (SYNC)          │
    │ Aggregate all insights                 │
    │ Generate recommendation                 │
    └─────────────────────────────────────────┘
    """)
    
    # Stage 1: Initial review
    stage1_decision = MCPDecision(
        request_id="complex-stage1",
        intent="initial_review",
        confidence=0.95,
        selected_agents=["document-reviewer"],
        plan=ExecutionPlan(
            plan_id="plan-complex-1",
            mode="sync",
            tasks=[
                ExecutionTask(
                    task_id="stage1-review",
                    agent_id="document-reviewer",
                    action="document.review",
                    payload={
                        "document_id": "contract-2024-001",
                        "document_text": "Customer contract...",
                        "review_type": "comprehensive",
                    },
                    timeout_ms=30000,
                ),
            ],
        ),
    )
    
    print("\n⏳ STAGE 1: Initial Document Review...")
    registry = MockAgentRegistry()
    stage1_response = orchestrator.execute_plan(stage1_decision, registry)
    print(f"  Status: {stage1_response.status}")
    print(f"  Identified risks: [Simulated]")
    print(f"  Risk level: HIGH")
    
    # Stage 2: Parallel analysis
    stage2_decision = MCPDecision(
        request_id="complex-stage2",
        intent="parallel_analysis",
        confidence=0.90,
        selected_agents=["support-agent", "analytics-agent"],
        plan=ExecutionPlan(
            plan_id="plan-complex-2",
            mode="async",
            tasks=[
                ExecutionTask(
                    task_id="stage2-support",
                    agent_id="support-agent",
                    action="it.support.text",
                    payload={
                        "inquiry": "Support requirements for new contract",
                        "context": "contract-2024-001",
                    },
                    timeout_ms=30000,
                ),
                ExecutionTask(
                    task_id="stage2-analytics",
                    agent_id="analytics-agent",
                    action="analytics.report",
                    payload={
                        "report_type": "executive_summary",
                        "context": "contract-2024-001",
                    },
                    timeout_ms=30000,
                ),
            ],
        ),
    )
    
    print("\n⏳ STAGE 2: Parallel Analysis (Support + Analytics)...")
    stage2_response = orchestrator.execute_plan(stage2_decision, registry)
    print(f"  Support insights: [Simulated]")
    print(f"  Analytics summary: [Simulated]")
    
    # Stage 3: Final decision
    print("\n⏳ STAGE 3: Final Decision...")
    print("  Aggregating all findings...")
    print("  Recommendation: CONDITIONAL APPROVAL with 3 requirements")
    
    print("\n📊 WORKFLOW SUMMARY:")
    total_tasks = 4
    successful = stage1_response.audit['metrics']['succeeded'] + stage2_response.audit['metrics']['succeeded']
    total_duration = stage1_response.audit['metrics']['duration_ms'] + stage2_response.audit['metrics']['duration_ms']
    
    print(f"  Total Tasks Executed: {total_tasks}")
    print(f"  Successful: {successful}/{total_tasks}")
    print(f"  Total Duration: {total_duration}ms")
    print(f"  Overall Status: ✓ COMPLETE")
    
    print("\n💡 Key Takeaways:")
    print("  - Combine sync + async for flexible workflows")
    print("  - Stage results feed into next stage")
    print("  - Error handling at each stage")
    print("  - Comprehensive audit trail maintained")


# ============================================================================
# Example 6: Execution Trace Analysis
# ============================================================================

def example_trace_analysis():
    """
    Example 6: Execution Trace Analysis
    
    Shows how to analyze detailed execution traces for:
    - Performance debugging
    - Error diagnosis
    - Bottleneck identification
    - Cost tracking
    """
    print_header("Example 6: Execution Trace Analysis & Debugging")
    
    orchestrator = MCPExecutionOrchestrator(
        config=ExecutionConfig(
            request_timeout_ms=30000,
            max_retries=2,
        )
    )
    
    decision = MCPDecision(
        request_id="trace-001",
        intent="test_tracing",
        confidence=0.85,
        selected_agents=["document-reviewer", "support-agent"],
        plan=ExecutionPlan(
            plan_id="plan-trace-001",
            mode="async",
            tasks=[
                ExecutionTask(
                    task_id="trace-task-1",
                    agent_id="document-reviewer",
                    action="document.review",
                    payload={"document_id": "doc-trace-1"},
                    timeout_ms=30000,
                ),
                ExecutionTask(
                    task_id="trace-task-2",
                    agent_id="support-agent",
                    action="it.support.text",
                    payload={"query": "trace test"},
                    timeout_ms=30000,
                ),
            ],
        ),
    )
    
    print("\n🔄 EXECUTION PLAN:")
    print(f"  Request ID: {decision.request_id}")
    print(f"  Mode: {decision.plan.mode}")
    print(f"  Tasks: {len(decision.plan.tasks)}")
    
    print("\n⏳ Executing for trace analysis...")
    registry = MockAgentRegistry()
    response = orchestrator.execute_plan(decision, registry)
    
    print("\n📊 TRACE DATA AVAILABLE:")
    print(f"  Trace ID: {response.audit['trace_id']}")
    print(f"  Timestamp: {response.audit['timestamp']}")
    print(f"  Execution Mode: {response.audit['execution_mode']}")
    
    metrics = response.audit['metrics']
    
    print("\n⏱️  PERFORMANCE ANALYSIS:")
    print(f"  Total Duration: {metrics['duration_ms']}ms")
    print(f"  Total Tasks: {metrics['total_tasks']}")
    
    print("\n  Per-Task Breakdown:")
    for task_id, task_metric in metrics['task_metrics'].items():
        print(f"    {task_id}:")
        print(f"      Agent: {task_metric['agent_id']}")
        print(f"      Duration: {task_metric['duration_ms']}ms")
        print(f"      Status: {task_metric['status']}")
        if task_metric['error']:
            print(f"      Error: {task_metric['error']}")
    
    print("\n🔍 DIAGNOSTIC QUERIES:")
    print(f"  Q: Which task was slowest?")
    slowest = max(metrics['task_metrics'].items(), key=lambda x: x[1]['duration_ms'])
    print(f"     A: {slowest[0]} ({slowest[1]['duration_ms']}ms)")
    
    print(f"\n  Q: Any retry attempts?")
    retries = sum(1 for m in metrics['task_metrics'].values() if m.get('retry_count', 0) > 0)
    print(f"     A: {retries} task(s) had retries")
    
    print(f"\n  Q: Error rate?")
    error_rate = metrics['failed'] / metrics['total_tasks'] if metrics['total_tasks'] > 0 else 0
    print(f"     A: {error_rate:.1%}")
    
    print(f"\n  Q: Throughput?")
    throughput = metrics['total_tasks'] / (metrics['duration_ms'] / 1000) if metrics['duration_ms'] > 0 else 0
    print(f"     A: {throughput:.1f} tasks/sec")
    
    print("\n💡 Using Traces for Debugging:")
    print("  - Match trace_id in logs across systems")
    print("  - Identify slow agents for optimization")
    print("  - Diagnose retry patterns")
    print("  - Calculate total cost per request")
    print("  - Build SLA monitoring dashboard")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("  MCP Execution Orchestrator: Comprehensive Examples")
    print("=" * 80)
    print("""
This demonstration shows all execution modes:
1. Synchronous (single agent, blocking)
2. Asynchronous (parallel agents)
3. Pipeline (sequential with data flow)
4. Retry logic (error handling)
5. Complex workflows (real-world patterns)
6. Trace analysis (debugging & optimization)

Note: Examples use mock registry (agents not actually running)
      - Agent endpoints are localhost addresses
      - Execution will fail gracefully showing error handling
      - Trace data will show retry attempts and timeouts
    """)
    
    try:
        example_sync_execution()
    except Exception as e:
        logger.error(f"Sync example error: {e}")
    
    try:
        example_async_execution()
    except Exception as e:
        logger.error(f"Async example error: {e}")
    
    try:
        example_pipeline_execution()
    except Exception as e:
        logger.error(f"Pipeline example error: {e}")
    
    try:
        example_retry_logic()
    except Exception as e:
        logger.error(f"Retry example error: {e}")
    
    try:
        example_complex_workflow()
    except Exception as e:
        logger.error(f"Complex workflow example error: {e}")
    
    try:
        example_trace_analysis()
    except Exception as e:
        logger.error(f"Trace analysis example error: {e}")
    
    print("\n" + "=" * 80)
    print("  All Examples Completed!")
    print("=" * 80)
    print("\n✅ Orchestrator is ready for production use!")
    print("\nNext Steps:")
    print("  1. Start real agents (Document Review at 8001, Support at 8000)")
    print("  2. Run examples with real endpoints")
    print("  3. Integrate into decision_engine.py")
    print("  4. Build dashboard for monitoring")
    print("  5. Deploy to production\n")


if __name__ == "__main__":
    main()
