"""shared/tools/math_tools.py — Calculator & Math Tools"""

from agents import function_tool


@function_tool
def calculate(expression: str) -> str:
    """Evaluate a math expression safely. Example: '2 + 2', '15 * 3.5'."""
    try:
        allowed = set("0123456789+-*/.() ")
        if all(c in allowed for c in expression):
            return f"{expression} = {eval(expression)}"
        return "Invalid expression — only numbers and +-*/() allowed"
    except Exception as e:
        return f"Error: {e}"
