"""Top-level agent that ties everything together.

Usage:
    agent = AgentOrchestrator()
    report = agent.run("Research the latest AI developments")
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from agent.planner import Planner, PlanStep
from agent.executor import Executor
from tools.base import BaseTool
from tools.web_search import WebSearchTool
from tools.wikipedia_tool import WikipediaTool
from tools.calculator import CalculatorTool
from tools.text_summarizer import TextSummarizerTool

logger = logging.getLogger("agent.orchestrator")


class AgentOrchestrator:
    """
    High-level orchestrator that:
      1. Accepts a user goal.
      2. Plans a sequence of steps.
      3. Executes the plan with tool calls.
      4. Handles errors and self-corrects.
      5. Produces a final structured report.
    """

    def __init__(self, simulate_failure: bool = True):
        """
        Args:
            simulate_failure: If True, the web-search tool will deliberately
                              fail on its first call to demonstrate error recovery.
        """
        self.planner = Planner()

        # Register all available tools
        self.tools: Dict[str, BaseTool] = {
            "web_search": WebSearchTool(simulate_failure=simulate_failure),
            "wikipedia": WikipediaTool(),
            "calculator": CalculatorTool(),
            "text_summarizer": TextSummarizerTool(),
        }

        self.executor: Optional[Executor] = None
        self._start_time: float = 0
        self._end_time: float = 0

    def run(self, goal: str) -> Dict[str, Any]:
        """
        Execute the full agent loop for *goal*.

        Returns a dict with keys:
            goal, plan, execution_trace, recovery_events,
            final_results, timing, metadata
        """
        logger.info("=" * 60)
        logger.info("AGENT START — Goal: %s", goal)
        logger.info("=" * 60)

        self._start_time = time.time()

        # ── Phase 1: Planning ──────────────────────────────────────
        logger.info("Phase 1: PLANNING")
        plan = self.planner.create_plan(goal)
        logger.info("Plan created with %d steps:", len(plan))
        for step in plan:
            logger.info(
                "  [%d] %s (tool=%s, fallback=%s)",
                step.step_id,
                step.description,
                step.tool_name,
                step.fallback_tool or "none",
            )

        # ── Phase 2: Execution ─────────────────────────────────────
        logger.info("Phase 2: EXECUTION")
        self.executor = Executor(self.tools)
        completed_steps = self.executor.run(plan)

        self._end_time = time.time()

        # ── Phase 3: Compile report data ───────────────────────────
        logger.info("Phase 3: COMPILING REPORT")
        report_data = self._compile_report(goal, completed_steps)

        logger.info("=" * 60)
        logger.info("AGENT COMPLETE — %.2f s total", self._end_time - self._start_time)
        logger.info("=" * 60)

        return report_data

    # ---- report compilation ----------------------------------------------------

    def _compile_report(
        self, goal: str, steps: List[PlanStep]
    ) -> Dict[str, Any]:
        """Assemble the structured report payload."""
        step_results = []
        for s in steps:
            step_results.append({
                "step_id": s.step_id,
                "description": s.description,
                "tool": s.tool_name,
                "status": s.status.value,
                "result_preview": self._preview(s.result),
                "retries": s.retry_count,
            })

        # Stats
        total = len(steps)
        succeeded = sum(1 for s in steps if s.status.value == "success")
        failed = sum(1 for s in steps if s.status.value == "failed")
        retried = sum(s.retry_count for s in steps)

        return {
            "goal": goal,
            "plan": [s.to_dict() for s in steps],
            "execution_trace": self.executor.execution_trace,
            "recovery_events": self.executor.error_handler.get_recovery_summary(),
            "step_results": step_results,
            "statistics": {
                "total_steps": total,
                "succeeded": succeeded,
                "failed": failed,
                "total_retries": retried,
                "success_rate": f"{succeeded / total * 100:.1f}%" if total else "N/A",
            },
            "timing": {
                "start": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(self._start_time)),
                "end": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(self._end_time)),
                "duration_seconds": round(self._end_time - self._start_time, 2),
            },
            "tools_available": list(self.tools.keys()),
        }

    @staticmethod
    def _preview(data: Any, max_len: int = 200) -> str:
        """Produce a short string preview of a result."""
        if data is None:
            return "(no data)"
        text = str(data)
        if len(text) > max_len:
            return text[:max_len] + "…"
        return text
