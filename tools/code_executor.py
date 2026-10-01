"""Safe sandboxed Python code execution tool.

Allows the agent to perform data manipulation, compute statistical summaries,
and generate formatted tables with security protections against arbitrary system calls.
"""

from __future__ import annotations

import ast
import io
import math
import statistics
import sys
from typing import Any, Dict, Optional

from tools.base import BaseTool, ToolResult, ToolStatus


class CodeExecutorTool(BaseTool):
    """Executes safe Python code snippets in a restricted sandbox."""

    # Explicitly forbidden AST identifiers and calls
    FORBIDDEN_CALLS = {
        "os", "sys", "subprocess", "socket", "urllib", "requests", "shutil",
        "open", "eval", "exec", "compile", "__import__", "globals", "locals",
        "breakpoint", "input", "exit", "quit"
    }

    @property
    def name(self) -> str:
        return "code_executor"

    @property
    def description(self) -> str:
        return (
            "Safely execute a Python code snippet for data analysis, math, or tabular formatting. "
            "Input: 'code' (str). "
            "Output: stdout captured output and evaluated 'result' variable."
        )

    def execute(self, **kwargs) -> ToolResult:
        code: str = kwargs.get("code", "")
        if not code:
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.FAILURE,
                error_msg="Missing required parameter: 'code'",
            )

        # Step 1: Security AST Validation
        security_error = self._validate_security(code)
        if security_error:
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.FAILURE,
                error_msg=f"Security Violation: {security_error}",
                metadata={"code": code, "security_blocked": True},
            )

        # Step 2: Sandboxed Execution
        return self._execute_sandboxed(code)

    def _validate_security(self, code: str) -> Optional[str]:
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return f"Syntax Error: {e}"

        for node in ast.walk(tree):
            # Block import statements
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                return "Imports are restricted. Use pre-loaded modules (math, statistics, json, re)."

            # Block forbidden function/attribute calls
            if isinstance(node, ast.Name) and node.id in self.FORBIDDEN_CALLS:
                return f"Access to '{node.id}' is blocked by security guardrails."

            if isinstance(node, ast.Attribute) and node.attr in self.FORBIDDEN_CALLS:
                return f"Access to '{node.attr}' is blocked by security guardrails."

            # Block dunder attribute access
            if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
                return f"Access to internal dunder attributes is blocked."

        return None

    def _execute_sandboxed(self, code: str) -> ToolResult:
        # Restricted safe global environment
        safe_globals = {
            "__builtins__": {
                "abs": abs, "all": all, "any": any, "bin": bin, "bool": bool,
                "dict": dict, "divmod": divmod, "enumerate": enumerate, "filter": filter,
                "float": float, "format": format, "hex": hex, "int": int, "isinstance": isinstance,
                "len": len, "list": list, "map": map, "max": max, "min": min, "oct": oct,
                "ord": ord, "pow": pow, "print": print, "range": range, "reversed": reversed,
                "round": round, "set": set, "sorted": sorted, "str": str, "sum": sum,
                "tuple": tuple, "zip": zip,
            },
            "math": math,
            "statistics": statistics,
        }
        local_scope: Dict[str, Any] = {}

        old_stdout = sys.stdout
        redirected_output = io.StringIO()

        try:
            sys.stdout = redirected_output
            exec(code, safe_globals, local_scope)
            stdout_text = redirected_output.getvalue().strip()

            raw_res = local_scope.get("result", stdout_text or "Execution completed successfully.")
            if isinstance(raw_res, (int, float, bool, list, dict)):
                result_value = raw_res
            else:
                result_value = str(raw_res)

            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.SUCCESS,
                data={
                    "output": stdout_text,
                    "result": result_value,
                    "variables": {k: str(v) for k, v in local_scope.items() if not k.startswith("_")}
                },
                metadata={"code_length": len(code)},
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.FAILURE,
                error_msg=f"Execution Error: {type(e).__name__}: {str(e)}",
                metadata={"code": code},
            )
        finally:
            sys.stdout = old_stdout
