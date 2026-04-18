"""
Technical Specialist Agent — Actuator AI

Combines: Tech Support + Knowledge Base RAG
Uses MCP PostgreSQL for all database queries (KB articles, system status, tickets).
"""

import sys
import os
import asyncio
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from agents import Agent, Runner, ModelSettings, function_tool

from shared.models.ollama_provider import get_model
from shared.mcp_config import create_mcp_postgres
from shared.guardrails.safety import detect_jailbreak, detect_sql_injection
from shared.tools.db_tools import create_support_ticket


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

DATABASE ACCESS: You have a 'query' MCP tool for direct PostgreSQL access.
ALWAYS search the knowledge base via MCP before responding to technical issues.
NEVER invent solutions — base all answers on DB knowledge articles or tool outputs.

DATABASE SCHEMA:
- 'knowledge_articles' (id, title, category, content, tags TEXT[], views INT, helpful_votes INT, is_published BOOL)
- 'support_tickets' (id, customer_id, contact_email, category, priority, subject, description, status, assigned_to, sla_deadline, first_response_at, resolved_at, satisfaction, created_at)
- 'ticket_comments' (id, ticket_id, author, author_type, content, is_internal BOOL, created_at)
- 'api_usage' (id, customer_id, month VARCHAR, api_calls INT, storage_used_gb NUMERIC, agent_sessions INT, webhook_events INT, overage_amount NUMERIC)
- 'customers' (id, company_name, industry, status, health_score, mrr)
- 'customer_contacts' (id, customer_id, name, email, phone, role)

STEP-BY-STEP PROTOCOL:
1. Search knowledge base via MCP:
   SELECT title, content, tags FROM knowledge_articles WHERE is_published = true AND (title ILIKE '%<keyword>%' OR content ILIKE '%<keyword>%') ORDER BY helpful_votes DESC LIMIT 3
2. Check system status using check_system_status tool for the affected service
3. Diagnose error using diagnose_service tool with service name and error code
4. If unresolved: call create_support_ticket tool with full context
5. Share exact KB article content + diagnostic output in your response

AVAILABLE TOOLS: query (MCP), diagnose_service, check_system_status, create_support_ticket

RULES:
- Always search KB first — article content IS the answer
- Never guess — use tools for verified information
- For 5xx errors: always check system status
- Keep responses technically precise"""


# --- Agent ---
agent = Agent(
    name="Technical Specialist",
    instructions=build_instructions,
    model=get_model(),
    model_settings=ModelSettings(temperature=0.2, max_tokens=1200),
    tools=[
        diagnose_service,
        check_system_status,
        create_support_ticket,
    ],
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
