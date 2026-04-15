"""
Operations Sync Agent — Actuator AI

CRM, tickets, and operations data from PostgreSQL.
Jira integration is stub-ready for real API.
"""

import sys
import os
import asyncio
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from agents import Agent, Runner, ModelSettings, function_tool

from shared.models.ollama_provider import get_model
from shared.guardrails.safety import detect_jailbreak
from shared.tools.db_tools import (
    search_crm, query_tickets, get_ticket_details,
    create_support_ticket, get_notifications,
)


# --- Agent-specific tools ---

@function_tool
def update_crm_note(customer_email: str, note: str, interaction_type: str) -> str:
    """Add interaction note to CRM record.

    Args:
        customer_email: Customer contact email.
        note: Note content.
        interaction_type: 'call', 'email', 'chat', 'meeting', 'internal'.
    """
    valid_types = ["call", "email", "chat", "meeting", "internal"]
    if interaction_type.lower() not in valid_types:
        return f"Invalid type '{interaction_type}'. Use: {', '.join(valid_types)}"
    # Production: write to CRM API (HubSpot, Salesforce, etc.)
    return (
        f"CRM note added:\n"
        f"  Customer: {customer_email}\n"
        f"  Type: {interaction_type}\n"
        f"  Note: {note[:120]}\n"
        f"  Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
    )


@function_tool
def create_jira_ticket(project: str, title: str, description: str, priority: str, assignee: str) -> str:
    """Create a Jira ticket for task tracking.

    Args:
        project: Jira project key — 'ENG', 'FIN', 'ACCT', 'PROD'.
        title: Ticket title.
        description: Full description.
        priority: 'P1', 'P2', 'P3', 'P4'.
        assignee: Person to assign to.
    """
    # Production: call Jira REST API
    ticket_key = f"{project.upper()}-{abs(hash(title)) % 10000:04d}"
    return (
        f"Jira ticket created:\n"
        f"  Key: {ticket_key}\n"
        f"  Project: {project}\n"
        f"  Title: {title}\n"
        f"  Priority: {priority}\n"
        f"  Assignee: {assignee}\n"
        f"  Status: Open"
    )


@function_tool
def update_jira_ticket(ticket_key: str, status: str, comment: str) -> str:
    """Update Jira ticket status and add comment.

    Args:
        ticket_key: Jira ticket key, e.g. 'ENG-0042'.
        status: New status — 'open', 'in_progress', 'review', 'resolved', 'closed'.
        comment: Comment to add.
    """
    valid_statuses = ["open", "in_progress", "review", "resolved", "closed"]
    if status.lower() not in valid_statuses:
        return f"Invalid status. Use: {', '.join(valid_statuses)}"
    return (
        f"Jira ticket updated:\n"
        f"  Ticket: {ticket_key}\n"
        f"  Status: {status}\n"
        f"  Comment: {comment[:120]}"
    )


# --- Dynamic Instructions ---
def build_instructions(ctx, agent):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""You are the Operations Sync Agent for Actuator AI. Current time: {now}

CAPABILITIES:
- CRM search from database (company info, tickets, lifetime value)
- Support ticket queries and creation (writes to PostgreSQL)
- Full ticket details with comment history
- Notification history lookup
- Jira ticket creation and updates (stub for API integration)
- CRM note logging

PROTOCOL:
1. For customer interactions: search CRM first, then log notes
2. For engineering issues: create Jira ticket + support ticket
3. For status checks: use get_ticket_details for full history
4. Ensure data consistency — always create DB records

ASSIGNMENT RULES:
- Billing → Finance Team (FIN)
- Technical → Engineering Team (ENG)
- Account → Account Team (ACCT)
- Feature requests → Product Team (PROD)
- P1/P2: 4-hour SLA | P3/P4: 24-hour SLA"""


# --- Agent ---
agent = Agent(
    name="Operations Sync Agent",
    instructions=build_instructions,
    model=get_model(),
    model_settings=ModelSettings(temperature=0.2, max_tokens=1000),
    tools=[
        search_crm,
        update_crm_note,
        query_tickets,
        get_ticket_details,
        create_support_ticket,
        get_notifications,
        create_jira_ticket,
        update_jira_ticket,
    ],
    input_guardrails=[detect_jailbreak],
    handoff_description="Operations: CRM updates, Jira tickets, support tickets, cross-system sync, task tracking",
)


async def main():
    queries = [
        "Show me the CRM record and recent tickets for ahmed@techvista.pk",
    ]
    for query in queries:
        print(f"\n{'='*60}\nQuery: {query}")
        result = await Runner.run(agent, query)
        print(f"Response:\n{result.final_output}")


if __name__ == "__main__":
    asyncio.run(main())
