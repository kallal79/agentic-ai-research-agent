"""Safe math expression evaluator.

Uses Python's AST module instead of eval() so we don't accidentally
run arbitrary code. Supports basic arithmetic and common math functions.
"""

from __future__ import annotations

import ast
import math
import operator
from typing import Any, Dict

from tools.base import BaseTool, ToolResult, ToolStatus

# Allowed operators for safe evaluation
_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

# Allowed function names
_SAFE_FUNCTIONS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "ceil": math.ceil,
    "floor": math.floor,
    "pow": math.pow,
    "pi": math.pi,
    "e": math.e,
}


class CalculatorTool(BaseTool):
    """Safely evaluate mathematical expressions."""

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return (
            "Evaluate a mathematical expression safely. "
            "Input: 'expression' (str, e.g. '(15 * 3) + sqrt(144)'). "
            "Supports +, -, *, /, //, %, **, and functions: "
            "abs, round, min, max, sqrt, log, log10, ceil, floor, pow, pi, e."
        )

    def execute(self, **kwargs) -> ToolResult:
        expression: str = kwargs.get("expression", "")

        if not expression:
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.FAILURE,
                error_msg="Missing required parameter: 'expression'",
            )

        try:
            result = self._safe_eval(expression)
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.SUCCESS,
                data={"expression": expression, "result": result},
                metadata={"expression": expression},
            )
        except (ValueError, TypeError, ZeroDivisionError, OverflowError) as exc:
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.FAILURE,
                error_msg=f"Math error: {exc}",
                metadata={"expression": expression},
            )
        except Exception as exc:
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.FAILURE,
                error_msg=f"Evaluation failed: {type(exc).__name__}: {exc}",
                metadata={"expression": expression},
            )

    # ---- safe AST-based evaluator ----------------------------------------------

    def _safe_eval(self, expr: str) -> float:
        """Parse and evaluate an expression using the AST — no exec/eval."""
        tree = ast.parse(expr.strip(), mode="eval")
        return self._eval_node(tree.body)

    def _eval_node(self, node: ast.AST) -> Any:
        # Numeric literal
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value

        # Unary operator (-x, +x)
        if isinstance(node, ast.UnaryOp):
            op_func = _SAFE_OPERATORS.get(type(node.op))
            if op_func is None:
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
            return op_func(self._eval_node(node.operand))

        # Binary operator (x + y, x * y, etc.)
        if isinstance(node, ast.BinOp):
            op_func = _SAFE_OPERATORS.get(type(node.op))
            if op_func is None:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            return op_func(left, right)

        # Function call (sqrt(x), log(x), etc.)
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only simple function calls allowed.")
            func_name = node.func.id
            if func_name not in _SAFE_FUNCTIONS:
                raise ValueError(f"Function not allowed: {func_name}")
            func = _SAFE_FUNCTIONS[func_name]
            args = [self._eval_node(a) for a in node.args]
            return func(*args)

        # Named constant (pi, e)
        if isinstance(node, ast.Name):
            if node.id in _SAFE_FUNCTIONS:
                val = _SAFE_FUNCTIONS[node.id]
                if isinstance(val, (int, float)):
                    return val
            raise ValueError(f"Unknown name: {node.id}")

        raise ValueError(f"Unsupported expression node: {type(node).__name__}")
