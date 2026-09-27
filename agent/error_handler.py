"""Retry, fallback, and self-correction logic.

When a tool call fails, the ErrorHandler decides what to do:
  1. Retry the same tool (up to max_retries)
  2. Switch to a fallback tool
  3. Mark the step as failed and move on
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List

from agent.planner import PlanStep, StepStatus
from tools.base import ToolResult, ToolStatus

logger = logging.getLogger("agent.error_handler")


@dataclass
class RecoveryEvent:
    """Record of a single recovery action taken by the agent."""
    step_id: int
    action: str        # "retry" | "fallback" | "skip"
    reason: str
    attempt: int
    outcome: str       # what happened after the recovery action

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "action": self.action,
            "reason": self.reason,
            "attempt": self.attempt,
            "outcome": self.outcome,
        }


class ErrorHandler:
    """
    Decide how to recover from a failed tool invocation.

    Usage (by Executor):
        handler = ErrorHandler()
        action = handler.evaluate(step, tool_result)
        # action is one of: "retry", "fallback", "skip"
    """

    def __init__(self):
        self.recovery_log: List[RecoveryEvent] = []

    def evaluate(self, step: PlanStep, result: ToolResult) -> str:
        """
        Given a failed ToolResult, decide the recovery strategy.

        Returns one of:
            "retry"    — caller should retry the same tool
            "fallback" — caller should try step.fallback_tool
            "skip"     — caller should mark step as failed and move on
        """
        # If it succeeded or partially succeeded, no recovery needed
        if result.ok:
            return "ok"

        reason = result.error_msg or f"Tool returned status {result.status.value}"

        # Can we retry?
        if step.retry_count < step.max_retries:
            step.retry_count += 1
            event = RecoveryEvent(
                step_id=step.step_id,
                action="retry",
                reason=reason,
                attempt=step.retry_count,
                outcome="Retrying same tool…",
            )
            self.recovery_log.append(event)
            logger.warning(
                "Step %d: %s — retrying (%d/%d)",
                step.step_id, reason, step.retry_count, step.max_retries,
            )
            return "retry"

        # Retries exhausted — can we fall back to another tool?
        if step.fallback_tool:
            event = RecoveryEvent(
                step_id=step.step_id,
                action="fallback",
                reason=f"Retries exhausted. {reason}",
                attempt=step.retry_count,
                outcome=f"Falling back to tool: {step.fallback_tool}",
            )
            self.recovery_log.append(event)
            logger.warning(
                "Step %d: retries exhausted — falling back to %s",
                step.step_id, step.fallback_tool,
            )
            return "fallback"

        # No fallback available — skip
        event = RecoveryEvent(
            step_id=step.step_id,
            action="skip",
            reason=f"No fallback available. {reason}",
            attempt=step.retry_count,
            outcome="Step marked as FAILED; continuing with remaining plan.",
        )
        self.recovery_log.append(event)
        logger.error(
            "Step %d: no recovery path — skipping. Reason: %s",
            step.step_id, reason,
        )
        return "skip"

    def get_recovery_summary(self) -> List[Dict[str, Any]]:
        """Return all recovery events as dicts for the final report."""
        return [e.to_dict() for e in self.recovery_log]
