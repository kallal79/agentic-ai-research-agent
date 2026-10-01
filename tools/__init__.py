"""
Tools package — each tool implements the BaseTool interface.
Available tools: WebSearchTool, WikipediaTool, CalculatorTool, TextSummarizerTool
"""

from tools.base import BaseTool, ToolResult
from tools.web_search import WebSearchTool
from tools.wikipedia_tool import WikipediaTool
from tools.calculator import CalculatorTool
from tools.text_summarizer import TextSummarizerTool
from tools.arxiv_tool import ArxivResearchTool
from tools.code_executor import CodeExecutorTool

__all__ = [
    "BaseTool",
    "ToolResult",
    "WebSearchTool",
    "WikipediaTool",
    "CalculatorTool",
    "TextSummarizerTool",
    "ArxivResearchTool",
    "CodeExecutorTool",
]
