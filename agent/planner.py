"""Goal decomposition and plan generation.

The Planner looks at a goal, figures out what kind of task it is
(research, competitive analysis, travel), and generates a list of
steps with tool assignments. It's rule-based for now - an LLM-backed
version would be a natural upgrade.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRIED = "retried"


@dataclass
class PlanStep:
    """A single executable step in the agent's plan."""
    step_id: int
    description: str
    tool_name: str          # which tool to invoke
    tool_kwargs: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[int] = field(default_factory=list)  # step_ids this depends on
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    retry_count: int = 0
    max_retries: int = 2
    fallback_tool: Optional[str] = None   # tool to try if primary fails
    fallback_kwargs: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "description": self.description,
            "tool": self.tool_name,
            "tool_kwargs": self.tool_kwargs,
            "depends_on": self.depends_on,
            "status": self.status.value,
            "retry_count": self.retry_count,
            "fallback_tool": self.fallback_tool,
        }


# ---- keyword / intent classifiers ------------------------------------------

_RESEARCH_KEYWORDS = [
    "research", "summarize", "summary", "developments", "trends",
    "news", "latest", "recent", "find", "discover", "explore",
    "report", "overview", "analyze", "analysis", "investigate",
]
_COMPETITIVE_KEYWORDS = [
    "competitive", "competitor", "landscape", "company", "companies",
    "market", "business", "industry", "compare", "comparison", "versus",
    "brand", "brands",
]
_TRAVEL_KEYWORDS = [
    "travel", "itinerary", "trip", "city", "hotel", "flight",
    "budget", "plan", "visit", "tourism", "tourist", "destination",
]
_CALCULATION_KEYWORDS = [
    "calculate", "compute", "math", "percentage", "cost", "budget",
    "price", "total", "average", "median", "ratio", "growth",
]


