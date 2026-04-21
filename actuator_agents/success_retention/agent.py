"""
Success Retention Agent — Actuator AI

Health scores, feature adoption, and usage trends via MCP PostgreSQL.
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


# --- Agent-specific tools ---

@function_tool
def schedule_check_in(email: str, date: str, agenda: str) -> str:
    """Schedule a proactive check-in call with customer.

    Args:
        email: Customer contact email.
        date: Proposed date, e.g. '2026-04-20'.
        agenda: Meeting agenda.
    """
    return (
        f"Check-in scheduled:\n"
        f"  Customer: {email}\n"
        f"  Date: {date}\n"
        f"  Agenda: {agenda}\n"
        f"  Calendar invite sent. CSM notified."
    )


@function_tool
def create_renewal_offer(email: str, discount_percent: int, term_months: int) -> str:
    """Create a renewal offer with optional discount.

    Args:
        email: Customer contact email.
        discount_percent: Discount percentage (max 25).
        term_months: Renewal term length in months.
    """
    if discount_percent > 25:
        return "Maximum discount is 25%. Escalate to VP Sales for higher discounts."
    return (
        f"Renewal offer created:\n"
        f"  Customer: {email}\n"
        f"  Discount: {discount_percent}% off current rate\n"
        f"  Term: {term_months} months\n"
        f"  Offer valid for 14 days\n"
        f"  Email with offer details sent to customer."
    )


@function_tool
def log_churn_intervention(email: str, risk_level: str, action_taken: str) -> str:
    """Log a churn prevention intervention for tracking.

    Args:
        email: Customer contact email.
        risk_level: 'critical', 'high', 'medium', 'low'.
        action_taken: Description of intervention action.
    """
    return (
        f"Churn intervention logged:\n"
        f"  Customer: {email}\n"
        f"  Risk level: {risk_level}\n"
        f"  Action: {action_taken}\n"
        f"  Logged at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"  Follow-up alert set for 7 days."
    )


# --- Dynamic Instructions ---
def build_instructions(ctx, agent):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    customer_email = ctx.context.get("customer_email", "Unknown")
    return f"""You are the Success Retention Agent for Actuator AI. Current time: {now}
CURRENT USER: {customer_email}

DATABASE ACCESS: You have a 'query' MCP tool for direct PostgreSQL access.
ALWAYS call 'query' to get real customer health and usage data before responding.
NEVER guess health scores, feature flags, or NPS values.

DATABASE SCHEMA:
- 'customers' (id, company_name, industry, company_size, region, status, health_score, mrr, created_at)
- 'customer_contacts' (id, customer_id, name, email, phone, role)
- 'subscriptions' (id, customer_id, product_id, status, billing_cycle, current_period_end, auto_renew)
- 'products' (id, name, slug, price_monthly, api_calls_limit, storage_gb, support_tier)
- 'api_usage' (id, customer_id, month VARCHAR, api_calls INT, storage_used_gb NUMERIC, agent_sessions INT, webhook_events INT, overage_amount NUMERIC)
- 'feature_flags' (id, customer_id, feature_name, enabled BOOL, enabled_at TIMESTAMP)
- 'feedback' (id, customer_id, rating INT, nps_score INT, comment TEXT, created_at)
- 'support_tickets' (id, customer_id, contact_email, category, priority, subject, status, created_at)
- 'invoices' (id, customer_id, total, currency, status)

STEP-BY-STEP PROTOCOL:
WARNING: DO NOT WRITE YOUR OWN SQL QUERIES. YOU MUST COPY AND PASTE THESE EXACT SQL PATTERNS. NEVER INVENT TABLES OR COLUMNS!
1. Query health score first:
   SELECT c.company_name, c.health_score, c.mrr, c.status, p.name as plan, s.current_period_end, s.auto_renew FROM customers c JOIN customer_contacts cc ON cc.customer_id = c.id JOIN subscriptions s ON s.customer_id = c.id JOIN products p ON p.id = s.product_id WHERE cc.email ILIKE '{customer_email}'
2. Query usage trend:
   SELECT month, api_calls, agent_sessions FROM api_usage WHERE customer_id = (SELECT customer_id FROM customer_contacts WHERE email ILIKE '{customer_email}') ORDER BY month DESC LIMIT 3
3. Query feature adoption:
   SELECT feature_name, enabled, enabled_at FROM feature_flags WHERE customer_id = (SELECT customer_id FROM customer_contacts WHERE email ILIKE '{customer_email}') ORDER BY feature_name
4. Query NPS/feedback:
   SELECT rating, nps_score, comment FROM feedback WHERE customer_id = (SELECT customer_id FROM customer_contacts WHERE email ILIKE '{customer_email}') ORDER BY created_at DESC LIMIT 1
5. Based on findings call: schedule_check_in, create_renewal_offer, or log_churn_intervention

AVAILABLE TOOLS: query (MCP), schedule_check_in, create_renewal_offer, log_churn_intervention

RETENTION RULES:
- Healthy (80+): celebrate wins, suggest advanced features
- At-risk (40-79): proactive outreach, training offers
- Critical (<40): executive escalation, significant discounts, personal CSM
- Never offer more than 25% discount without escalation
- DO NOT INVENT SQL QUERIES OR TABLES!"""


# --- Agent ---
agent = Agent(
    name="Success Retention Agent",
    instructions=build_instructions,
    model=get_model(),
    model_settings=ModelSettings(temperature=0.4, max_tokens=1200),
    tools=[
        schedule_check_in,
        create_renewal_offer,
        log_churn_intervention,
    ],
    input_guardrails=[detect_jailbreak],
    handoff_description="Customer success: health checks, renewals, churn prevention, feature adoption, proactive outreach",
)


async def main():
    queries = [
        "Check health and feature adoption for sara@novabyte.io",
    ]
    for query in queries:
        print(f"\n{'='*60}\nQuery: {query}")
        result = await Runner.run(agent, query)
        print(f"Response:\n{result.final_output}")


if __name__ == "__main__":
    asyncio.run(main())
