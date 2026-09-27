"""Web search tool using DuckDuckGo.

Has a deliberate failure mode on the first call so the error-handling
path can be demonstrated during review.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from tools.base import BaseTool, ToolResult, ToolStatus


class WebSearchTool(BaseTool):
    """Search the web via DuckDuckGo and return top results."""

    # --- deliberate failure simulation -------------------------------------------
    # When True, the FIRST call will raise a simulated timeout so reviewers can
    # see the agent's retry / fallback behaviour.  After the first call the flag
    # resets so subsequent searches succeed.
    _simulate_failure: bool = True
    _failure_triggered: bool = False

    def __init__(self, simulate_failure: bool = True):
        self._simulate_failure = simulate_failure
        self._failure_triggered = False

    # --- BaseTool interface ------------------------------------------------------

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return (
            "Search the web using DuckDuckGo. "
            "Input: 'query' (str), optional 'max_results' (int, default 5). "
            "Returns a list of {title, url, snippet} dicts."
        )

    def execute(self, **kwargs) -> ToolResult:
        query: str = kwargs.get("query", "")
        max_results: int = kwargs.get("max_results", 5)

        if not query:
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.FAILURE,
                error_msg="Missing required parameter: 'query'",
            )

        # ---------- deliberate failure on first call ----------
        if self._simulate_failure and not self._failure_triggered:
            self._failure_triggered = True
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.TIMEOUT,
                error_msg=(
                    "Simulated timeout: DuckDuckGo did not respond within 10 s. "
                    "(This failure is intentional to demonstrate error recovery.)"
                ),
                metadata={"simulated": True, "query": query},
            )

        # ---------- real search ----------
        try:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                from duckduckgo_search import DDGS
                with DDGS() as ddgs:
                    raw = list(ddgs.text(query, max_results=max_results))

            results: List[Dict[str, str]] = [
                {
                    "title": r.get("title", ""),
                    "url": r.get("href", r.get("link", "")),
                    "snippet": r.get("body", r.get("snippet", "")),
                }
                for r in raw
            ]

            if not results:
                return ToolResult(
                    tool_name=self.name,
                    status=ToolStatus.PARTIAL,
                    data=[],
                    error_msg="Search returned zero results.",
                    metadata={"query": query},
                )

            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.SUCCESS,
                data=results,
                metadata={"query": query, "count": len(results)},
            )

        except ImportError:
            # Fallback: if duckduckgo-search is not installed, return mock data
            return self._mock_search(query, max_results)

        except Exception as exc:
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.FAILURE,
                error_msg=f"Web search error: {type(exc).__name__}: {exc}",
                metadata={"query": query},
            )

    # ---- fallback mock (so the agent always has something to work with) --------

    def _mock_search(self, query: str, max_results: int) -> ToolResult:
        """Return plausible mock results when the search library is unavailable."""
        mock_data = [
            {
                "title": f"Latest developments in {query} — Overview",
                "url": f"https://example.com/{query.replace(' ', '-')}/overview",
                "snippet": (
                    f"A comprehensive overview of recent trends and breakthroughs "
                    f"related to {query}, including key statistics and expert analysis."
                ),
            },
            {
                "title": f"{query}: Industry Report 2025",
                "url": f"https://example.com/{query.replace(' ', '-')}/report-2025",
                "snippet": (
                    f"This report covers the competitive landscape, market size, "
                    f"and future outlook for {query}."
                ),
            },
            {
                "title": f"Top experts weigh in on {query}",
                "url": f"https://example.com/{query.replace(' ', '-')}/experts",
                "snippet": (
                    f"Leading researchers discuss the most promising directions "
                    f"in {query} and what to expect next."
                ),
            },
        ]
        return ToolResult(
            tool_name=self.name,
            status=ToolStatus.PARTIAL,
            data=mock_data[:max_results],
            error_msg="Used mock data (duckduckgo-search library not available).",
            metadata={"query": query, "mock": True},
        )