class Planner:
    """
    Analyse a user goal and produce an ordered plan of PlanSteps.

    The planner:
      1. Extracts key topics from the goal.
      2. Classifies the goal intent (research, competitive, travel, …).
      3. Generates an appropriate sequence of tool-backed steps.
      4. Adds fallback strategies for robustness.
    """

    def create_plan(self, goal: str) -> List[PlanStep]:
        """Main entry point: goal string → list of PlanSteps."""
        goal_lower = goal.lower()
        topics = self._extract_topics(goal)
        intent = self._classify_intent(goal_lower)

        if intent == "competitive":
            return self._plan_competitive(goal, topics)
        elif intent == "travel":
            return self._plan_travel(goal, topics)
        else:
            # Default to research plan (most general)
            return self._plan_research(goal, topics)

    # ---- intent classification -------------------------------------------------

    @staticmethod
    def _classify_intent(goal_lower: str) -> str:
        scores = {
            "research": sum(1 for kw in _RESEARCH_KEYWORDS if kw in goal_lower),
            "competitive": sum(1 for kw in _COMPETITIVE_KEYWORDS if kw in goal_lower),
            "travel": sum(1 for kw in _TRAVEL_KEYWORDS if kw in goal_lower),
        }
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "research"

    # ---- topic extraction ------------------------------------------------------

    @staticmethod
    def _extract_topics(goal: str) -> List[str]:
        """Pull out likely topic phrases from the goal."""
        # Remove common filler words and extract noun phrases heuristically
        cleaned = re.sub(
            r"\b(research|summarize|find|give|me|the|a|an|and|or|in|on|of|"
            r"from|for|about|top|latest|recent|last|week|month|year|"
            r"produce|create|make|build|plan|identify|suggest|"
            r"please|could|would|can|do|using|public|web|data|"
            r"given|short|brief|3|three|two|2|day|days|"
            r"developments|issues|fixes|quality|potential)\b",
            "",
            goal,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r"[^\w\s]", "", cleaned)
        tokens = cleaned.split()
        # Group remaining tokens into topic phrases
        topics = []
        current = []
        for tok in tokens:
            if len(tok) > 2:
                current.append(tok)
            else:
                if current:
                    topics.append(" ".join(current))
                    current = []
        if current:
            topics.append(" ".join(current))

        # Deduplicate and filter out very short/noisy topics
        seen = set()
        unique = []
        for t in topics:
            t_clean = t.strip().lower()
            if t_clean and t_clean not in seen and len(t_clean) > 3:
                seen.add(t_clean)
                unique.append(t.strip())
        return unique if unique else [goal.strip()[:60]]

    # ---- plan templates --------------------------------------------------------

    def _plan_research(self, goal: str, topics: List[str]) -> List[PlanStep]:
        """Generate a research-oriented plan."""
        steps: List[PlanStep] = []
        step_id = 1
        primary_topic = " ".join(topics) if topics else goal[:60]

        # Step 1: Web search for the topic
        steps.append(PlanStep(
            step_id=step_id,
            description=f"Search the web for recent information on: {primary_topic}",
            tool_name="web_search",
            tool_kwargs={"query": f"{primary_topic} latest developments 2025", "max_results": 5},
            fallback_tool="wikipedia",
            fallback_kwargs={"topic": primary_topic, "sentences": 8},
        ))
        step_id += 1

        # Step 2: Wikipedia deep-dive on each topic
        for topic in topics[:3]:  # limit to 3 topics
            steps.append(PlanStep(
                step_id=step_id,
                description=f"Look up background information on Wikipedia: {topic}",
                tool_name="wikipedia",
                tool_kwargs={"topic": topic, "sentences": 6},
                depends_on=[1],  # after the web search
            ))
            step_id += 1

        # Step 3: Summarize all collected information
        steps.append(PlanStep(
            step_id=step_id,
            description="Summarize all gathered information into a concise overview",
            tool_name="text_summarizer",
            tool_kwargs={"num_sentences": 4},  # text will be injected by executor
            depends_on=list(range(1, step_id)),
        ))
        step_id += 1

        # Step 4: Calculate some metric (e.g., word count ratio)
        steps.append(PlanStep(
            step_id=step_id,
            description="Calculate summary compression ratio (original vs summary word count)",
            tool_name="calculator",
            tool_kwargs={"expression": "0"},  # placeholder — executor injects real values
            depends_on=[step_id - 1],
        ))

        return steps

    def _plan_competitive(self, goal: str, topics: List[str]) -> List[PlanStep]:
        """Generate a competitive-analysis plan."""
        steps: List[PlanStep] = []
        step_id = 1
        company = " ".join(topics) if topics else "the company"

        # Step 1: Web search for the company
        steps.append(PlanStep(
            step_id=step_id,
            description=f"Search the web for competitive landscape of: {company}",
            tool_name="web_search",
            tool_kwargs={"query": f"{company} competitors market analysis 2025", "max_results": 5},
            fallback_tool="wikipedia",
            fallback_kwargs={"topic": company, "sentences": 8},
        ))
        step_id += 1

        # Step 2: Wikipedia lookup for the company
        steps.append(PlanStep(
            step_id=step_id,
            description=f"Get background from Wikipedia on: {company}",
            tool_name="wikipedia",
            tool_kwargs={"topic": company, "sentences": 6},
        ))
        step_id += 1

        # Step 3: Search for competitors
        steps.append(PlanStep(
            step_id=step_id,
            description=f"Search the web for top competitors of: {company}",
            tool_name="web_search",
            tool_kwargs={"query": f"top competitors of {company} 2025", "max_results": 5},
            depends_on=[1],
            fallback_tool="wikipedia",
            fallback_kwargs={"topic": f"{company} competitors", "sentences": 6},
        ))
        step_id += 1

        # Step 4: Summarize
        steps.append(PlanStep(
            step_id=step_id,
            description="Compile and summarize all competitive intelligence",
            tool_name="text_summarizer",
            tool_kwargs={"num_sentences": 5},
            depends_on=list(range(1, step_id)),
        ))
        step_id += 1

        # Step 5: Calculate a metric
        steps.append(PlanStep(
            step_id=step_id,
            description="Calculate total data sources used and summary compression ratio",
            tool_name="calculator",
            tool_kwargs={"expression": "0"},
            depends_on=[step_id - 1],
        ))

        return steps

    def _plan_travel(self, goal: str, topics: List[str]) -> List[PlanStep]:
        """Generate a travel-planning plan."""
        steps: List[PlanStep] = []
        step_id = 1
        destination = " ".join(topics) if topics else "a popular city"

        # Step 1: Web search for the destination
        steps.append(PlanStep(
            step_id=step_id,
            description=f"Search the web for top attractions and travel tips: {destination}",
            tool_name="web_search",
            tool_kwargs={"query": f"{destination} top attractions travel guide 2025", "max_results": 5},
            fallback_tool="wikipedia",
            fallback_kwargs={"topic": destination, "sentences": 8},
        ))
        step_id += 1

        # Step 2: Wikipedia on the city
        steps.append(PlanStep(
            step_id=step_id,
            description=f"Get background info from Wikipedia: {destination}",
            tool_name="wikipedia",
            tool_kwargs={"topic": destination, "sentences": 8},
        ))
        step_id += 1

        # Step 3: Search for budget info
        steps.append(PlanStep(
            step_id=step_id,
            description=f"Search for budget travel information: {destination}",
            tool_name="web_search",
            tool_kwargs={"query": f"{destination} budget travel cost per day 2025", "max_results": 3},
            depends_on=[1],
            fallback_tool="wikipedia",
            fallback_kwargs={"topic": f"Tourism in {destination}", "sentences": 5},
        ))
        step_id += 1

        # Step 4: Budget calculation
        steps.append(PlanStep(
            step_id=step_id,
            description="Estimate total trip cost (3 days × estimated daily budget)",
            tool_name="calculator",
            tool_kwargs={"expression": "3 * 150"},  # $150/day default estimate
            depends_on=[3],
        ))
        step_id += 1

        # Step 5: Summarize
        steps.append(PlanStep(
            step_id=step_id,
            description="Summarize all travel information into a concise itinerary overview",
            tool_name="text_summarizer",
            tool_kwargs={"num_sentences": 5},
            depends_on=list(range(1, step_id)),
        ))

        return steps
