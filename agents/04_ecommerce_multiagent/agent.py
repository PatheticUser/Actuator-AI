"""
04_ecommerce_multiagent/agent.py - E-Commerce Multi-Agent System

Concepts: Handoffs, triage routing, specialist agents, handoff callbacks
"""

import sys 
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from agents import Agent, Runner, function_tool, handoff

from shared.models.ollama_provider import get_model


MODEL = get_model()

# --- Tools ---
@function_tool
def track_order(order_id: str) -> str:
    """Track order shipping status."""
    return f"Order {order_id}: Shipped via TCS, delivery March 12."

@function_tool
def apply_discount(code: str) -> str:
    """Apply a discount code."""
    codes = {"SAVE10": "10% off applied!", "WELCOME": "15% off!"}
    return codes.get(code.upper(), f"Invalid code: {code}")

@function_tool
def get_product_info(name: str) -> str:
    """Get product details."""
    return f"{name}: PKR 4,999 | In stock | 4.5★ | Free shipping"


# --- Specialist Agents ---
order_agent = Agent(
    name="Order Specialist",
    instructions="Help with orders: tracking, cancellation, delivery issues.",
    model=MODEL, 
    tools=[track_order],
    handoff_description="Order tracking, cancellation, delivery",
)

product_agent = Agent(
    name="Product Specialist",
    instructions="Help with product info: specs, availability, comparisons.",
    model=MODEL, 
    tools=[get_product_info],
    handoff_description="Product info, specs, availability",
)

promo_agent = Agent(
    name="Promotions Specialist",
    instructions="Help with discounts, promo codes, deals.",
    model=MODEL, 
    tools=[apply_discount],
    handoff_description="Discount codes, promotions, deals",
)

escalation_agent = Agent(
    name="Manager",
    instructions="Handle escalated complaints with empathy and authority.",
    model=MODEL,
    handoff_description="Angry customers, complex disputes, escalations",
)


# --- Triage Router ---
triage = Agent(
    name="Triage",
    instructions="""Route customers to the right specialist:
    - Order issues → Order Specialist
    - Product questions → Product Specialist
    - Discount codes → Promotions Specialist
    - Angry/escalation → Manager
    Do NOT solve issues yourself. Just route.""",
    model=MODEL,
    handoffs=[
        order_agent, 
        product_agent, 
        promo_agent, 
        escalation_agent
    ],
)


async def main():
    scenarios = [
        "Where is my order ORD-7890?",
        # "Tell me about the wireless keyboard",
        # "I have code SAVE10",
        # "This is RIDICULOUS! 3 weeks waiting! I want a manager!",
    ]
    for msg in scenarios:
        result = await Runner.run(triage, msg)
        print(f"\n{msg}")
        print(f"→ {result.last_agent.name}")
        print(f"{result.final_output[:200]}")
        print("-" * 50)


if __name__ == "__main__":
    asyncio.run(main())
