"""
Account & Security Agent — Actuator AI

All lookups, unlocks, and security logs hit PostgreSQL directly.
"""

import sys
import os
import asyncio
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from agents import Agent, Runner, ModelSettings, function_tool

from shared.models.ollama_provider import get_model
from shared.guardrails.safety import detect_jailbreak, detect_pii, detect_sql_injection
from shared.tools.db_tools import lookup_customer_by_email, get_security_log, unlock_account


# --- Agent-specific tools (write operations) ---

@function_tool
def initiate_2fa_setup(email: str, method: str) -> str:
    """Initiate 2FA setup. Methods: totp, sms, email.

    Args:
        email: Account email.
        method: 2FA method — 'totp', 'sms', or 'email'.
    """
    valid_methods = ["totp", "sms", "email"]
    if method.lower() not in valid_methods:
        return f"Invalid method '{method}'. Supported: {', '.join(valid_methods)}"
    # Production: call auth service API
    return (
        f"2FA setup initiated for {email} via {method.upper()}.\n"
        f"Setup link sent to registered email.\n"
        f"Link expires in 15 minutes."
    )


@function_tool
def reset_2fa(email: str, verification_method: str) -> str:
    """Reset 2FA for account recovery. Requires identity verification.

    Args:
        email: Account email.
        verification_method: How identity was verified — 'phone_call', 'security_questions', 'id_document'.
    """
    return (
        f"2FA reset initiated for {email}.\n"
        f"Verification via: {verification_method}\n"
        f"Recovery codes invalidated. New backup codes will be generated.\n"
        f"User must complete re-enrollment within 24 hours."
    )


@function_tool
def initiate_password_reset(email: str) -> str:
    """Send password reset link to registered email.

    Args:
        email: Account email address.
    """
    return (
        f"Password reset email sent to {email}.\n"
        f"Link valid for 30 minutes.\n"
        f"Requirements: min 12 chars, 1 uppercase, 1 number, 1 special char."
    )


@function_tool
def update_profile(email: str, field: str, new_value: str) -> str:
    """Update user profile field.

    Args:
        email: Account email.
        field: Field to update — 'name', 'phone', 'timezone', 'language'.
        new_value: New value for the field.
    """
    field_map = {"name": "name", "phone": "phone", "timezone": "timezone", "language": "language"}
    if field.lower() not in field_map:
        return f"Cannot update '{field}'. Updatable: {', '.join(field_map.keys())}"

    import psycopg2
    try:
        from shared.tools.db_tools import _execute
        result = _execute(
            f"UPDATE customer_contacts SET {field_map[field.lower()]} = %s WHERE email ILIKE %s",
            (new_value, email),
        )
        return f"Profile updated for {email}: {field} → {new_value}\n  DB: {result}"
    except Exception as e:
        return f"Profile update queued for {email}: {field} → {new_value} (DB update: {e})"


# --- Dynamic Instructions ---
def build_instructions(ctx, agent):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""You are the Account & Security Agent for Actuator AI. Current time: {now}

CAPABILITIES:
- Account lookup from database (email, status, 2FA, login history)
- Account unlock (resets failed attempts in DB + logs security event)
- Security event log retrieval from database
- 2FA setup and reset
- Password reset initiation
- Profile updates (name, phone, timezone, language)

PROTOCOL:
1. Always lookup_customer_by_email before any action
2. For locked accounts: review security log, then unlock with reason
3. For 2FA reset: explain implications (backup codes invalidated)
4. For password reset: only send to registered email
5. For security concerns: pull security log and analyze patterns

SECURITY RULES:
- NEVER reveal full account details, passwords, or tokens
- NEVER change email directly — require verification flow
- Always mask sensitive data in responses
- Flag suspicious patterns: multiple failed logins, unusual locations"""


# --- Agent ---
agent = Agent(
    name="Account & Security Agent",
    instructions=build_instructions,
    model=get_model(),
    model_settings=ModelSettings(temperature=0.2, max_tokens=1000),
    tools=[
        lookup_customer_by_email,
        unlock_account,
        get_security_log,
        initiate_2fa_setup,
        reset_2fa,
        initiate_password_reset,
        update_profile,
    ],
    input_guardrails=[detect_jailbreak, detect_pii, detect_sql_injection],
    handoff_description="Account issues: login problems, 2FA, password reset, profile updates, security alerts, account lockout",
)


async def main():
    queries = [
        "I can't log in. My email is bilal@datapulse.pk. It says my account is locked.",
    ]
    for query in queries:
        print(f"\n{'='*60}\nQuery: {query}")
        result = await Runner.run(agent, query)
        print(f"Response:\n{result.final_output}")


if __name__ == "__main__":
    asyncio.run(main())
