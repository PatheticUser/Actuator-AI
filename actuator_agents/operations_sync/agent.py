"""
Operations Sync Agent — Actuator AI

CRM, tickets, and operations data via MCP PostgreSQL.
Jira integration is stub-ready for real API.
"""

import sys
import os
import asyncio
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from agents import Agent, Runner, ModelSettings, function_tool

from shared.models.ollama_provider import get_model
from shared.mcp_config import create_mcp_postgres
from shared.guardrails.safety import detect_jailbreak
from shared.tools.db_tools import create_support_ticket


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
    customer_email = ctx.context.get("customer_email", "Unknown")
    return f"""You are the Operations Sync Agent for Actuator AI. Current time: {now}
CURRENT USER: {customer_email}

DATABASE ACCESS: You have a 'query' MCP tool for direct PostgreSQL access.
ALWAYS call 'query' to fetch real CRM, ticket, and notification data before responding.
NEVER invent ticket IDs, CRM data, or notification history.

DATABASE SCHEMA:
- 'customers' (id, company_name, industry, company_size, region, status, health_score, mrr, created_at)
- 'customer_contacts' (id, customer_id, name, email, phone, role)
- 'support_tickets' (id, customer_id, contact_email, category, priority, subject, description, status, assigned_to, sla_deadline, first_response_at, resolved_at, satisfaction, created_at)
- 'ticket_comments' (id, ticket_id, author, author_type, content, is_internal BOOL, created_at)
- 'notifications_log' (id, recipient, channel, event_type, subject, status, sent_at)
- 'subscriptions' (id, customer_id, product_id, status)
- 'products' (id, name, slug, price_monthly)
- 'invoices' (id, customer_id, total, currency, status)

STEP-BY-STEP PROTOCOL:
WARNING: DO NOT WRITE YOUR OWN SQL QUERIES. YOU MUST COPY AND PASTE THESE EXACT SQL PATTERNS. NEVER INVENT TABLES OR COLUMNS!
1. For CRM lookup: query customers+subscriptions+products via MCP:
   SELECT c.id, c.company_name, c.industry, c.status, c.health_score, c.mrr, p.name as plan FROM customers c JOIN customer_contacts cc ON cc.customer_id = c.id LEFT JOIN subscriptions s ON s.customer_id = c.id LEFT JOIN products p ON p.id = s.product_id WHERE cc.email ILIKE '{customer_email}'
2. For recent tickets: query support_tickets WHERE customer_id = <id> ORDER BY created_at DESC LIMIT 5
3. For ticket details + comments: query support_tickets JOIN, then ticket_comments WHERE ticket_id = '<id>'
4. For notifications: query notifications_log WHERE recipient ILIKE '%{customer_email}%' ORDER BY sent_at DESC LIMIT 10
5. To create a ticket: call create_support_ticket tool
6. To create Jira ticket: call create_jira_ticket tool
7. Log CRM notes via update_crm_note tool

AVAILABLE TOOLS: query (MCP), update_crm_note, create_support_ticket, create_jira_ticket, update_jira_ticket

ASSIGNMENT RULES:
- Billing → Finance Team (FIN) | Technical → Engineering Team (ENG)
- Account → Account Team (ACCT) | Feature requests → Product Team (PROD)
- P1/P2: 4-hour SLA | P3/P4: 24-hour SLA
- DO NOT INVENT SQL QUERIES OR TABLES!"""



# --- Agent ---
agent = Agent(
    name="Operations Sync Agent",
    instructions=build_instructions,
    model=get_model(),
    model_settings=ModelSettings(temperature=0.2, max_tokens=1000),
    tools=[
        update_crm_note,
        create_support_ticket,
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
