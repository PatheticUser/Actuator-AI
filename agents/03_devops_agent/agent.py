"""
03_devops_agent/agent.py — DevOps Incident Response Agent

Concepts: Async tools, Human-in-the-loop (needs_approval), multi-step reasoning
"""

import sys 
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from agents import Agent, Runner, function_tool

from shared.models.ollama_provider import get_model


@function_tool
def check_service_health(service: str) -> str:
    """Check health of a microservice."""
    services = {
        "api-gateway": "healthy | 45ms | 0.1% errors",
        "user-service": "degraded | 850ms | 12.5% errors",
        "payment-service": "healthy | 120ms | 0.3% errors",
    }
    return services.get(service, f"Unknown service: {service}")


@function_tool
def query_logs(service: str, level: str) -> str:
    """Query recent logs. Level: info, warn, error."""
    return (
        f"[ERROR] {service}: Connection pool exhausted\n"
        f"[ERROR] {service}: Timeout after 5000ms\n"
        f"[WARN]  {service}: Memory at 89%"
    )


@function_tool
def page_oncall(engineer: str, severity: str, message: str) -> str:
    """Page the on-call engineer."""
    return f"PAGED {engineer} [{severity}]: {message}"


@function_tool(needs_approval=True)
def restart_service(service: str) -> str:
    """Restart a service. REQUIRES HUMAN APPROVAL."""
    return f"{service} restart initiated. ETA: 30s."


agent = Agent(
    name="Incident Response Agent",
    instructions="""You are a DevOps incident response agent.
    
    PROTOCOL:
    1. check_service_health for the affected service
    2. If degraded: query_logs with level="error"
    3. If error_rate > 10%: page_oncall as P1, attempt restart_service
    4. If error_rate 5-10%: page_oncall as P2
    5. Provide incident summary
    
    On-call: Ahmed (ahmed@company.com). Be methodical.""",
    model=get_model(),
    tools=[
        check_service_health, 
        query_logs, 
        page_oncall, 
        restart_service
    ],
)


async def main():
    result = await Runner.run(
        agent, "ALERT: user-service showing high errors. Users can't login."
    )

    # if result.interruptions:
    #     print("APPROVAL NEEDED — Restart service?")
    #     for i in result.interruptions:
    #         print(f"   Action: {i.raw_item.name}")

    #     state = result.to_state()
    #     for i in result.interruptions:
    #         state.approve(i)  # Auto-approve for demo
    #     result = await Runner.run(agent, state)

    state = result.to_state()
    for i in result.interruptions:
        answer = input(f"   Approve '{i.raw_item.name}' on '{i.raw_item.arguments}'? (y/n): ").strip().lower()
        if answer == "y":
            state.approve(i)
    result = await Runner.run(agent, state)

    print(f"\n{result.final_output}")


if __name__ == "__main__":
    asyncio.run(main())
