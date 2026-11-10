from __future__ import annotations

import math
from typing import Any


def calculate(expression: str) -> dict[str, Any]:
    """Safely evaluate basic mathematical expressions."""
    if not expression or not expression.strip():
        return {"error": "empty_expression", "message": "Expression cannot be empty"}

    allowed_names = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "pow": pow,
        "sqrt": math.sqrt,
        "log": math.log,
        "sin": math.sin,
        "cos": math.cos,
        "pi": math.pi,
        "e": math.e,
    }

    clean_expr = expression.strip()
    for forbidden in ["import", "exec", "eval", "open", "os", "sys", "__"]:
        if forbidden in clean_expr:
            return {"error": "forbidden_expression", "message": f"Forbidden keyword: {forbidden}"}

    try:
        result = eval(clean_expr, {"__builtins__": {}}, allowed_names)
        return {"expression": clean_expr, "result": result}
    except Exception as exc:
        return {"error": type(exc).__name__, "message": str(exc)}
