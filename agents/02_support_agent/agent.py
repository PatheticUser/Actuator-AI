"""
02_support_agent/agent.py - Customer Support Agent

Concepts: Multiple tools, dynamic instructions, ModelSettings, Structured output (Try it...)
"""

import sys 
import os
import asyncio
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from agents import Agent, Runner, ModelSettings, function_tool

from shared.models.ollama_provider import get_model
# from shared.schemas.common import TicketClassification


# --- Tools ---
@function_tool
def lookup_customer(email: str) -> str:
    """Look up customer by email."""
    customers = {
        "ahmed@example.com": "Ahmed Hassan | Enterprise | PKR 29,900/mo | Since 2025",
        "sara@startup.io": "Sara Khan | Pro | PKR 4,900/mo | Since 2026",
    }
    return customers.get(email.lower(), f"No customer found: {email}")


@function_tool
def search_knowledge_base(query: str) -> str:
    """Search help articles."""
    kb = {
        "password": "Reset at Settings > Security > Change Password.",
        "billing": "Invoices generated on 1st of each month. Change plan at Settings > Billing.",
        "api": "API docs at docs.example.com. Rate limit: 1000 req/min (Pro).",
    }
    for key, val in kb.items():
        if key in query.lower():
            return val
    return "No article found. Escalate to human agent."


@function_tool
def create_ticket(email: str, category: str, description: str) -> str:
    """Create a support ticket."""
    tid = f"TKT-{abs(hash(description)) % 100000:05d}"
    return f"Ticket {tid} created for {email} [{category}]: {description[:80]}"


# --- Dynamic Instructions ---
def instructions(ctx, agent):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    return f"""You are a CloudSync customer support agent. Time: {now}
    WORKFLOW:
    1. Greet professionally
    2. Look up customer if email provided
    3. Search knowledge base for solutions
    4. If unresolved, create a ticket
    5. End with "Is there anything else?"
    
    Be empathetic, professional, concise."""


# --- Agent ---
agent = Agent(
    name="Support Agent",
    instructions=instructions,
    model=get_model(),
    model_settings=ModelSettings(temperature=0.3, max_tokens=800),
    tools=[
        lookup_customer, 
        search_knowledge_base, 
        create_ticket
    ],
)


async def main():
    queries = [
        "Hi, I'm ahmed@example.com. How do I reset my password?", 
        # "I was charged twice! This is frustrating.",
        # "What are the API rate limits for Pro plan?",
    ]
    for query in queries:
        print(f"\n{'='*50}\n{query}")
        result = await Runner.run(agent, query)
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
