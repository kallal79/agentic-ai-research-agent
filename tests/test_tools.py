"""
test_tools.py — Unit tests for all tools.

Run with:  pytest tests/test_tools.py -v
"""

import pytest
from tools.base import ToolStatus
from tools.web_search import WebSearchTool
from tools.wikipedia_tool import WikipediaTool
from tools.calculator import CalculatorTool
from tools.text_summarizer import TextSummarizerTool


# ── Calculator Tests ──────────────────────────────────────────────────────

class TestCalculatorTool:
    def setup_method(self):
        self.calc = CalculatorTool()

    def test_basic_addition(self):
        result = self.calc.safe_execute(expression="2 + 3")
        assert result.ok
        assert result.data["result"] == 5

    def test_multiplication(self):
        result = self.calc.safe_execute(expression="7 * 8")
        assert result.ok
        assert result.data["result"] == 56

    def test_complex_expression(self):
        result = self.calc.safe_execute(expression="(10 + 5) * 3 - 2")
        assert result.ok
        assert result.data["result"] == 43

    def test_power(self):
        result = self.calc.safe_execute(expression="2 ** 10")
        assert result.ok
        assert result.data["result"] == 1024

    def test_sqrt_function(self):
        result = self.calc.safe_execute(expression="sqrt(144)")
        assert result.ok
        assert result.data["result"] == 12.0

    def test_division_by_zero(self):
        result = self.calc.safe_execute(expression="1 / 0")
        assert not result.ok
        assert result.status == ToolStatus.FAILURE

    def test_empty_expression(self):
        result = self.calc.safe_execute(expression="")
        assert not result.ok

    def test_missing_expression(self):
        result = self.calc.safe_execute()
        assert not result.ok

    def test_unsafe_code_rejected(self):
        result = self.calc.safe_execute(expression="__import__('os').system('echo pwned')")
        assert not result.ok
        assert result.status == ToolStatus.FAILURE

    def test_nested_functions(self):
        result = self.calc.safe_execute(expression="round(sqrt(200), 2)")
        assert result.ok
        assert abs(result.data["result"] - 14.14) < 0.01


# ── Text Summarizer Tests ────────────────────────────────────────────────

class TestTextSummarizerTool:
    def setup_method(self):
        self.summarizer = TextSummarizerTool()

    def test_summarize_long_text(self):
        text = (
            "Artificial intelligence has made remarkable progress in recent years. "
            "Deep learning models have achieved superhuman performance on many tasks. "
            "Natural language processing has been transformed by transformer architectures. "
            "Computer vision systems can now identify objects with incredible accuracy. "
            "Reinforcement learning agents can master complex games and simulations. "
            "The field continues to advance at an unprecedented pace. "
            "Ethical considerations are becoming increasingly important. "
            "Researchers are working on making AI systems more interpretable and fair."
        )
        result = self.summarizer.safe_execute(text=text, num_sentences=3)
        assert result.ok
        assert "summary" in result.data
        assert result.data["word_count"] > 0
        assert len(result.data["key_terms"]) > 0

    def test_short_text_passthrough(self):
        text = "AI is growing fast. Many breakthroughs happened."
        result = self.summarizer.safe_execute(text=text, num_sentences=5)
        assert result.ok
        assert result.data["summary"] == text

    def test_too_short_text(self):
        result = self.summarizer.safe_execute(text="Short")
        assert not result.ok

    def test_empty_text(self):
        result = self.summarizer.safe_execute(text="")
        assert not result.ok

    def test_key_terms_extraction(self):
        text = (
            "Python is a popular programming language. "
            "Python is used for data science. "
            "Python is great for machine learning. "
            "Python has many libraries for AI development."
        )
        result = self.summarizer.safe_execute(text=text, num_sentences=2)
        assert result.ok
        assert "python" in result.data["key_terms"]


# ── Web Search Tests ──────────────────────────────────────────────────────

class TestWebSearchTool:
    def test_deliberate_failure_then_success(self):
        """First call should simulate a timeout; second should work."""
        tool = WebSearchTool(simulate_failure=True)

        # First call — simulated timeout
        result1 = tool.safe_execute(query="test query")
        assert result1.status == ToolStatus.TIMEOUT

        # Second call — should succeed or return partial (mock)
        result2 = tool.safe_execute(query="test query")
        assert result2.ok

    def test_no_failure_simulation(self):
        tool = WebSearchTool(simulate_failure=False)
        result = tool.safe_execute(query="test query")
        assert result.ok  # either real results or mock fallback

    def test_missing_query(self):
        tool = WebSearchTool(simulate_failure=False)
        result = tool.safe_execute()
        assert not result.ok
        assert "Missing" in result.error_msg


# ── Wikipedia Tests ───────────────────────────────────────────────────────

class TestWikipediaTool:
    def setup_method(self):
        self.wiki = WikipediaTool()

    def test_missing_topic(self):
        result = self.wiki.safe_execute()
        assert not result.ok

    def test_lookup_returns_data(self):
        """Should return data via API or mock — never crash."""
        result = self.wiki.safe_execute(topic="Python programming language")
        assert result.ok
        assert "title" in result.data
        assert "summary" in result.data


# ── Base Tool Tests ───────────────────────────────────────────────────────

class TestToolResult:
    def test_ok_for_success(self):
        from tools.base import ToolResult, ToolStatus
        r = ToolResult(tool_name="test", status=ToolStatus.SUCCESS, data="x")
        assert r.ok

    def test_ok_for_partial(self):
        from tools.base import ToolResult, ToolStatus
        r = ToolResult(tool_name="test", status=ToolStatus.PARTIAL, data="x")
        assert r.ok

    def test_not_ok_for_failure(self):
        from tools.base import ToolResult, ToolStatus
        r = ToolResult(tool_name="test", status=ToolStatus.FAILURE)
        assert not r.ok

    def test_to_dict(self):
        from tools.base import ToolResult, ToolStatus
        r = ToolResult(tool_name="test", status=ToolStatus.SUCCESS, data=42)
        d = r.to_dict()
        assert d["tool_name"] == "test"
        assert d["status"] == "success"
        assert d["data"] == 42
