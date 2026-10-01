"""Step-by-step plan execution engine.

Walks through PlanSteps, calls tools, pipes data between steps,
and delegates failure handling to the ErrorHandler.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from agent.planner import PlanStep, StepStatus
from agent.error_handler import ErrorHandler
from tools.base import BaseTool, ToolResult, ToolStatus

logger = logging.getLogger("agent.executor")


class Executor:
    """
    Execute a list of PlanSteps using a registry of tools.

    The executor is responsible for:
      - Calling tools via safe_execute()
      - Piping outputs between steps
      - Delegating failures to ErrorHandler
      - Collecting a full execution trace
    """

    def __init__(self, tools: Dict[str, BaseTool]):
        self.tools = tools
        self.error_handler = ErrorHandler()
        self.execution_trace: List[Dict[str, Any]] = []
        self._collected_text: List[str] = []  # accumulates text across steps

    def run(self, steps: List[PlanStep]) -> List[PlanStep]:
        """Execute all steps in order, returning the updated steps."""
        logger.info("Executor: starting %d steps", len(steps))

        for step in steps:
            self._execute_step(step, steps)

        logger.info("Executor: finished all steps")
        return steps

    # ---- core execution logic --------------------------------------------------

    def _execute_step(self, step: PlanStep, all_steps: List[PlanStep]) -> None:
        """Run a single step, handling retries and fallbacks."""
        step.status = StepStatus.RUNNING
        logger.info("Step %d: %s [tool=%s]", step.step_id, step.description, step.tool_name)

        # Check that the tool exists
        tool = self.tools.get(step.tool_name)
        if tool is None:
            step.status = StepStatus.FAILED
            step.result = {"error": f"Tool '{step.tool_name}' not registered."}
            self._log_trace(step, None)
            return

        # Inject dynamic data if needed
        kwargs = self._prepare_kwargs(step, all_steps)

        # Execute with retry loop
        while True:
            result = tool.safe_execute(**kwargs)
            self._log_trace(step, result)

            if result.ok:
                step.status = StepStatus.SUCCESS
                step.result = result.data
                self._accumulate_text(result)
                logger.info(
                    "Step %d: SUCCESS (%.1f ms)",
                    step.step_id, result.duration_ms,
                )
                return

            # Ask error handler what to do
            action = self.error_handler.evaluate(step, result)

            if action == "retry":
                step.status = StepStatus.RETRIED
                logger.warning("Step %d: retrying…", step.step_id)
                continue

            if action == "fallback":
                fb_tool = self.tools.get(step.fallback_tool)
                if fb_tool:
                    fb_kwargs = step.fallback_kwargs or {}
                    fb_result = fb_tool.safe_execute(**fb_kwargs)
                    self._log_trace(step, fb_result, is_fallback=True)
                    if fb_result.ok:
                        step.status = StepStatus.SUCCESS
                        step.result = fb_result.data
                        self._accumulate_text(fb_result)
                        logger.info(
                            "Step %d: fallback SUCCESS via %s (%.1f ms)",
                            step.step_id, step.fallback_tool, fb_result.duration_ms,
                        )
                        return

            # Nothing worked — mark failed
            step.status = StepStatus.FAILED
            step.result = {"error": result.error_msg}
            logger.error("Step %d: FAILED — %s", step.step_id, result.error_msg)
            return

    def run_step(self, step: PlanStep, all_steps: List[PlanStep]) -> PlanStep:
        """Execute a single dynamically injected step."""
        self._execute_step(step, all_steps)
        return step

    @property
    def collected_text(self) -> List[str]:
        """Return a copy of the gathered raw text corpus."""
        return list(self._collected_text)

    # ---- dynamic data injection ------------------------------------------------

    def _prepare_kwargs(self, step: PlanStep, all_steps: List[PlanStep]) -> Dict[str, Any]:
        """Inject runtime data into tool kwargs based on step context."""
        kwargs = dict(step.tool_kwargs)

        # Summarizer: inject collected text
        if step.tool_name == "text_summarizer" and "text" not in kwargs:
            combined = " ".join(self._collected_text)
            kwargs["text"] = combined if combined else "No data collected yet."

        # Calculator: inject compression ratio if this is the metric step
        if step.tool_name == "calculator" and kwargs.get("expression") == "0":
            original_words = len(" ".join(self._collected_text).split())
            # Find the summarizer step result
            summary_words = 0
            for s in all_steps:
                if (
                    s.tool_name == "text_summarizer"
                    and s.status == StepStatus.SUCCESS
                    and isinstance(s.result, dict)
                ):
                    summary_text = s.result.get("summary", "")
                    summary_words = len(summary_text.split())
                    break

            if original_words > 0 and summary_words > 0:
                kwargs["expression"] = f"round({summary_words} / {original_words} * 100, 2)"
            else:
                kwargs["expression"] = "0"

        return kwargs

    # ---- text accumulation -----------------------------------------------------

    def _accumulate_text(self, result: ToolResult) -> None:
        """Extract readable text from a tool result and add to buffer."""
        data = result.data
        if data is None:
            return

        if isinstance(data, str):
            self._collected_text.append(data)
        elif isinstance(data, dict):
            # ArXiv paper findings
            if "papers" in data and isinstance(data["papers"], list):
                for p in data["papers"]:
                    if isinstance(p, dict):
                        parts = []
                        if p.get("title"):
                            parts.append(p["title"])
                        if p.get("summary"):
                            parts.append(p["summary"])
                        if parts:
                            self._collected_text.append(". ".join(parts))
            # Code executor results
            if "output" in data and data["output"]:
                self._collected_text.append(f"Code Output: {data['output']}")
            # Wikipedia-style result
            if "summary" in data:
                self._collected_text.append(data["summary"])
            # Calculator result
            if "result" in data and "expression" in data:
                self._collected_text.append(
                    f"Calculation: {data['expression']} = {data['result']}"
                )
        elif isinstance(data, list):
            # Web search or ArXiv papers
            for item in data:
                if isinstance(item, dict):
                    parts = []
                    if item.get("title"):
                        parts.append(item["title"])
                    if item.get("snippet"):
                        parts.append(item["snippet"])
                    if item.get("summary"):
                        parts.append(item["summary"])
                    if parts:
                        self._collected_text.append(". ".join(parts))

    # ---- trace logging ---------------------------------------------------------

    def _log_trace(
        self,
        step: PlanStep,
        result: Optional[ToolResult],
        is_fallback: bool = False,
    ) -> None:
        """Append an entry to the execution trace for the final report."""
        entry = {
            "step_id": step.step_id,
            "description": step.description,
            "tool": step.tool_name if not is_fallback else f"{step.fallback_tool} (fallback)",
            "status": result.status.value if result else "error",
            "duration_ms": round(result.duration_ms, 2) if result else 0,
            "error": result.error_msg if result and result.error_msg else None,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        self.execution_trace.append(entry)
