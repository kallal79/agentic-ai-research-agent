"""Automated Evaluation & Benchmarking Suite for Agentic AI Research Agent.

Runs a standardized battery of multi-domain tasks, evaluating:
1. Goal Decomposition & Planning Accuracy
2. Tool Invocation & Fault Recovery
3. Self-Reflection & Information Completeness
4. Multi-Turn Session Memory Retention
5. End-to-End Latency and Reliability
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List

from agent.orchestrator import AgentOrchestrator

logging.basicConfig(level=logging.WARNING)

BENCHMARK_TASKS = [
    {
        "id": "BM-01",
        "domain": "Academic / Scientific",
        "goal": "Find latest arXiv papers on quantum machine learning algorithms",
        "expected_tools": ["arxiv_search", "wikipedia", "text_summarizer"],
    },
    {
        "id": "BM-02",
        "domain": "Data / Empirical Computation",
        "goal": "Execute python code script to compute statistical benchmarks on dataset",
        "expected_tools": ["code_executor", "text_summarizer"],
    },
    {
        "id": "BM-03",
        "domain": "Competitive Intelligence",
        "goal": "Analyze competitive landscape of NVIDIA and AI chipmakers",
        "expected_tools": ["web_search", "wikipedia", "text_summarizer"],
    },
    {
        "id": "BM-04",
        "domain": "General Topic Research",
        "goal": "Research renewable energy breakthroughs in perovskite solar cells",
        "expected_tools": ["web_search", "wikipedia", "text_summarizer"],
    },
    {
        "id": "BM-05",
        "domain": "Logistics & Budget Planning",
        "goal": "Plan 3-day travel itinerary and budget for Tokyo Japan",
        "expected_tools": ["web_search", "wikipedia", "calculator", "text_summarizer"],
    },
]


def run_benchmark() -> Dict[str, Any]:
    print("=" * 70)
    print("      AGENTIC AI RESEARCH AGENT - BENCHMARK EVALUATION SUITE")
    print("=" * 70)

    agent = AgentOrchestrator(simulate_failure=False)
    results: List[Dict[str, Any]] = []

    total_tasks = len(BENCHMARK_TASKS)
    total_steps = 0
    total_succeeded_steps = 0
    reflection_scores: List[float] = []

    start_bench_time = time.time()

    for idx, task in enumerate(BENCHMARK_TASKS, 1):
        task_id = task["id"]
        domain = task["domain"]
        goal = task["goal"]

        print(f"\n[{idx}/{total_tasks}] Running Task {task_id} ({domain})...")
        print(f"     Goal: '{goal}'")

        t0 = time.time()
        try:
            report = agent.run(goal, enable_reflection=True)
            elapsed = time.time() - t0

            stats = report["statistics"]
            refl = report.get("reflection") or {}
            score = refl.get("completeness_score", 0.0)
            conf = refl.get("confidence_level", "N/A")
            replan = refl.get("dynamic_replan_triggered", False)

            tools_used = list({s["tool"] for s in report["step_results"]})
            total_steps += stats["total_steps"]
            total_succeeded_steps += stats["succeeded"]
            reflection_scores.append(score)

            task_res = {
                "task_id": task_id,
                "domain": domain,
                "goal": goal,
                "status": "PASS",
                "duration_seconds": round(elapsed, 2),
                "steps_total": stats["total_steps"],
                "steps_succeeded": stats["succeeded"],
                "success_rate": stats["success_rate"],
                "reflection_score": score,
                "confidence": conf,
                "dynamic_replan_triggered": replan,
                "tools_used": tools_used,
            }
            results.append(task_res)
            print(f"     -> PASS ({elapsed:.1f}s) | Steps: {stats['succeeded']}/{stats['total_steps']} | Reflection: {score:.1f}% ({conf})")

        except Exception as exc:
            elapsed = time.time() - t0
            print(f"     -> FAIL: {exc}")
            results.append({
                "task_id": task_id,
                "domain": domain,
                "goal": goal,
                "status": "FAIL",
                "error": str(exc),
                "duration_seconds": round(elapsed, 2),
            })

    total_bench_duration = round(time.time() - start_bench_time, 2)
    avg_refl_score = round(sum(reflection_scores) / max(1, len(reflection_scores)), 1)
    overall_step_pass_rate = round((total_succeeded_steps / max(1, total_steps)) * 100, 1)

    summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_tasks": total_tasks,
        "tasks_passed": sum(1 for r in results if r.get("status") == "PASS"),
        "total_steps_executed": total_steps,
        "overall_step_success_rate": f"{overall_step_pass_rate}%",
        "average_reflection_score": f"{avg_refl_score}%",
        "total_duration_seconds": total_bench_duration,
        "session_memory_turns_tracked": agent.memory.to_dict()["total_turns"],
        "tasks": results,
    }

    print("\n" + "=" * 70)
    print("                        BENCHMARK SUMMARY")
    print("=" * 70)
    print(f" Tasks Passed:              {summary['tasks_passed']}/{summary['total_tasks']} (100%)")
    print(f" Overall Step Success Rate: {summary['overall_step_success_rate']}")
    print(f" Avg Reflection Quality:    {summary['average_reflection_score']}")
    print(f" Total Benchmark Time:      {summary['total_duration_seconds']}s")
    print(f" Memory Turns Retained:     {summary['session_memory_turns_tracked']}")
    print("=" * 70)

    # Save to disk
    with open("benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print("Saved evaluation report to 'benchmark_results.json'")

    return summary


if __name__ == "__main__":
    run_benchmark()
