"""Unit and integration tests for newly implemented Agentic AI features:
- ArxivResearchTool
- Sandboxed CodeExecutorTool
- Self-Reflection & Dynamic Replanning Engine
- Multi-Turn Session Memory
- Planner academic and data analysis intents
"""

import pytest
from unittest.mock import MagicMock, patch

from tools.arxiv_tool import ArxivResearchTool
from tools.code_executor import CodeExecutorTool
from agent.reflection import ReflectionEngine, ReflectionReport
from agent.memory import SessionMemory
from agent.planner import Planner, PlanStep, StepStatus
from agent.orchestrator import AgentOrchestrator


# ============================================================================
# 1. ArxivResearchTool Tests
# ============================================================================

def test_arxiv_tool_initialization():
    tool = ArxivResearchTool()
    assert tool.name == "arxiv_search"
    assert "arxiv" in tool.description.lower()


def test_arxiv_tool_mock_query():
    xml_data = b"""<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <title>ArXiv Query Results</title>
      <entry>
        <title>Quantum Supremacy in Agentic Systems</title>
        <id>http://arxiv.org/abs/2401.0001</id>
        <published>2024-01-01T00:00:00Z</published>
        <summary>Demonstrating quantum computational advantage in distributed multi-agent systems.</summary>
        <author><name>Dr. Alice Quantum</name></author>
        <link rel="alternate" href="https://arxiv.org/abs/2401.0001" type="text/html"/>
        <link title="pdf" href="https://arxiv.org/pdf/2401.0001.pdf" type="application/pdf"/>
      </entry>
    </feed>
    """
    tool = ArxivResearchTool()
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = xml_data
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        res = tool.safe_execute(query="quantum multi-agent", max_results=2)
        assert res.ok is True
        assert isinstance(res.data, list)
        assert len(res.data) == 1
        paper = res.data[0]
        assert paper["title"] == "Quantum Supremacy in Agentic Systems"
        assert "Dr. Alice Quantum" in paper["authors"]
        assert "2401.0001" in paper["url"]


def test_arxiv_tool_fallback_on_network_error():
    tool = ArxivResearchTool()
    with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
        res = tool.safe_execute(query="neural radiance fields")
        assert res.ok is True
        assert isinstance(res.data, list)
        assert len(res.data) > 0
        assert "title" in res.data[0]
        assert res.metadata.get("fallback") is True


# ============================================================================
# 2. Sandboxed CodeExecutorTool Tests
# ============================================================================

def test_code_executor_valid_calculation():
    tool = CodeExecutorTool()
    code = """
numbers = [10, 20, 30, 40]
avg = sum(numbers) / len(numbers)
print(f"Calculated average is {avg}")
result = {"average": avg, "total": sum(numbers)}
"""
    res = tool.safe_execute(code=code)
    assert res.ok is True
    assert "Calculated average is 25.0" in res.data["output"]
    assert res.data["result"]["average"] == 25.0
    assert res.data["result"]["total"] == 100


def test_code_executor_security_violation_import():
    tool = CodeExecutorTool()
    malicious_code = "import os\nos.system('dir')"
    res = tool.safe_execute(code=malicious_code)
    assert res.ok is False
    assert "Security Violation" in res.error_msg
    assert "import" in res.error_msg.lower()


def test_code_executor_security_violation_dunder():
    tool = CodeExecutorTool()
    exploit_code = "x = ().__class__.__bases__[0].__subclasses__()"
    res = tool.safe_execute(code=exploit_code)
    assert res.ok is False
    assert "Security Violation" in res.error_msg


# ============================================================================
# 3. Self-Reflection & Dynamic Replanning Tests
# ============================================================================

def test_reflection_engine_high_confidence():
    engine = ReflectionEngine()
    goal = "Research transformer architecture and attention mechanisms"
    steps = [
        PlanStep(step_id=1, description="Step 1", tool_name="web_search", status=StepStatus.SUCCESS),
        PlanStep(step_id=2, description="Step 2", tool_name="wikipedia", status=StepStatus.SUCCESS),
    ]
    collected_text = [
        "Transformer architecture relies on self-attention mechanisms allowing models to process tokens in parallel.",
        "Attention mechanisms revolutionized natural language processing and multimodal deep learning networks.",
        "Extensive experiments show transformer architecture surpasses recurrent neural networks significantly.",
    ]
    report = engine.reflect(goal, steps, collected_text)
    assert report.completeness_score >= 70.0
    assert report.confidence_level in ("HIGH", "MODERATE")
    assert report.recommended_action == "PROCEED_TO_SYNTHESIS"
    assert report.follow_up_step is None


def test_reflection_engine_gap_detection_and_replan():
    engine = ReflectionEngine()
    goal = "Investigate quantum computing superconducting qubits and error correction"
    # Provide sparse text missing key keywords
    steps = [
        PlanStep(step_id=1, description="Step 1", tool_name="web_search", status=StepStatus.FAILED),
    ]
    collected_text = ["Short note without key concepts."]
    report = engine.reflect(goal, steps, collected_text)
    assert report.completeness_score < 75.0
    assert len(report.identified_gaps) > 0
    assert report.recommended_action == "DYNAMIC_REPLAN_INJECTED"
    assert report.follow_up_step is not None
    assert report.follow_up_step.step_id == 2
    assert "web_search" in report.follow_up_step.tool_name


# ============================================================================
# 4. Multi-Turn Session Memory Tests
# ============================================================================

def test_session_memory_operations():
    memory = SessionMemory(max_turns=3)
    memory.add_turn(
        goal="Analyze DeepSeek-V3 architecture",
        domain="academic",
        summary="DeepSeek-V3 uses Multi-Head Latent Attention and Mixture-of-Experts with 671B parameters.",
        key_entities=["DeepSeek", "MLA", "MoE"],
    )
    assert len(memory.history) == 1

    # Follow-up referencing entity
    ctx = memory.get_context_for_goal("Compare DeepSeek with Llama 3")
    assert ctx is not None
    assert "DeepSeek" in ctx["prior_entities"]
    assert "DeepSeek-V3" in ctx["prior_goal"]

    # Test overflow eviction
    memory.add_turn("Goal 2", "research", "Summary 2")
    memory.add_turn("Goal 3", "research", "Summary 3")
    memory.add_turn("Goal 4", "research", "Summary 4")
    assert len(memory.history) == 3
    assert memory.history[0].goal == "Goal 2"


# ============================================================================
# 5. Planner Academic and Data Analysis Intents
# ============================================================================

def test_planner_academic_intent():
    planner = Planner()
    plan = planner.create_plan("Find latest arXiv academic paper on quantum neural networks")
    tool_names = [s.tool_name for s in plan]
    assert "arxiv_search" in tool_names
    assert "wikipedia" in tool_names
    assert "text_summarizer" in tool_names


def test_planner_data_analysis_intent():
    planner = Planner()
    plan = planner.create_plan("Execute python code script to compute statistical benchmarks on dataset")
    tool_names = [s.tool_name for s in plan]
    assert "code_executor" in tool_names
    assert "text_summarizer" in tool_names


# ============================================================================
# 6. End-to-End Orchestrator Integration Test
# ============================================================================

def test_orchestrator_full_flow():
    agent = AgentOrchestrator(simulate_failure=False)
    report = agent.run("Evaluate quantum neural network paper", enable_reflection=True)

    assert "plan" in report
    assert "step_results" in report
    assert "reflection" in report
    assert report["reflection"] is not None
    assert "session_memory" in report
    assert report["session_memory"]["total_turns"] >= 1
    assert "statistics" in report
