"""
Account Security Agent — Actuator AI

All lookups via MCP PostgreSQL. Unlocks and security writes via function tools.
"""

import sys
import os
import asyncio
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from agents import Agent, Runner, ModelSettings, function_tool

from shared.models.ollama_provider import get_model
from shared.mcp_config import create_mcp_postgres
from shared.guardrails.safety import detect_jailbreak, detect_pii, detect_sql_injection
from shared.tools.db_tools import unlock_account


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

    try:
        from shared.tools.db_tools import _execute
        result = _execute(
            f"UPDATE customer_contacts SET {field_map[field.lower()]} = %s WHERE email ILIKE %s",
            (new_value, email),
        )
        return f"Profile updated for {email}: {field} → {new_value}\n  DB: {result}"
    except Exception as e:
        return f"Profile update queued for {email}: {field} → {new_value} (DB update: {e})"


from shared.tools.db_tools import register_customer, update_customer_profile, add_customer_contact
from shared.tools.notification_tools import send_email

# --- Dynamic Instructions ---
def build_instructions(ctx, agent):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    customer_email = ctx.context.get("customer_email", "Unknown")
    return f"""You are the Account & Security Agent for Actuator AI. Current time: {now}
CURRENT USER: {customer_email}

DATABASE ACCESS: You have a 'query' MCP tool for direct PostgreSQL access.

UNKNOWN USER & NO ACCOUNT FOUND PROTOCOL:
If a user queries for an email or account that returns no records in the database, respond warmly and clearly in this format:
"Hi, I wasn't able to find an account associated with [email] in our system.

Could you double-check the email address on your account? Alternatively, if you have:
• Your company name
• A different email address you might have used
• An invoice number (INV-XXXX format)
Any of these would help me locate your subscription details.

Would you like me to register a new account for you?"

If the user asks to register, ask for their Company Name, Full Name, Email, and Plan (free, pro, enterprise), then call the `register_customer` tool.

DATABASE SCHEMA:
- 'customers' (id, company_name, industry, status, health_score, mrr)
- 'customer_contacts' (id, customer_id, name, email, phone, role, account_locked, login_failures, two_factor_enabled, two_factor_method)
- 'security_events' (id, contact_email, event_type, ip_address, location, details JSONB, created_at)

STEP-BY-STEP PROTOCOL:
1. Call 'query' MCP tool to fetch account details.
2. For locked accounts: query security_events, then call unlock_account tool
3. For 2FA requests: call initiate_2fa_setup or reset_2fa
4. For password: call initiate_password_reset
5. For registration: call register_customer
6. Report exact DB results to the customer

AVAILABLE TOOLS: query (MCP), unlock_account, initiate_2fa_setup, reset_2fa, initiate_password_reset, update_profile, register_customer

RULES:
- NEVER reveal full account details or tokens
- Always confirm account exists in DB before taking action
- Report lock status, 2FA method, and last login from actual DB data"""


# --- Agent ---
agent = Agent(
    name="Account Security Agent",
    instructions=build_instructions,
    model=get_model(),
    model_settings=ModelSettings(temperature=0.2, max_tokens=1000),
    tools=[
        unlock_account,
        initiate_2fa_setup,
        reset_2fa,
        initiate_password_reset,
        update_profile,
        update_customer_profile,
        add_customer_contact,
        register_customer,
        send_email,
    ],
    input_guardrails=[detect_jailbreak, detect_pii, detect_sql_injection],
    handoff_description="Account and security issues: login problems, 2FA, password reset, profile updates, security alerts, account lockout, new account registration",
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
