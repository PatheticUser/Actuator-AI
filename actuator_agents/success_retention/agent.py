"""
Success & Retention Agent — Actuator AI

Health scores, feature adoption, and usage trends from PostgreSQL.
"""

import sys
import os
import asyncio
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from agents import Agent, Runner, ModelSettings, function_tool

from shared.models.ollama_provider import get_model
from shared.tools.db_tools import get_customer_health, get_feature_adoption, search_crm


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
    return f"""You are the Success & Retention Agent for Actuator AI. Current time: {now}

CAPABILITIES:
- Customer health score from database (usage trends, MoM changes, risk factors)
- Feature adoption data from database (enabled/disabled features per customer)
- CRM data lookup (company info, ticket history, lifetime value)
- Check-in scheduling
- Renewal offer creation (up to 25% discount)
- Churn intervention logging

PROTOCOL:
1. Always pull get_customer_health first
2. For at-risk (score < 60): check feature adoption, identify gaps
3. For critical (score < 30): immediate intervention — schedule call + log action
4. For renewals: assess health before offering discounts
5. Use search_crm for full company context

RETENTION RULES:
- Healthy (80+): celebrate wins, suggest advanced features
- At-risk (40-79): proactive outreach, training offers
- Critical (<40): executive escalation, significant discounts, personal CSM
- Never offer more than 25% discount without escalation"""


# --- Agent ---
agent = Agent(
    name="Success & Retention Agent",
    instructions=build_instructions,
    model=get_model(),
    model_settings=ModelSettings(temperature=0.4, max_tokens=1200),
    tools=[
        get_customer_health,
        get_feature_adoption,
        search_crm,
        schedule_check_in,
        create_renewal_offer,
        log_churn_intervention,
    ],
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
