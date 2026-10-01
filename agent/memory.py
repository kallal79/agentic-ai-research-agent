"""Multi-turn session memory for contextual agent reasoning.

Retains entities, research summaries, and key metrics across consecutive runs,
enabling follow-up queries and iterative exploration without starting from scratch.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("agent.memory")


class MemoryEntry:
    """A single record of an executed research session."""

    def __init__(
        self,
        turn_id: int,
        goal: str,
        domain: str,
        summary: str,
        key_entities: List[str],
        timestamp: float,
    ):
        self.turn_id = turn_id
        self.goal = goal
        self.domain = domain
        self.summary = summary
        self.key_entities = key_entities
        self.timestamp = timestamp

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "goal": self.goal,
            "domain": self.domain,
            "summary_snippet": self.summary[:200] + ("..." if len(self.summary) > 200 else ""),
            "key_entities": self.key_entities,
            "timestamp": self.timestamp,
        }


class SessionMemory:
    """Manages short-term conversational context across multiple agent runs."""

    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns
        self.history: List[MemoryEntry] = []
        self._turn_counter = 0

    def add_turn(
        self,
        goal: str,
        domain: str,
        summary: str,
        key_entities: Optional[List[str]] = None,
    ) -> MemoryEntry:
        """Record the outcome of a completed goal."""
        self._turn_counter += 1
        entry = MemoryEntry(
            turn_id=self._turn_counter,
            goal=goal,
            domain=domain,
            summary=summary,
            key_entities=key_entities or [],
            timestamp=time.time(),
        )
        self.history.append(entry)
        if len(self.history) > self.max_turns:
            self.history.pop(0)

        logger.info("SessionMemory: saved turn #%d for goal '%s'", entry.turn_id, goal[:40])
        return entry

    def get_context_for_goal(self, current_goal: str) -> Optional[Dict[str, Any]]:
        """
        Check if previous memory turns contain relevant context or entities
        that should inform the current goal.
        """
        if not self.history:
            return None

        # Look for entity matches in history
        current_lower = current_goal.lower()
        relevant_entries = []

        for entry in reversed(self.history):
            # Check if previous entity is referenced, or if domain aligns
            matches = [e for e in entry.key_entities if e.lower() in current_lower]
            if matches or "compare" in current_lower or "previous" in current_lower or "also" in current_lower:
                relevant_entries.append(entry)

        if not relevant_entries and len(self.history) > 0:
            # Default to the most recent turn if user says 'it', 'them', or follow-up connectors
            if any(w in current_lower.split() for w in ("it", "its", "them", "now", "compare", "also", "further")):
                relevant_entries.append(self.history[-1])

        if relevant_entries:
            top_match = relevant_entries[0]
            return {
                "prior_turn_id": top_match.turn_id,
                "prior_goal": top_match.goal,
                "prior_entities": top_match.key_entities,
                "context_snippet": top_match.summary[:300],
            }

        return None

    def clear(self) -> None:
        """Reset memory."""
        self.history.clear()
        self._turn_counter = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_turns": len(self.history),
            "turns": [entry.to_dict() for entry in self.history],
        }
