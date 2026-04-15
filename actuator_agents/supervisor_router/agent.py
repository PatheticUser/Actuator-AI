"""
Supervisor Router Agent — Actuator AI

The central orchestrator. Combines: Triage + Routing + Escalation
Responsibilities:
  - Classify incoming requests
  - Route to appropriate specialist agent via handoffs
  - Handle escalations when specialists can't resolve
  - Manage multi-agent conversation flow
"""

import sys
import os
import asyncio
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from agents import Agent, Runner, ModelSettings, function_tool

from shared.models.ollama_provider import get_model
from shared.mcp_config import get_mcp_postgres
from shared.guardrails.safety import detect_jailbreak, detect_pii, detect_sql_injection

# --- Import specialist agents ---
from actuator_agents.technical_specialist.agent import agent as technical_specialist
from actuator_agents.account_security.agent import agent as account_security
from actuator_agents.billing_finance.agent import agent as billing_finance
from actuator_agents.success_retention.agent import agent as success_retention
from actuator_agents.operations_sync.agent import agent as operations_sync
from actuator_agents.linguistic.agent import agent as linguistic_agent
from actuator_agents.audit.agent import agent as audit_agent


MODEL = get_model()


# --- Supervisor Tools ---

@function_tool
def classify_request(message: str) -> str:
    """Classify incoming request into category and priority."""
    message_lower = message.lower()

    # Category detection
    category_signals = {
        "technical": ["error", "bug", "api", "500", "502", "timeout", "crash", "sdk", "debug", "deploy"],
        "account": ["login", "password", "2fa", "locked", "access", "account", "profile", "reset"],
        "billing": ["invoice", "charge", "refund", "payment", "plan", "upgrade", "downgrade", "billing"],
        "success": ["cancel", "renew", "churn", "health", "adoption", "retention", "satisfaction"],
        "operations": ["crm", "jira", "ticket", "sync", "assign", "track"],
        "linguistic": ["translate", "sentiment", "language", "tone", "quality score"],
        "audit": ["audit", "hallucination", "compliance", "qa", "review response"],
    }

    category = "general"
    max_score = 0
    for cat, signals in category_signals.items():
        score = sum(1 for s in signals if s in message_lower)
        if score > max_score:
            max_score = score
            category = cat

    # Priority detection
    urgent_signals = ["urgent", "asap", "critical", "down", "outage", "can't login", "locked out",
                      "charged twice", "data loss", "security breach"]
    is_urgent = any(s in message_lower for s in urgent_signals)
    priority = "P1-critical" if is_urgent else "P3-medium"

    return (
        f"Classification:\n"
        f"  Category: {category}\n"
        f"  Priority: {priority}\n"
        f"  Confidence: {min(max_score * 0.3 + 0.4, 1.0):.2f}\n"
        f"  Route to: {category.replace('_', ' ').title()} Agent"
    )


@function_tool
def escalate_to_human(
    reason: str, customer_email: str, conversation_summary: str
) -> str:
    """Escalate to human supervisor when agents cannot resolve."""
    esc_id = f"ESC-{abs(hash(reason)) % 100000:05d}"
    return (
        f"Escalation created:\n"
        f"  ID: {esc_id}\n"
        f"  Customer: {customer_email}\n"
        f"  Reason: {reason}\n"
        f"  Summary: {conversation_summary[:200]}\n"
        f"  Assigned to: On-duty supervisor\n"
        f"  SLA: 30 minutes\n"
        f"  Status: Awaiting human response"
    )


# --- Dynamic Instructions ---
def build_instructions(ctx, agent):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    customer_email = ctx.context.get("customer_email", "Unknown")
    return f"""You are the Supervisor Router for Actuator AI. Current time: {now}
CURRENT USER: {customer_email}

YOU ARE THE FRONT DOOR. Every customer message comes to you first.
GREET USER BY NAME/EMAIL IF KNOWN. DO NOT be overly technical. 

DATABASE SCHEMA (PostgreSQL):
- 'customers' (id, company_name, industry, status, health_score, mrr)
- 'customer_contacts' (id, customer_id, name, email, phone, role, account_locked, login_failures, two_factor_enabled)
- 'support_tickets' (id, customer_id, contact_email, category, priority, subject, status)
- 'api_usage' (id, customer_id, month, api_calls, storage_used_gb)

PROTOCOL:
1. Classify the request using classify_request tool
2. Based on classification, hand off to the appropriate specialist
3. If unclear, ask ONE clarifying question before routing

RULES:
- NEVER try to solve issues yourself — always route to specialists
- Keep responses clean, minimal, and polite."""


# --- Supervisor Agent ---
supervisor = Agent(
    name="Supervisor Router",
    instructions=build_instructions,
    model=MODEL,
    model_settings=ModelSettings(temperature=0.2, max_tokens=800),
    tools=[classify_request, escalate_to_human],
    handoffs=[
        technical_specialist,
        account_security,
        billing_finance,
        success_retention,
        operations_sync,
        linguistic_agent,
        audit_agent,
    ],
    mcp_servers=[get_mcp_postgres()],
    input_guardrails=[detect_jailbreak, detect_pii, detect_sql_injection],
)


async def main():
    scenarios = [
        "Our API is returning 502 errors. Users can't access the platform!",
        # "I can't log in. My account seems locked. Email: locked@example.com",
        # "I was charged twice this month! I want a refund immediately.",
        # "We're thinking about cancelling. The product isn't being used much.",
        # "Create a Jira ticket for the payment gateway timeout issue.",
        # "Analyze this message sentiment: 'This is the worst service ever!'",
        # "I want to speak to a manager. This is unacceptable.",
    ]

    for msg in scenarios:
        print(f"\n{'='*70}")
        print(f"Customer: {msg}")
        print(f"{'='*70}")

        result = await Runner.run(supervisor, msg)

        # Handle HITL approvals (e.g., refunds)
        if result.interruptions:
            print(f"\n⚠ APPROVAL NEEDED")
            state = result.to_state()
            for i in result.interruptions:
                answer = input(f"  Approve '{i.raw_item.name}'? (y/n): ").strip().lower()
                if answer == "y":
                    state.approve(i)
            result = await Runner.run(supervisor, state)

        print(f"\n→ Handled by: {result.last_agent.name}")
        print(f"\nResponse:\n{result.final_output}")
        print("-" * 70)


if __name__ == "__main__":
    asyncio.run(main())
