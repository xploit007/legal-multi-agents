"""A thin wrapper to create LangGraph-style flows and persist step outputs to Mongo.

This wrapper provides step-level tracing and auditability. Each step of an
agent's reasoning is persisted to MongoDB's `reasoning_steps` collection,
enabling replay, debugging, and audit trails.

If `langgraph` is not installed, it provides a compatible stub that still
persists step-level traces to Mongo so the system remains auditable.

Adapted from LegalServer-main by teammate.
"""
from typing import Callable, Any, Dict, Optional, List
import time

# Try to import langgraph (optional dependency)
try:
    import langgraph  # type: ignore
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

from services.mongo_utils import start_agent_run, finish_agent_run, write_reasoning_step


class StepTracer:
    """Traces and persists individual reasoning steps for an agent run."""

    def __init__(self, agent_name: str, case_id: str, metadata: Optional[Dict[str, Any]] = None):
        self.agent_name = agent_name
        self.case_id = case_id
        self.run = start_agent_run(agent_name, case_id, metadata)
        self.steps_executed: List[Dict[str, Any]] = []

    def run_step(self, step_name: str, fn: Callable[[], Any]) -> Dict[str, Any]:
        """Execute a single step and persist its output.

        Args:
            step_name: Name of the reasoning step
            fn: Callable that returns the step output

        Returns:
            Dict with 'output' and 'step_id'
        """
        start_time = time.time()
        try:
            output = fn()
            status = "success"
            error = None
        except Exception as e:
            output = None
            status = "error"
            error = str(e)

        duration_ms = int((time.time() - start_time) * 1000)

        # Persist to MongoDB
        step_doc = write_reasoning_step(
            self.run["run_id"],
            step_name,
            {
                "output": output,
                "status": status,
                "error": error,
                "duration_ms": duration_ms
            }
        )

        result = {
            "output": output,
            "step_id": step_doc.get("step_id"),
            "status": status,
            "error": error,
            "duration_ms": duration_ms
        }

        self.steps_executed.append({
            "step_name": step_name,
            **result
        })

        return result

    def run_steps(self, steps: Dict[str, Callable[[], Any]]) -> Dict[str, Dict[str, Any]]:
        """Execute a series of named steps sequentially.

        Args:
            steps: Dict mapping step names to callables

        Returns:
            Dict mapping step names to their results
        """
        results = {}
        for name, fn in steps.items():
            results[name] = self.run_step(name, fn)
        return results

    def finish(self, status: str = "completed", result: Optional[Dict[str, Any]] = None):
        """Mark the agent run as finished."""
        finish_agent_run(self.run["run_id"], status, result)

    @property
    def run_id(self) -> str:
        return self.run["run_id"]

    @property
    def trace(self) -> Dict[str, str]:
        """Return a mapping of step names to step IDs for tracing."""
        return {
            step["step_name"]: step["step_id"]
            for step in self.steps_executed
            if step.get("step_id")
        }


def build_and_run_simple_graph(
    agent_name: str,
    case_id: str,
    steps: Dict[str, Callable[[], Any]],
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Dict[str, Any]]:
    """Execute a simple sequential graph of steps with full tracing.

    This is the main entry point for running agent reasoning with persistence.
    Each step is executed in order and persisted to the `reasoning_steps` collection.

    Args:
        agent_name: Name of the agent (e.g., "Harvey", "Tanner")
        case_id: The case being analyzed
        steps: Dict mapping step names to callables that return results
        metadata: Optional metadata to attach to the run

    Returns:
        Dict mapping step names to their results (including step_id for tracing)
    """
    tracer = StepTracer(agent_name, case_id, metadata)
    results = tracer.run_steps(steps)
    tracer.finish(status="completed", result={"steps_count": len(steps)})
    return results


class AsyncStepTracer(StepTracer):
    """Async version of StepTracer for use with asyncio."""

    async def run_step_async(self, step_name: str, fn: Callable[[], Any]) -> Dict[str, Any]:
        """Execute a step asynchronously."""
        import asyncio

        start_time = time.time()
        try:
            if asyncio.iscoroutinefunction(fn):
                output = await fn()
            else:
                output = await asyncio.to_thread(fn)
            status = "success"
            error = None
        except Exception as e:
            output = None
            status = "error"
            error = str(e)

        duration_ms = int((time.time() - start_time) * 1000)

        step_doc = write_reasoning_step(
            self.run["run_id"],
            step_name,
            {
                "output": output,
                "status": status,
                "error": error,
                "duration_ms": duration_ms
            }
        )

        result = {
            "output": output,
            "step_id": step_doc.get("step_id"),
            "status": status,
            "error": error,
            "duration_ms": duration_ms
        }

        self.steps_executed.append({
            "step_name": step_name,
            **result
        })

        return result

    async def run_steps_async(self, steps: Dict[str, Callable[[], Any]]) -> Dict[str, Dict[str, Any]]:
        """Execute steps asynchronously in sequence."""
        results = {}
        for name, fn in steps.items():
            results[name] = await self.run_step_async(name, fn)
        return results
