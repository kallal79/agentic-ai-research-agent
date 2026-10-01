"""Self-Reflection & Dynamic Replanning Engine.

Audits collected step findings against the user's high-level goal,
evaluates information completeness, identifies missing facets,
and dynamically injects follow-up steps if gaps are detected.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from agent.planner import PlanStep, StepStatus

logger = logging.getLogger("agent.reflection")


class ReflectionReport:
    """Dataclass capturing the outcome of the agent's self-reflection phase."""

    def __init__(
        self,
        completeness_score: float,
        confidence_level: str,
        critique: str,
        identified_gaps: List[str],
        recommended_action: str,
        follow_up_step: Optional[PlanStep] = None,
    ):
        self.completeness_score = completeness_score
        self.confidence_level = confidence_level
        self.critique = critique
        self.identified_gaps = identified_gaps
        self.recommended_action = recommended_action
        self.follow_up_step = follow_up_step

    def to_dict(self) -> Dict[str, Any]:
        return {
            "completeness_score": round(self.completeness_score, 1),
            "confidence_level": self.confidence_level,
            "critique": self.critique,
            "identified_gaps": self.identified_gaps,
            "recommended_action": self.recommended_action,
            "dynamic_replan_triggered": self.follow_up_step is not None,
            "follow_up_step": self.follow_up_step.to_dict() if self.follow_up_step else None,
        }


class ReflectionEngine:
    """Evaluates collected knowledge and dynamically triggers replanning when needed."""

    def reflect(
        self,
        goal: str,
        executed_steps: List[PlanStep],
        collected_text: List[str],
    ) -> ReflectionReport:
        """
        Audit the results of executed research steps before final synthesis.

        Returns a ReflectionReport with gap analysis and optional follow-up PlanStep.
        """
        logger.info("Phase 2.5: Running Self-Reflection on %d executed steps", len(executed_steps))

        total_words = sum(len(txt.split()) for txt in collected_text)
        succeeded_steps = [s for s in executed_steps if s.status == StepStatus.SUCCESS]
        failed_steps = [s for s in executed_steps if s.status in (StepStatus.FAILED, StepStatus.SKIPPED)]

        # --- Criterion 1: Execution Health (40 pts) ---
        health_score = (len(succeeded_steps) / max(1, len(executed_steps))) * 40.0

        # --- Criterion 2: Information Density (30 pts) ---
        if total_words > 300:
            density_score = 30.0
        elif total_words > 150:
            density_score = 22.0
        elif total_words > 50:
            density_score = 15.0
        else:
            density_score = 5.0

        # --- Criterion 3: Goal Keyword Coverage (30 pts) ---
        coverage_score, missing_topics = self._evaluate_keyword_coverage(goal, collected_text)

        total_score = min(100.0, health_score + density_score + coverage_score)

        # Confidence level
        if total_score >= 80.0:
            confidence = "HIGH"
        elif total_score >= 60.0:
            confidence = "MODERATE"
        else:
            confidence = "LOW"

        # Gap identification
        gaps: List[str] = []
        if failed_steps:
            gaps.append(f"{len(failed_steps)} step(s) failed or were skipped during execution.")
        if missing_topics:
            gaps.append(f"Key facets have low representation: {', '.join(missing_topics[:3])}")
        if total_words < 100:
            gaps.append("Accumulated text volume is sparse (< 100 words).")

        # Dynamic replanning decision
        follow_up_step: Optional[PlanStep] = None
        action = "PROCEED_TO_SYNTHESIS"

        # If coverage is low and missing a clear topic, trigger dynamic replan
        if total_score < 75.0 and missing_topics:
            topic_to_query = missing_topics[0]
            next_id = max((s.step_id for s in executed_steps), default=0) + 1
            follow_up_step = PlanStep(
                step_id=next_id,
                description=f"Supplementary targeted search to bridge identified gap: '{topic_to_query}'",
                tool_name="web_search",
                tool_kwargs={"query": f"{topic_to_query} overview analysis"},
                fallback_tool="wikipedia",
            )
            action = "DYNAMIC_REPLAN_INJECTED"
            critique = (
                f"Self-reflection identified knowledge gap on '{topic_to_query}' (Completeness: {total_score:.1f}%). "
                f"Autonomously injecting supplementary step {next_id} to enrich dataset before final report."
            )
        else:
            critique = (
                f"Sufficient information gathered ({total_words} words, {len(succeeded_steps)} successful steps). "
                f"Completeness evaluated at {total_score:.1f}% with {confidence} confidence."
            )

        logger.info("Reflection result: score=%.1f, confidence=%s, action=%s", total_score, confidence, action)

        return ReflectionReport(
            completeness_score=total_score,
            confidence_level=confidence,
            critique=critique,
            identified_gaps=gaps,
            recommended_action=action,
            follow_up_step=follow_up_step,
        )

    def _evaluate_keyword_coverage(
        self,
        goal: str,
        collected_text: List[str],
    ) -> Tuple[float, List[str]]:
        """Check if substantive words from the goal appear in gathered findings."""
        stop_words = {
            "the", "and", "for", "with", "from", "that", "this", "about", "into",
            "over", "top", "recent", "latest", "produce", "short", "given", "using",
            "plan", "make", "create", "find", "research", "summarize", "last", "week",
        }
        words = re.findall(r"\b[a-zA-Z]{4,}\b", goal.lower())
        keywords = [w for w in words if w not in stop_words]

        if not keywords:
            return 30.0, []

        full_corpus = " ".join(collected_text).lower()
        found = [kw for kw in keywords if kw in full_corpus]
        missing = [kw for kw in keywords if kw not in full_corpus]

        ratio = len(found) / len(keywords)
        score = ratio * 30.0
        return score, missing
