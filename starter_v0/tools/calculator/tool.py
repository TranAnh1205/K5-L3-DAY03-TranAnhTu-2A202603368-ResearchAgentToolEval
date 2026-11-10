from __future__ import annotations

import ast
import math
import operator
from typing import Any


_BINARY = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
           ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
           ast.Mod: operator.mod, ast.Pow: operator.pow}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_FUNCTIONS = {"abs": abs, "round": round, "min": min, "max": max,
              "sqrt": math.sqrt, "log": math.log}
_CONSTANTS = {"pi": math.pi, "e": math.e}


def _evaluate(node: ast.AST) -> float | int:
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        value = node.value
    elif isinstance(node, ast.Name) and node.id in _CONSTANTS:
        value = _CONSTANTS[node.id]
    elif isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
        value = _UNARY[type(node.op)](_evaluate(node.operand))
    elif isinstance(node, ast.BinOp) and type(node.op) in _BINARY:
        left, right = _evaluate(node.left), _evaluate(node.right)
        if isinstance(node.op, ast.Pow) and (abs(right) > 12 or abs(left) > 1e9):
            raise ValueError("power_out_of_range")
        value = _BINARY[type(node.op)](left, right)
    elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCTIONS and not node.keywords:
        if len(node.args) > 8:
            raise ValueError("too_many_arguments")
        value = _FUNCTIONS[node.func.id](*(_evaluate(arg) for arg in node.args))
    else:
        raise ValueError("unsupported_expression")
    if type(value) not in (int, float) or not math.isfinite(value) or abs(value) > 1e18:
        raise ValueError("result_out_of_range")
    return value


def calculate(expression: str) -> dict[str, Any]:
    """Evaluate limited arithmetic without executing Python code."""
    if not isinstance(expression, str) or not expression.strip():
        return {"error": "empty_expression", "message": "Expression cannot be empty"}
    expression = expression.strip()
    if len(expression) > 200:
        return {"error": "expression_too_long", "message": "Expression exceeds 200 characters"}
    try:
        return {"expression": expression, "result": _evaluate(ast.parse(expression, mode="eval").body)}
    except (SyntaxError, ValueError, TypeError, ZeroDivisionError, OverflowError) as exc:
        return {"error": type(exc).__name__, "message": str(exc)}
