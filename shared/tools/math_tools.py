"""shared/tools/math_tools.py — Calculator, Currency & Unit Conversion"""

import os
import httpx
from agents import function_tool


@function_tool
def calculate(expression: str) -> str:
    """Safely evaluate a math expression.

    Args:
        expression: Math expression, e.g. '(29900 * 12) * 0.85'
    """
    allowed = set("0123456789+-*/.() %")
    if not all(c in allowed for c in expression):
        return "[ERROR] Invalid characters. Only numbers and +-*/.()" " allowed."
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"{expression} = {result:,.4f}".rstrip("0").rstrip(".")
    except Exception as e:
        return f"[ERROR] Calculation failed: {e}"


@function_tool
def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert between currencies using live rates.

    Args:
        amount: Amount to convert.
        from_currency: Source currency code, e.g. 'USD'.
        to_currency: Target currency code, e.g. 'PKR'.
    """
    # Uses free exchangerate.host API — no key needed
    try:
        response = httpx.get(
            f"https://api.exchangerate.host/convert",
            params={"from": from_currency.upper(), "to": to_currency.upper(), "amount": amount},
            timeout=10.0,
        )
        data = response.json()
        if data.get("success") and data.get("result"):
            rate = data["info"]["rate"]
            result = data["result"]
            return (
                f"Currency conversion:\n"
                f"  {amount:,.2f} {from_currency.upper()} = {result:,.2f} {to_currency.upper()}\n"
                f"  Rate: 1 {from_currency.upper()} = {rate:,.4f} {to_currency.upper()}"
            )
        # Fallback static rates if API fails
        return _fallback_currency(amount, from_currency, to_currency)
    except Exception:
        return _fallback_currency(amount, from_currency, to_currency)


def _fallback_currency(amount: float, from_c: str, to_c: str) -> str:
    """Fallback static rates for common pairs."""
    rates = {
        ("USD", "PKR"): 278.50,
        ("PKR", "USD"): 0.0036,
        ("USD", "EUR"): 0.92,
        ("EUR", "USD"): 1.09,
        ("GBP", "USD"): 1.27,
        ("USD", "GBP"): 0.79,
    }
    key = (from_c.upper(), to_c.upper())
    if key in rates:
        result = amount * rates[key]
        return (
            f"Currency conversion (cached rates):\n"
            f"  {amount:,.2f} {from_c.upper()} ≈ {result:,.2f} {to_c.upper()}\n"
            f"  ⚠ Using cached rate. Live API unavailable."
        )
    return f"[ERROR] No rate available for {from_c.upper()} → {to_c.upper()}."


@function_tool
def percentage(value: float, total: float) -> str:
    """Calculate percentage and related metrics.

    Args:
        value: Part value.
        total: Total value.
    """
    if total == 0:
        return "[ERROR] Total cannot be zero."
    pct = (value / total) * 100
    remaining = total - value
    return (
        f"Percentage calculation:\n"
        f"  {value:,.2f} / {total:,.2f} = {pct:.2f}%\n"
        f"  Remaining: {remaining:,.2f} ({100 - pct:.2f}%)"
    )
