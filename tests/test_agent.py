"""
test_agent.py — Integration tests for the agent pipeline.

Run with:  pytest tests/test_agent.py -v
"""

import pytest
from agent.planner import Planner, PlanStep, StepStatus
from agent.executor import Executor
from agent.error_handler import ErrorHandler, RecoveryEvent
from agent.orchestrator import AgentOrchestrator
from tools.base import ToolResult, ToolStatus


# ── Planner Tests ─────────────────────────────────────────────────────────

class TestPlanner:
    def setup_method(self):
        self.planner = Planner()

    def test_research_plan_creation(self):
        plan = self.planner.create_plan("Research the latest AI developments")
        assert len(plan) >= 3
        assert plan[0].tool_name == "web_search"
        assert any(s.tool_name == "wikipedia" for s in plan)
        assert any(s.tool_name == "text_summarizer" for s in plan)

    def test_competitive_plan_creation(self):
        plan = self.planner.create_plan(
            "Produce a competitive landscape brief for Tesla"
        )
        assert len(plan) >= 3
        # Should include web search for competitors
        web_searches = [s for s in plan if s.tool_name == "web_search"]
        assert len(web_searches) >= 1

    def test_travel_plan_creation(self):
        plan = self.planner.create_plan(
            "Plan a 3-day itinerary for Tokyo"
        )
        assert len(plan) >= 3
        assert any(s.tool_name == "calculator" for s in plan)

    def test_plan_has_fallbacks(self):
        plan = self.planner.create_plan("Research quantum computing")
        # At least the first web search step should have a fallback
        assert plan[0].fallback_tool is not None

    def test_empty_goal_still_produces_plan(self):
        plan = self.planner.create_plan("something")
        assert len(plan) >= 1

    def test_topic_extraction(self):
        topics = Planner._extract_topics("Research artificial intelligence trends")
        assert len(topics) >= 1
        # Should extract "artificial intelligence" or similar
        combined = " ".join(topics).lower()
        assert "artificial" in combined or "intelligence" in combined


# ── ErrorHandler Tests ────────────────────────────────────────────────────

class TestErrorHandler:
    def setup_method(self):
        self.handler = ErrorHandler()

    def test_retry_on_first_failure(self):
        step = PlanStep(step_id=1, description="test", tool_name="web_search")
        result = ToolResult(
            tool_name="web_search",
            status=ToolStatus.FAILURE,
            error_msg="Connection refused",
        )
        action = self.handler.evaluate(step, result)
        assert action == "retry"
        assert step.retry_count == 1

    def test_fallback_after_retries_exhausted(self):
        step = PlanStep(
            step_id=1, description="test", tool_name="web_search",
            fallback_tool="wikipedia", max_retries=0,
        )
        result = ToolResult(
            tool_name="web_search",
            status=ToolStatus.FAILURE,
            error_msg="All retries failed",
        )
        action = self.handler.evaluate(step, result)
        assert action == "fallback"

    def test_skip_when_no_options(self):
        step = PlanStep(
            step_id=1, description="test", tool_name="web_search",
            max_retries=0,
        )
        result = ToolResult(
            tool_name="web_search",
            status=ToolStatus.FAILURE,
            error_msg="Permanent failure",
        )
        action = self.handler.evaluate(step, result)
        assert action == "skip"

    def test_ok_on_success(self):
        step = PlanStep(step_id=1, description="test", tool_name="calculator")
        result = ToolResult(
            tool_name="calculator",
            status=ToolStatus.SUCCESS,
            data=42,
        )
        action = self.handler.evaluate(step, result)
        assert action == "ok"

    def test_recovery_log_populated(self):
        step = PlanStep(step_id=1, description="test", tool_name="web_search")
        result = ToolResult(
            tool_name="web_search",
            status=ToolStatus.TIMEOUT,
            error_msg="Timed out",
        )
        self.handler.evaluate(step, result)
        assert len(self.handler.recovery_log) == 1
        assert self.handler.recovery_log[0].action == "retry"


# ── Full Agent Integration Tests ──────────────────────────────────────────

class TestAgentOrchestrator:
    def test_full_run_completes(self):
        """The agent should complete a full run without crashing."""
        agent = AgentOrchestrator(simulate_failure=True)
        result = agent.run("Research artificial intelligence")
        assert "goal" in result
        assert "plan" in result
        assert "execution_trace" in result
        assert "statistics" in result
        assert result["statistics"]["total_steps"] >= 3

    def test_error_recovery_logged(self):
        """The deliberate failure should trigger at least one recovery event."""
        agent = AgentOrchestrator(simulate_failure=True)
        result = agent.run("Research machine learning")
        recovery = result.get("recovery_events", [])
        assert len(recovery) >= 1, "Expected at least one recovery event from simulated failure"

    def test_no_failure_mode(self):
        """Without simulated failures, everything should succeed."""
        agent = AgentOrchestrator(simulate_failure=False)
        result = agent.run("Research Python programming")
        stats = result["statistics"]
        # All steps should succeed or at least not crash
        assert int(stats["failed"]) == 0 or stats["success_rate"] != "0.0%"

    def test_competitive_goal(self):
        agent = AgentOrchestrator(simulate_failure=False)
        result = agent.run("Produce a competitive landscape brief for Apple")
        assert result["statistics"]["total_steps"] >= 3

    def test_report_structure(self):
        agent = AgentOrchestrator(simulate_failure=False)
        result = agent.run("Research quantum computing")
        # Check all required keys
        required_keys = [
            "goal", "plan", "execution_trace",
            "recovery_events", "step_results", "statistics",
            "timing", "tools_available",
        ]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"
