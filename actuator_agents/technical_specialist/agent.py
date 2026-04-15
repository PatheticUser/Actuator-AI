"""
Technical Specialist Agent — Actuator AI

Combines: Tech Support + Knowledge Base RAG
Tools query PostgreSQL for KB articles, system status, and tickets.
"""

import sys
import os
import asyncio
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from agents import Agent, Runner, ModelSettings, function_tool

from shared.models.ollama_provider import get_model
from shared.mcp_config import get_mcp_postgres
from shared.guardrails.safety import detect_jailbreak, detect_sql_injection
from shared.tools.db_tools import search_knowledge_base, query_tickets, create_support_ticket, get_ticket_details


# --- Agent-specific tools (not in DB) ---

@function_tool
def diagnose_service(service_name: str, error_code: str) -> str:
    """Run diagnostics on a service given error code. Returns diagnosis.

    Args:
        service_name: Name of service, e.g. 'user-service', 'api-gateway'.
        error_code: HTTP error code or keyword like '500', '502', 'timeout'.
    """
    diagnostics = {
        "500": f"{service_name}: Internal server error. Check application logs. "
               "Common causes: unhandled exception, DB connection timeout, OOM.",
        "502": f"{service_name}: Bad gateway. Upstream service unreachable. "
               "Check service health, network policies, and load balancer config.",
        "503": f"{service_name}: Service unavailable. Likely overloaded or in maintenance. "
               "Check replica count, CPU/memory utilization.",
        "429": f"{service_name}: Rate limited. Client exceeding quota. "
               "Review rate limit tier and suggest upgrade or backoff strategy.",
        "401": f"{service_name}: Unauthorized. Token expired or invalid. "
               "Verify token refresh flow and check auth service health.",
        "timeout": f"{service_name}: Request timeout. P99 latency spike detected. "
                   "Check DB query performance, external API calls, connection pool exhaustion.",
    }
    return diagnostics.get(
        error_code.lower(),
        f"{service_name}: Unknown error '{error_code}'. Collecting logs for engineering review."
    )


@function_tool
def check_system_status(component: str) -> str:
    """Check real-time status of infrastructure components.

    Args:
        component: Component name, e.g. 'api-gateway', 'user-service', 'database-primary'.
    """
    # Production: query Prometheus/Grafana API
    statuses = {
        "api-gateway": "HEALTHY | Latency: 42ms | Error rate: 0.1% | Uptime: 99.97%",
        "auth-service": "HEALTHY | Latency: 28ms | Error rate: 0.0% | Uptime: 99.99%",
        "user-service": "DEGRADED | Latency: 890ms | Error rate: 8.2% | Uptime: 98.1%",
        "payment-service": "HEALTHY | Latency: 156ms | Error rate: 0.3% | Uptime: 99.95%",
        "notification-service": "MAINTENANCE | Scheduled until 03:00 UTC",
        "database-primary": "HEALTHY | Connections: 142/200 | Replication lag: 0ms",
        "database-replica": "HEALTHY | Connections: 89/200 | Replication lag: 12ms",
        "redis-cache": "HEALTHY | Memory: 2.1GB/8GB | Hit rate: 94.6%",
    }
    return statuses.get(
        component.lower(),
        f"Component '{component}' not found. Available: {', '.join(statuses.keys())}"
    )


# --- Dynamic Instructions ---
def build_instructions(ctx, agent):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    customer_email = ctx.context.get("customer_email", "Unknown")
    return f"""You are the Technical Specialist for Actuator AI. Current time: {now}
CURRENT USER: {customer_email}

DATABASE SCHEMA:
- 'knowledge_articles' (id, title, category, content, tags)
- 'support_tickets' (id, customer_id, contact_email, category, priority, subject, status)
- 'api_usage' (id, customer_id, month, api_calls, storage_used_gb)

CAPABILITIES:
- Search knowledge base (PostgreSQL) for documented solutions
- Diagnose API errors with specific error codes
- Check real-time infrastructure/system status
- Query and create support tickets

PROTOCOL:
1. Search knowledge base first for documented solutions
2. If infrastructure-related, check system status
3. If unresolved, create a support ticket with full context

RULES:
- Never guess — use tools for verified information
- Keep responses technically clean and minimal."""


# --- Agent ---
agent = Agent(
    name="Technical Specialist",
    instructions=build_instructions,
    model=get_model(),
    model_settings=ModelSettings(temperature=0.2, max_tokens=1200),
    tools=[
        search_knowledge_base,
        diagnose_service,
        check_system_status,
        query_tickets,
        get_ticket_details,
        create_support_ticket,
    ],
    mcp_servers=[get_mcp_postgres()],
    input_guardrails=[detect_jailbreak, detect_sql_injection],
    handoff_description="Technical issues: API errors, SDK problems, infrastructure, integrations, debugging",
)


async def main():
    queries = [
        "Our API is returning 502 errors on the user-service. Users can't log in.",
    ]
    for query in queries:
        print(f"\n{'='*60}\nQuery: {query}")
        result = await Runner.run(agent, query)
        print(f"Response:\n{result.final_output}")


if __name__ == "__main__":
    asyncio.run(main())
