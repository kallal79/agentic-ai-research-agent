"""Base class and result container for all tools.

Every tool inherits from BaseTool and returns a ToolResult.
This gives us a uniform interface so the Executor can call any tool
the same way.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class ToolStatus(Enum):
    """Outcome status of a tool invocation."""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    PARTIAL = "partial"  # some data retrieved, but incomplete


@dataclass
class ToolResult:
    """Container returned by every tool with status, data, and timing info."""
    tool_name: str
    status: ToolStatus
    data: Any = None
    error_msg: str = ""
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        """Convenience check: did the tool succeed (or partially)?"""
        return self.status in (ToolStatus.SUCCESS, ToolStatus.PARTIAL)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for JSON reporting."""
        return {
            "tool_name": self.tool_name,
            "status": self.status.value,
            "data": self.data,
            "error_msg": self.error_msg,
            "duration_ms": round(self.duration_ms, 2),
            "metadata": self.metadata,
        }


class BaseTool(ABC):
    """Abstract base for every tool. Subclasses implement name, description, and execute()."""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        ...

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        ...

    def safe_execute(self, **kwargs) -> ToolResult:
        """Wrapper that catches exceptions and measures how long the tool takes."""
        start = time.perf_counter()
        try:
            result = self.execute(**kwargs)
            result.duration_ms = (time.perf_counter() - start) * 1000
            return result
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.FAILURE,
                data=None,
                error_msg=f"Unhandled exception: {type(exc).__name__}: {exc}",
                duration_ms=elapsed,
            )

    def __repr__(self) -> str:
        return f"<Tool: {self.name}>"
