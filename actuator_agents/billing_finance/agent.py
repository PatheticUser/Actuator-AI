"""
Billing Finance Agent — Actuator AI

All billing lookups via MCP PostgreSQL.
Refunds still need HITL approval.
"""

import sys
import os
import asyncio
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from agents import Agent, Runner, ModelSettings, function_tool

from shared.models.ollama_provider import get_model
from shared.mcp_config import create_mcp_postgres
from shared.guardrails.safety import detect_jailbreak, detect_pii


# --- Agent-specific tools ---

@function_tool
def change_plan(email: str, new_plan: str) -> str:
    """Upgrade or downgrade subscription plan.

    Args:
        email: Customer contact email.
        new_plan: Target plan slug — 'free', 'pro', 'enterprise', 'enterprise_plus'.
    """
    from shared.tools.db_tools import _query
    products = _query("SELECT slug, name, price_monthly FROM products WHERE is_active = true")
    plan_map = {p["slug"]: p for p in products} if products and "error" not in products[0] else {}

    if new_plan.lower() not in plan_map:
        return f"Invalid plan '{new_plan}'. Available: {', '.join(plan_map.keys())}"

    p = plan_map[new_plan.lower()]
    return (
        f"Plan change initiated for {email}:\n"
        f"  New plan: {p['name']}\n"
        f"  Price: PKR {p['price_monthly']:,.0f}/mo\n"
        f"  Effective: Next billing cycle\n"
        f"  Prorated credit will be applied if downgrading."
    )


@function_tool(needs_approval=True)
def process_refund(email: str, invoice_id: str, amount: float, reason: str) -> str:
    """Process a refund. REQUIRES MANAGER APPROVAL.

    Args:
        email: Customer email.
        invoice_id: Invoice to refund against.
        amount: Refund amount in PKR.
        reason: Reason for refund.
    """
    from shared.tools.db_tools import _query, _execute
    import uuid

    payments = _query(
        "SELECT id FROM payments WHERE invoice_id = %s LIMIT 1",
        (invoice_id.upper(),),
    )
    payment_id = payments[0]["id"] if payments and "error" not in payments[0] else None

    cust = _query("SELECT customer_id FROM customer_contacts WHERE email ILIKE %s LIMIT 1", (email,))
    cust_id = cust[0]["customer_id"] if cust and "error" not in cust[0] else None

    refund_id = f"REF-{abs(hash(str(uuid.uuid4()))) % 100000:05d}"

    if payment_id:
        _execute(
            "INSERT INTO refunds (id, payment_id, customer_id, amount, reason, status) VALUES (%s, %s, %s, %s, %s, 'pending')",
            (refund_id, payment_id, cust_id, amount, reason),
        )

    return (
        f"Refund processed:\n"
        f"  Refund ID: {refund_id}\n"
        f"  Customer: {email}\n"
        f"  Invoice: {invoice_id}\n"
        f"  Amount: PKR {amount:,.0f}\n"
        f"  Reason: {reason}\n"
        f"  Status: Pending approval\n"
        f"  ETA: 5-7 business days after approval"
    )


@function_tool
def apply_credit(email: str, amount: float, reason: str) -> str:
    """Apply account credit for goodwill or error correction.

    Args:
        email: Customer email.
        amount: Credit amount in PKR.
        reason: Reason for credit.
    """
    if amount > 5000:
        return f"Credits above PKR 5,000 require escalation. Requested: PKR {amount:,.0f}"
    return (
        f"Credit applied to {email}:\n"
        f"  Amount: PKR {amount:,.0f}\n"
        f"  Reason: {reason}\n"
        f"  Credit will be applied to next invoice."
    )


# --- Dynamic Instructions ---
def build_instructions(ctx, agent):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    customer_email = ctx.context.get("customer_email", "Unknown")
    return f"""You are the Billing Finance Agent for Actuator AI. Current time: {now}
CURRENT USER: {customer_email}

DATABASE ACCESS: You have a 'query' MCP tool for direct PostgreSQL access.
ALWAYS use the 'query' MCP tool to fetch real billing data before responding.
NEVER invent invoice amounts, dates, or plan information.

DATABASE SCHEMA:
- 'customers' (id, company_name, industry, status, health_score, mrr)
- 'customer_contacts' (id, customer_id, name, email, phone, role)
- 'subscriptions' (id, customer_id, product_id, status, billing_cycle, current_period_end, auto_renew)
- 'products' (id, name, slug, price_monthly, price_yearly, api_calls_limit, storage_gb, support_tier, is_active)
- 'invoices' (id, customer_id, amount, tax, total, currency, status, due_date, paid_at, payment_method, created_at)
- 'invoice_line_items' (id, invoice_id, description, quantity, unit_price, amount)
- 'payments' (id, invoice_id, method, status, processed_at)
- 'refunds' (id, payment_id, customer_id, amount, reason, status)
- 'api_usage' (id, customer_id, month, api_calls, storage_used_gb, agent_sessions, webhook_events, overage_amount)

STEP-BY-STEP PROTOCOL:
1. For billing overview: query subscriptions+products+customer_contacts JOIN
2. For specific invoice: query invoices WHERE id = 'INV-XXXX', then query invoice_line_items
3. For refund request: confirm invoice exists in DB, then call process_refund tool (REQUIRES APPROVAL)
4. For plan query: query products WHERE is_active = true ORDER BY price_monthly
5. For plan change: call change_plan tool
6. For credits up to PKR 5000: call apply_credit tool directly

AVAILABLE TOOLS: query (MCP), change_plan, process_refund (needs approval), apply_credit

RULES:
- NEVER use tool names not listed above (no check_refund_status, no get_billing_info)
- Refunds ALWAYS require manager approval via process_refund tool
- Credits up to PKR 5,000 can be applied directly
- Never share full payment card numbers
- Always quote exact DB values for amounts and dates
- WARNING: DO NOT WRITE YOUR OWN SQL QUERIES. ONLY USE THE EXACT SQL PATTERNS DESCRIBED ABOVE. NEVER INVENT TABLES OR COLUMNS!"""


# --- Agent ---
agent = Agent(
    name="Billing Finance Agent",
    instructions=build_instructions,
    model=get_model(),
    model_settings=ModelSettings(temperature=0.2, max_tokens=1000),
    tools=[
        change_plan,
        process_refund,
        apply_credit,
    ],
    input_guardrails=[detect_jailbreak, detect_pii],
    handoff_description="Billing and finance: invoices, payments, refunds, plan changes, usage, credits, billing disputes",
)


async def main():
    queries = [
        "Show me the invoice INV-2026-0401 for TechVista.",
    ]
    for query in queries:
        print(f"\n{'='*60}\nQuery: {query}")
        result = await Runner.run(agent, query)
        if result.interruptions:
            print("⚠ REFUND NEEDS APPROVAL")
            state = result.to_state()
            for i in result.interruptions:
                answer = input(f"  Approve '{i.raw_item.name}'? (y/n): ").strip().lower()
                if answer == "y":
                    state.approve(i)
            result = await Runner.run(agent, state)
        print(f"Response:\n{result.final_output}")


if __name__ == "__main__":
    asyncio.run(main())
