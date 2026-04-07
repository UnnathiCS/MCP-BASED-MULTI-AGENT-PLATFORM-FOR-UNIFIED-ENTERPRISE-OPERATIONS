"""
MCP Execution Orchestrator: Execute agent invocations based on MCP decisions.

Responsibilities:
- Take MCPDecision output and execute the plan
- Handle sync, async, and pipeline execution modes
- Call agent endpoints with standard MCP contract
- Aggregate results from multiple agents
- Implement error handling and retry logic
- Track execution metrics and traces
"""

import logging
import asyncio
import requests
from typing import List, Dict, Any, Optional, Tuple, Callable
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid

from .models import (
    MCPDecision,
    MCPResponse,
    ExecutionPlan,
    ExecutionTask,
    AgentInvocation,
    AgentResponse,
)

logger = logging.getLogger(__name__)


class ExecutionMetrics:
    """Track metrics for task/plan execution."""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.end_time = None
        self.duration_ms = 0
        self.task_metrics: Dict[str, Dict[str, Any]] = {}
        self.total_tasks = 0
        self.succeeded = 0
        self.failed = 0
        self.retried = 0
    
    def record_task(self, task_id: str, agent_id: str, status: str, duration_ms: int, error: str = ""):
        """Record metrics for a task."""
        self.task_metrics[task_id] = {
            "agent_id": agent_id,
            "status": status,
            "duration_ms": duration_ms,
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if status == "success":
            self.succeeded += 1
        elif status == "error":
            self.failed += 1
    
    def finalize(self):
        """Finalize metrics."""
        self.end_time = datetime.utcnow()
        self.duration_ms = int((self.end_time - self.start_time).total_seconds() * 1000)
        self.total_tasks = len(self.task_metrics)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        return {
            "duration_ms": self.duration_ms,
            "total_tasks": self.total_tasks,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "retried": self.retried,
            "success_rate": self.succeeded / self.total_tasks if self.total_tasks > 0 else 0,
            "task_metrics": self.task_metrics,
        }


class ExecutionConfig:
    """Configuration for execution orchestrator."""
    
    def __init__(
        self,
        request_timeout_ms: int = 30000,
        max_retries: int = 3,
        retry_backoff_ms: int = 1000,
        max_parallel_tasks: int = 10,
        enable_distributed_tracing: bool = True,
    ):
        self.request_timeout_ms = request_timeout_ms
        self.max_retries = max_retries
        self.retry_backoff_ms = retry_backoff_ms
        self.max_parallel_tasks = max_parallel_tasks
        self.enable_distributed_tracing = enable_distributed_tracing


class TaskResult:
    """Result of a single task execution."""
    
    def __init__(
        self,
        task_id: str,
        agent_id: str,
        status: str,
        result: Any = None,
        error: str = "",
        duration_ms: int = 0,
        retry_count: int = 0,
    ):
        self.task_id = task_id
        self.agent_id = agent_id
        self.status = status  # "success", "error", "timeout", "retry"
        self.result = result
        self.error = error
        self.duration_ms = duration_ms
        self.retry_count = retry_count
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "retry_count": self.retry_count,
            "timestamp": self.timestamp,
        }


