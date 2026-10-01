"""Robustness, Fuzzing, and Random Data Property Tests.

Validates that the Agentic AI Research Agent:
1. Never raises unhandled exceptions on random, noisy, or adversarial inputs.
2. Gracefully sanitizes empty, whitespace-only, and unicode/emoji goals.
3. Successfully parses and decomposes randomized multi-domain queries.
4. Generates valid synthetic labeled traces without schema violations.
"""

import pytest
import random

from agent.orchestrator import AgentOrchestrator
from agent.planner import Planner
from generate_random_data import (
    generate_synthetic_traces,
    RANDOM_ACADEMIC_TOPICS,
    RANDOM_CODE_TASKS,
    RANDOM_EDGE_CASES,
)


@pytest.fixture(scope="module")
def shared_agent():
    return AgentOrchestrator(simulate_failure=False)


def test_random_synthetic_trace_generation():
    traces = generate_synthetic_traces(count_per_category=4)
    assert len(traces) >= 20
    for t in traces:
        assert "trace_id" in t
        assert "goal_input" in t
        assert "domain_intent" in t
        assert "tool_sequence" in t
        assert "precision_label" in t
        assert t["precision_label"] in ("TP", "FP", "TN", "FN")


def test_empty_and_whitespace_random_input(shared_agent):
    for empty_val in ["", "   ", "\t\n\r", "          "]:
        report = shared_agent.run(empty_val, enable_reflection=False)
        assert "statistics" in report
        assert report["statistics"]["total_steps"] > 0
        assert report["statistics"]["succeeded"] > 0


def test_random_keyboard_mash_and_symbols(shared_agent):
    gibberish_inputs = [
        "asdfghjkl qwertyuiop zxcvbnm",
        "1234567890 !@#$%^&*()_+",
        "`~-=[]\\;',./{}|:\"<>?",
        "zzzzzzzzzzzzzzzzzzzzzzzzzz",
    ]
    for gibberish in gibberish_inputs:
        report = shared_agent.run(gibberish, enable_reflection=False)
        assert "step_results" in report
        assert len(report["step_results"]) > 0


def test_random_unicode_and_adversarial_payloads(shared_agent):
    adversarial_inputs = [
        "🚀 🤖 🧠 ⚡ 🔬 💻",
        "SELECT * FROM users WHERE 1=1; DROP TABLE data; --",
        "<script>console.log('xss_test')</script>",
        "python " * 20 + "code compute variance",
    ]
    for adv in adversarial_inputs:
        report = shared_agent.run(adv, enable_reflection=False)
        assert report["statistics"]["total_steps"] > 0


def test_randomized_academic_planning():
    planner = Planner()
    for _ in range(5):
        topic = random.choice(RANDOM_ACADEMIC_TOPICS)
        plan = planner.create_plan(f"Query arXiv academic papers on {topic}")
        tools = [s.tool_name for s in plan]
        assert "arxiv_search" in tools
        assert "text_summarizer" in tools


def test_randomized_code_planning():
    planner = Planner()
    for _ in range(5):
        task = random.choice(RANDOM_CODE_TASKS)
        plan = planner.create_plan(f"Run python code script to {task}")
        tools = [s.tool_name for s in plan]
        assert "code_executor" in tools
        assert "text_summarizer" in tools
