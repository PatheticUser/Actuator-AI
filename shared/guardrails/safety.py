"""shared/guardrails/safety.py — Reusable Guardrail Functions"""

import re
from agents import GuardrailFunctionOutput, input_guardrail, output_guardrail


@input_guardrail(name="Jailbreak Detector")
async def detect_jailbreak(ctx, agent, input):
    """Block common jailbreak / prompt injection patterns."""
    text = str(input).lower()
    patterns = [
        "ignore your instructions", "ignore previous instructions",
        "you are now", "pretend you are", "act as if",
        "DAN mode", "jailbreak", "forget your instructions",
        "override your", "system prompt", "<|im_start|>",
    ]
    for p in patterns:
        if p.lower() in text:
            return GuardrailFunctionOutput(
                tripwire_triggered=True, output_info=f"Jailbreak: '{p}'"
            )
    return GuardrailFunctionOutput(tripwire_triggered=False, output_info="Clean")


@input_guardrail(name="PII Detector")
async def detect_pii(ctx, agent, input):
    """Block messages with credit card numbers or SSNs."""
    text = str(input)
    if re.search(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', text):
        return GuardrailFunctionOutput(
            tripwire_triggered=True, output_info="Credit card detected"
        )
    if re.search(r'\b\d{3}-\d{2}-\d{4}\b', text):
        return GuardrailFunctionOutput(
            tripwire_triggered=True, output_info="SSN detected"
        )
    return GuardrailFunctionOutput(tripwire_triggered=False, output_info="No PII")


@input_guardrail(name="SQL Injection Detector")
async def detect_sql_injection(ctx, agent, input):
    """Block SQL injection attempts."""
    text = str(input).upper()
    patterns = ["DROP TABLE", "DELETE FROM", "'; --", "OR 1=1", "UNION SELECT"]
    for p in patterns:
        if p in text:
            return GuardrailFunctionOutput(
                tripwire_triggered=True, output_info=f"SQL injection: {p}"
            )
    return GuardrailFunctionOutput(tripwire_triggered=False, output_info="Safe")


@output_guardrail(name="Response Length Check")
async def check_response_length(ctx, agent, output):
    """Block excessively long responses (cost/quality control)."""
    if len(str(output)) > 3000:
        return GuardrailFunctionOutput(
            tripwire_triggered=True,
            output_info=f"Response too long: {len(str(output))} chars"
        )
    return GuardrailFunctionOutput(tripwire_triggered=False, output_info="OK")