class MCPExecutionOrchestrator:
    """
    Executes agent invocations based on MCP decision plans.
    
    Features:
    - Sync execution: Single agent, blocking
    - Async execution: Multiple agents in parallel
    - Pipeline execution: Sequential agents with data flow
    - Error handling: Retry logic with exponential backoff
    - Distributed tracing: Full execution tracking
    - Metrics: Performance monitoring
    """
    
    def __init__(self, config: Optional[ExecutionConfig] = None):
        self.config = config or ExecutionConfig()
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_parallel_tasks)
    
    def execute_plan(
        self,
        decision: MCPDecision,
        registry: Any,  # AgentRegistry
    ) -> MCPResponse:
        """
        Execute an execution plan from MCP decision.
        
        Args:
            decision: MCPDecision with execution plan
            registry: Agent registry for lookups
            
        Returns:
            MCPResponse with execution results
        """
        logger.info(f"Executing plan {decision.plan.plan_id} ({decision.plan.mode} mode)")
        
        metrics = ExecutionMetrics()
        trace_id = f"trace-{uuid.uuid4()}"
        
        try:
            # Execute based on mode
            if decision.plan.mode == "sync":
                results = self._execute_sync(decision, registry, metrics, trace_id)
            elif decision.plan.mode == "async":
                results = self._execute_async(decision, registry, metrics, trace_id)
            elif decision.plan.mode == "pipeline":
                results = self._execute_pipeline(decision, registry, metrics, trace_id)
            else:
                return self._error_response(
                    decision.request_id,
                    f"Unknown execution mode: {decision.plan.mode}",
                    trace_id,
                )
            
            metrics.finalize()
            
            # Aggregate results
            aggregated = self._aggregate_results(results)
            
            # Build response
            return MCPResponse(
                request_id=decision.request_id,
                status="ok" if metrics.failed == 0 else "partial",
                result=aggregated,
                mcp_decision=decision,
                selected_agents=decision.selected_agents,
                audit={
                    "timestamp": datetime.utcnow().isoformat(),
                    "trace_id": trace_id,
                    "execution_mode": decision.plan.mode,
                    "metrics": metrics.to_dict(),
                },
            )
        
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            metrics.finalize()
            return self._error_response(decision.request_id, str(e), trace_id)
    
    def _execute_sync(
        self,
        decision: MCPDecision,
        registry: Any,
        metrics: ExecutionMetrics,
        trace_id: str,
    ) -> List[TaskResult]:
        """
        Synchronous execution: invoke tasks sequentially.
        
        - Blocking wait for each task
        - Stop on first error (unless fallback enabled)
        - Return results in order
        """
        logger.debug(f"Starting sync execution with {len(decision.plan.tasks)} tasks")
        
        results = []
        task_data = {}  # For pipeline data flow
        
        for task in decision.plan.tasks:
            try:
                # Check dependencies
                if task.depends_on:
                    for dep_id in task.depends_on:
                        if dep_id not in task_data:
                            logger.warning(f"Dependency {dep_id} not found")
                            continue
                        # Inject dependency data into payload
                        task.payload["_dependency_output"] = task_data[dep_id]
                
                # Invoke task
                result = self._invoke_task(task, registry, trace_id, metrics)
                results.append(result)
                
                # Store output for next task
                task_data[task.task_id] = result.result
                
                if result.status == "error":
                    logger.warning(f"Task {task.task_id} failed, continuing...")
                    
            except Exception as e:
                logger.error(f"Sync execution error: {e}")
                result = TaskResult(
                    task_id=task.task_id,
                    agent_id=task.agent_id,
                    status="error",
                    error=str(e),
                )
                results.append(result)
        
        return results
    
    def _execute_async(
        self,
        decision: MCPDecision,
        registry: Any,
        metrics: ExecutionMetrics,
        trace_id: str,
    ) -> List[TaskResult]:
        """
        Asynchronous execution: invoke multiple tasks in parallel.
        
        - Launch all tasks at once
        - Wait for all to complete
        - Return results in completion order
        - No data dependencies
        """
        logger.debug(f"Starting async execution with {len(decision.plan.tasks)} tasks")
        
        futures = {}
        for task in decision.plan.tasks:
            future = self.executor.submit(
                self._invoke_task,
                task,
                registry,
                trace_id,
                metrics,
            )
            futures[future] = task.task_id
        
        results = []
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Async task failed: {e}")
                results.append(TaskResult(
                    task_id=futures[future],
                    agent_id="unknown",
                    status="error",
                    error=str(e),
                ))
        
        return results
    
    def _execute_pipeline(
        self,
        decision: MCPDecision,
        registry: Any,
        metrics: ExecutionMetrics,
        trace_id: str,
    ) -> List[TaskResult]:
        """
        Pipeline execution: sequential tasks with data flow.
        
        - Task N uses output of Task N-1
        - Stop on error
        - Return chained results
        """
        logger.debug(f"Starting pipeline execution with {len(decision.plan.tasks)} tasks")
        
        results = []
        previous_result = None
        
        for task in decision.plan.tasks:
            try:
                # Inject previous result into payload
                if previous_result is not None:
                    task.payload["_pipeline_input"] = previous_result
                
                # Invoke task
                result = self._invoke_task(task, registry, trace_id, metrics)
                results.append(result)
                previous_result = result.result
                
                if result.status == "error":
                    logger.warning(f"Pipeline stopped at task {task.task_id}")
                    break
                    
            except Exception as e:
                logger.error(f"Pipeline execution error: {e}")
                result = TaskResult(
                    task_id=task.task_id,
                    agent_id=task.agent_id,
                    status="error",
                    error=str(e),
                )
                results.append(result)
                break
        
        return results
    
    def _invoke_task(
        self,
        task: ExecutionTask,
        registry: Any,
        trace_id: str,
        metrics: ExecutionMetrics,
        retry_count: int = 0,
    ) -> TaskResult:
        """
        Invoke a single task with retry logic.
        
        Args:
            task: Task to execute
            registry: Agent registry
            trace_id: Distributed trace ID
            metrics: Execution metrics
            retry_count: Current retry count
            
        Returns:
            TaskResult with execution status and result
        """
        start_time = datetime.utcnow()
        
        # Get agent
        agent = registry.get_agent(task.agent_id)
        if not agent:
            error_msg = f"Agent {task.agent_id} not found"
            logger.error(error_msg)
            return TaskResult(
                task_id=task.task_id,
                agent_id=task.agent_id,
                status="error",
                error=error_msg,
                duration_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
            )
        
        try:
            # Build MCP invocation envelope
            invocation = AgentInvocation(
                request_id=str(uuid.uuid4()),
                trace_id=trace_id,
                user_id="system",
                mcp_meta={
                    "agent_id": task.agent_id,
                    "action": task.action,
                },
                payload=task.payload,
                timeout_ms=task.timeout_ms,
                idempotency_key=task.idempotency_key or str(uuid.uuid4()),
            )
            
            # Invoke agent
            url = f"{agent.endpoint}/invoke"
            logger.info(f"Invoking task {task.task_id} on {agent.name}: {url}")
            
            response = requests.post(
                url,
                json=invocation.to_dict(),
                timeout=task.timeout_ms / 1000,
            )
            
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"Task {task.task_id} succeeded in {duration_ms}ms")
                
                metrics.record_task(task.task_id, task.agent_id, "success", duration_ms)
                
                return TaskResult(
                    task_id=task.task_id,
                    agent_id=task.agent_id,
                    status="success",
                    result=response_data.get("result", {}),
                    duration_ms=duration_ms,
                )
            else:
                error_msg = f"Agent returned status {response.status_code}: {response.text}"
                logger.warning(error_msg)
                
                # Retry logic
                if retry_count < self.config.max_retries:
                    logger.info(f"Retrying task {task.task_id} (attempt {retry_count + 1})")
                    metrics.retried += 1
                    await_ms = self.config.retry_backoff_ms * (2 ** retry_count)
                    asyncio.run(asyncio.sleep(await_ms / 1000))
                    return self._invoke_task(
                        task, registry, trace_id, metrics, retry_count + 1
                    )
                
                metrics.record_task(task.task_id, task.agent_id, "error", duration_ms, error_msg)
                
                return TaskResult(
                    task_id=task.task_id,
                    agent_id=task.agent_id,
                    status="error",
                    error=error_msg,
                    duration_ms=duration_ms,
                    retry_count=retry_count,
                )
        
        except requests.exceptions.Timeout:
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            error_msg = f"Request timeout after {duration_ms}ms"
            logger.warning(error_msg)
            
            # Retry on timeout
            if retry_count < self.config.max_retries:
                logger.info(f"Retrying task {task.task_id} after timeout")
                metrics.retried += 1
                await_ms = self.config.retry_backoff_ms * (2 ** retry_count)
                asyncio.run(asyncio.sleep(await_ms / 1000))
                return self._invoke_task(
                    task, registry, trace_id, metrics, retry_count + 1
                )
            
            metrics.record_task(task.task_id, task.agent_id, "timeout", duration_ms, error_msg)
            
            return TaskResult(
                task_id=task.task_id,
                agent_id=task.agent_id,
                status="timeout",
                error=error_msg,
                duration_ms=duration_ms,
                retry_count=retry_count,
            )
        
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error: {str(e)}"
            logger.error(error_msg)
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Retry on connection error
            if retry_count < self.config.max_retries:
                logger.info(f"Retrying task {task.task_id} after connection error")
                metrics.retried += 1
                await_ms = self.config.retry_backoff_ms * (2 ** retry_count)
                asyncio.run(asyncio.sleep(await_ms / 1000))
                return self._invoke_task(
                    task, registry, trace_id, metrics, retry_count + 1
                )
            
            metrics.record_task(task.task_id, task.agent_id, "error", duration_ms, error_msg)
            
            return TaskResult(
                task_id=task.task_id,
                agent_id=task.agent_id,
                status="error",
                error=error_msg,
                duration_ms=duration_ms,
                retry_count=retry_count,
            )
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            metrics.record_task(task.task_id, task.agent_id, "error", duration_ms, error_msg)
            
            return TaskResult(
                task_id=task.task_id,
                agent_id=task.agent_id,
                status="error",
                error=error_msg,
                duration_ms=duration_ms,
            )
    
    def _aggregate_results(self, results: List[TaskResult]) -> Dict[str, Any]:
        """
        Aggregate results from multiple tasks.
        
        Returns:
            Dict with aggregated data
        """
        aggregated = {
            "task_results": [r.to_dict() for r in results],
            "successful_tasks": sum(1 for r in results if r.status == "success"),
            "failed_tasks": sum(1 for r in results if r.status == "error"),
            "timed_out_tasks": sum(1 for r in results if r.status == "timeout"),
            "results_by_agent": {},
        }
        
        # Group by agent
        for result in results:
            if result.agent_id not in aggregated["results_by_agent"]:
                aggregated["results_by_agent"][result.agent_id] = []
            aggregated["results_by_agent"][result.agent_id].append(result.to_dict())
        
        # Combine task results into single output
        combined = {}
        for result in results:
            if result.status == "success" and result.result:
                combined.update(result.result)
        
        aggregated["combined_output"] = combined
        
        return aggregated
    
    def _error_response(
        self,
        request_id: str,
        error_msg: str,
        trace_id: str,
    ) -> MCPResponse:
        """Create error response."""
        return MCPResponse(
            request_id=request_id,
            status="error",
            result={"error": error_msg},
            audit={
                "timestamp": datetime.utcnow().isoformat(),
                "trace_id": trace_id,
                "error": error_msg,
            },
        )
    
    def __del__(self):
        """Cleanup thread pool."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
