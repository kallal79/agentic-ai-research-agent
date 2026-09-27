"""Wikipedia lookup tool.

Uses the wikipedia-api library, falls back to the REST API,
and ultimately to mock data if nothing else works.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from tools.base import BaseTool, ToolResult, ToolStatus


class WikipediaTool(BaseTool):
    """Look up a topic on Wikipedia and return a structured summary."""

    @property
    def name(self) -> str:
        return "wikipedia"

    @property
    def description(self) -> str:
        return (
            "Fetch a Wikipedia article summary. "
            "Input: 'topic' (str), optional 'sentences' (int, default 5). "
            "Returns {title, summary, url, categories}."
        )

    def execute(self, **kwargs) -> ToolResult:
        topic: str = kwargs.get("topic", "")
        sentences: int = kwargs.get("sentences", 5)

        if not topic:
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.FAILURE,
                error_msg="Missing required parameter: 'topic'",
            )

        # Strategy 1: use the wikipedia-api library
        try:
            return self._via_wikipediaapi(topic, sentences)
        except Exception:
            pass

        # Strategy 2: raw REST call to MediaWiki
        try:
            return self._via_rest(topic, sentences)
        except Exception:
            pass

        # Strategy 3: mock data so the agent never fully stalls
        return self._mock_lookup(topic)

    # ---- implementation strategies ---------------------------------------------

    def _via_wikipediaapi(self, topic: str, sentences: int) -> ToolResult:
        import wikipediaapi

        wiki = wikipediaapi.Wikipedia(
            user_agent="AgenticAI-ResearchAgent/1.0 (student project)",
            language="en",
        )
        page = wiki.page(topic)

        if not page.exists():
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.FAILURE,
                error_msg=f"Wikipedia page not found for '{topic}'.",
                metadata={"topic": topic},
            )

        # Trim to requested sentence count
        summary_text = page.summary
        sentence_list = summary_text.split(". ")
        trimmed = ". ".join(sentence_list[:sentences])
        if not trimmed.endswith("."):
            trimmed += "."

        categories = [c for c in list(page.categories.keys())[:8]]

        return ToolResult(
            tool_name=self.name,
            status=ToolStatus.SUCCESS,
            data={
                "title": page.title,
                "summary": trimmed,
                "url": page.fullurl,
                "categories": categories,
            },
            metadata={"topic": topic, "source": "wikipedia-api"},
        )

    def _via_rest(self, topic: str, sentences: int) -> ToolResult:
        import requests

        url = (
            "https://en.wikipedia.org/api/rest_v1/page/summary/"
            + topic.replace(" ", "_")
        )
        resp = requests.get(url, timeout=10, headers={
            "User-Agent": "AgenticAI-ResearchAgent/1.0 (student project)"
        })
        resp.raise_for_status()
        data = resp.json()

        summary = data.get("extract", "")
        sentence_list = summary.split(". ")
        trimmed = ". ".join(sentence_list[:sentences])
        if not trimmed.endswith("."):
            trimmed += "."

        return ToolResult(
            tool_name=self.name,
            status=ToolStatus.SUCCESS,
            data={
                "title": data.get("title", topic),
                "summary": trimmed,
                "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                "categories": [],
            },
            metadata={"topic": topic, "source": "rest-api"},
        )

    def _mock_lookup(self, topic: str) -> ToolResult:
        return ToolResult(
            tool_name=self.name,
            status=ToolStatus.PARTIAL,
            data={
                "title": topic.title(),
                "summary": (
                    f"{topic.title()} is a notable subject with significant developments "
                    f"in recent years. It has attracted attention from researchers, "
                    f"industry leaders, and policymakers worldwide. Key areas of focus "
                    f"include innovation, scalability, and societal impact."
                ),
                "url": f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}",
                "categories": ["General knowledge"],
            },
            error_msg="Used mock data (both wikipedia-api and requests unavailable).",
            metadata={"topic": topic, "mock": True},
        )
