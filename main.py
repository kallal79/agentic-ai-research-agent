#!/usr/bin/env python3
"""CLI entry point for the agentic AI research agent.

Run with no args for interactive mode, or pass a goal directly:
    python main.py "Research AI trends in 2025"
    python main.py --demo
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time

# ── Fix Windows console encoding ──────────────────────────────────────────
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# ── Rich console for beautiful terminal output ────────────────────────────
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.logging import RichHandler
    from rich.markdown import Markdown
    from rich import box

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from agent.orchestrator import AgentOrchestrator
from report.builder import ReportBuilder


# ── Demo goals for showcasing ─────────────────────────────────────────────
DEMO_GOALS = [
    "Research and summarize the top 3 developments in artificial intelligence from the last week.",
    "Given a company name Tesla, produce a short competitive-landscape brief using public web data.",
    "Plan a 3-day itinerary for Tokyo, respecting a budget of $500 and interests in food and culture.",
]


def setup_logging(verbose: bool = False) -> None:
    """Configure logging: rich handler if available, else basic."""
    level = logging.DEBUG if verbose else logging.INFO

    if RICH_AVAILABLE:
        logging.basicConfig(
            level=level,
            format="%(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(
                rich_tracebacks=True,
                show_path=False,
                markup=True,
            )],
        )
    else:
        logging.basicConfig(
            level=level,
            format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        )

    # Quiet noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def print_banner() -> None:
    """Print the project banner."""
    if RICH_AVAILABLE:
        console = Console()
        banner = Text()
        banner.append("Agentic AI Research Agent", style="bold cyan")
        banner.append("\nAutonomous Planning | Tool Execution | Error Recovery", style="dim")
        banner.append("\nTake-Home Assignment", style="dim italic")
        console.print(Panel(banner, box=box.ROUNDED, border_style="cyan", padding=(1, 2)))
    else:
        print("=" * 60)
        print("  Agentic AI Research Agent")
        print("  Autonomous Planning | Tool Execution | Error Recovery")
        print("  Take-Home Assignment")
        print("=" * 60)


def print_plan(plan: list, console=None) -> None:
    """Display the plan in a clean table."""
    if RICH_AVAILABLE and console:
        table = Table(
            title="Execution Plan",
            box=box.ROUNDED,
            show_lines=True,
            title_style="bold yellow",
        )
        table.add_column("Step", style="bold cyan", width=5, justify="center")
        table.add_column("Description", style="white", min_width=40)
        table.add_column("Tool", style="green")
        table.add_column("Fallback", style="dim yellow")

        for step in plan:
            table.add_row(
                str(step["step_id"]),
                step["description"][:65],
                step["tool"],
                step.get("fallback_tool") or "—",
            )
        console.print(table)
    else:
        print("\nExecution Plan:")
        for step in plan:
            fb = step.get("fallback_tool") or "none"
            print(f"  [{step['step_id']}] {step['description'][:65]}")
            print(f"      Tool: {step['tool']} | Fallback: {fb}")


def print_results(report_data: dict, console=None) -> None:
    """Display final results summary."""
    stats = report_data.get("statistics", {})

    if RICH_AVAILABLE and console:
        # Stats table
        table = Table(
            title="Execution Statistics",
            box=box.ROUNDED,
            title_style="bold green",
        )
        table.add_column("Metric", style="bold")
        table.add_column("Value", style="cyan", justify="right")
        table.add_row("Total Steps", str(stats.get("total_steps", 0)))
        table.add_row("Succeeded", str(stats.get("succeeded", 0)))
        table.add_row("Failed", str(stats.get("failed", 0)))
        table.add_row("Total Retries", str(stats.get("total_retries", 0)))
        table.add_row("Success Rate", stats.get("success_rate", "N/A"))
        table.add_row("Duration", f"{report_data['timing']['duration_seconds']}s")
        console.print(table)

        # Recovery events
        recovery = report_data.get("recovery_events", [])
        if recovery:
            console.print("\n[bold yellow]Error Recovery Events:[/bold yellow]")
            for evt in recovery:
                console.print(
                    f"  Step {evt['step_id']}: "
                    f"[bold]{evt['action']}[/bold] — {evt['reason'][:80]}"
                )
    else:
        print("\nExecution Statistics:")
        for k, v in stats.items():
            print(f"  {k}: {v}")


def run_agent(goal: str, verbose: bool = False) -> dict:
    """Run the agent on a given goal and return the report data."""
    console = Console() if RICH_AVAILABLE else None

    if RICH_AVAILABLE and console:
        console.print(f"\n[bold cyan]Goal:[/bold cyan] {goal}\n")
    else:
        print(f"\nGoal: {goal}\n")

    # Create and run agent
    agent = AgentOrchestrator(simulate_failure=True)

    # Show plan
    plan = agent.planner.create_plan(goal)
    plan_dicts = [s.to_dict() for s in plan]
    print_plan(plan_dicts, console)

    if RICH_AVAILABLE and console:
        console.print("\n[bold]Executing plan...[/bold]\n")
    else:
        print("\nExecuting plan...\n")

    # Execute
    report_data = agent.run(goal)

    # Show results
    print_results(report_data, console)

    # Save reports
    builder = ReportBuilder(output_dir="output")
    paths = builder.save(report_data)

    if RICH_AVAILABLE and console:
        console.print(f"\n[bold green]Reports saved:[/bold green]")
        console.print(f"   Markdown: [link=file://{paths['markdown']}]{paths['markdown']}[/link]")
        console.print(f"   JSON:     [link=file://{paths['json']}]{paths['json']}[/link]")
    else:
        print(f"\nReports saved:")
        print(f"   Markdown: {paths['markdown']}")
        print(f"   JSON:     {paths['json']}")

    return report_data


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Agentic AI Research Agent — Autonomous Planning & Tool Use",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "Research AI trends in 2025"
  python main.py --demo
  python main.py --demo --goal-index 1
  python main.py -v "Plan a trip to Tokyo"
        """,
    )
    parser.add_argument("goal", nargs="?", help="The goal for the agent (natural language)")
    parser.add_argument("--demo", action="store_true", help="Run a pre-built demo goal")
    parser.add_argument("--goal-index", type=int, default=0, help="Which demo goal to run (0-2)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument("--all-demos", action="store_true", help="Run ALL demo goals sequentially")

    args = parser.parse_args()
    setup_logging(args.verbose)
    print_banner()

    if args.all_demos:
        for i, goal in enumerate(DEMO_GOALS):
            console = Console() if RICH_AVAILABLE else None
            if console:
                console.rule(f"[bold cyan]Demo {i + 1} of {len(DEMO_GOALS)}[/bold cyan]")
            else:
                print(f"\n{'=' * 40} Demo {i + 1} {'=' * 40}")
            run_agent(goal, args.verbose)
        return

    if args.demo:
        idx = max(0, min(args.goal_index, len(DEMO_GOALS) - 1))
        goal = DEMO_GOALS[idx]
    elif args.goal:
        goal = args.goal
    else:
        # Interactive mode
        print("\nEnter your goal (or press Enter for a demo):")
        goal = input("  > ").strip()
        if not goal:
            goal = DEMO_GOALS[0]
            print(f"  Using default: {goal}")

    run_agent(goal, args.verbose)


if __name__ == "__main__":
    main()
