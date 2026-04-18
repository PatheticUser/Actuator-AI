"""backend/services/agent_service.py — Agent orchestration service

Bridges FastAPI ↔ OpenAI Agents SDK. Handles:
  - Loading the supervisor + all specialist agents
  - Running conversations through the agent pipeline
  - Creating fresh MCP connections per request
  - Persisting messages to database
"""

import asyncio
import traceback
from datetime import datetime, timezone
from sqlmodel import Session, select

from agents import Runner, InputGuardrailTripwireTriggered

from actuator_agents.supervisor_router.agent import supervisor
from actuator_agents.technical_specialist.agent import agent as technical_specialist
from actuator_agents.account_security.agent import agent as account_security
from actuator_agents.billing_finance.agent import agent as billing_finance
from actuator_agents.success_retention.agent import agent as success_retention
from actuator_agents.operations_sync.agent import agent as operations_sync
from actuator_agents.linguistic.agent import agent as linguistic_agent
from actuator_agents.audit.agent import agent as audit_agent

from shared.mcp_config import create_mcp_postgres
from backend.models.conversation import Conversation, Message


# All agents that receive MCP DB access
_ALL_AGENTS = [
    supervisor, technical_specialist, account_security,
    billing_finance, success_retention, operations_sync,
    linguistic_agent, audit_agent,
]

# Lock prevents concurrent requests from clashing on shared agent objects
_run_lock = asyncio.Lock()


# Registry of all agents for info endpoint
AGENT_REGISTRY = {
    "supervisor_router": supervisor,
    "technical_specialist": technical_specialist,
    "account_security": account_security,
    "billing_finance": billing_finance,
    "success_retention": success_retention,
    "operations_sync": operations_sync,
    "linguistic": linguistic_agent,
    "audit": audit_agent,
}


def get_agent_info(agent_key: str) -> dict | None:
    """Get agent metadata."""
    agent = AGENT_REGISTRY.get(agent_key)
    if not agent:
        return None
    return {
        "name": agent.name,
        "description": agent.handoff_description or "Supervisor Router",
        "tool_count": len(agent.tools),
        "tools": [t.name for t in agent.tools],
    }


def list_agents() -> list[dict]:
    """List all registered agents."""
    return [
        {
            "key": key,
            "name": agent.name,
            "description": agent.handoff_description or "Central router and orchestrator",
            "tool_count": len(agent.tools),
        }
        for key, agent in AGENT_REGISTRY.items()
    ]


async def run_chat(
    message: str,
    conversation_id: str,
    db: Session,
    customer_email: str | None = None,
) -> dict:
    """Run a message through the supervisor agent pipeline.

    Creates a FRESH MCP server per request to avoid lifecycle conflicts.
    Returns dict with: response, agent_name, needs_approval, approval_items
    """
    try:
        # Rebuild conversation history from DB — EXCLUDE guardrail-blocked messages
        prior_messages = db.exec(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .where(Message.agent_name != "Guardrail")  # skip blocked exchanges
            .order_by(Message.created_at)
        ).all()

        input_list = []
        for msg in prior_messages:
            role = msg.role if msg.role in ("user", "assistant") else "user"
            input_list.append({"role": role, "content": msg.content})

        # Add current message to the input
        input_list.append({"role": "user", "content": message})

        # Create fresh MCP instance and run with lock
        async with _run_lock:
            mcp = create_mcp_postgres()
            await mcp.connect()
            print(f"✅ MCP connected for request")

            # Assign MCP to all agents
            for ag in _ALL_AGENTS:
                ag.mcp_servers = [mcp]

            try:
                result = await Runner.run(
                    supervisor,
                    input_list,
                    context={"customer_email": customer_email},
                )
            finally:
                # Always cleanup: remove MCP refs + disconnect
                for ag in _ALL_AGENTS:
                    ag.mcp_servers = []
                try:
                    await mcp.cleanup()
                    print(f"✅ MCP cleaned up")
                except Exception as cleanup_err:
                    print(f"⚠ MCP cleanup warning: {cleanup_err}")

        response_text = result.final_output or "No response generated."
        agent_name = result.last_agent.name if result.last_agent else "Supervisor Router"

        # Check for HITL approvals
        needs_approval = bool(result.interruptions)
        approval_items = []
        if needs_approval:
            for interruption in result.interruptions:
                approval_items.append(interruption.raw_item.name)

        # Save BOTH messages only AFTER successful processing
        user_msg = Message(
            conversation_id=conversation_id,
            role="user",
            content=message,
        )
        db.add(user_msg)

        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=response_text,
            agent_name=agent_name,
        )
        db.add(assistant_msg)

        # Update conversation
        conv = db.get(Conversation, conversation_id)
        if conv:
            conv.last_agent = agent_name

        db.commit()

        return {
            "response": response_text,
            "agent_name": agent_name,
            "needs_approval": needs_approval,
            "approval_items": approval_items,
        }

    except InputGuardrailTripwireTriggered as e:
        # DON'T save the blocked user message to DB — prevents poison history
        blocked_msg = f"⚠️ Message blocked by safety guardrail."
        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=blocked_msg,
            agent_name="Guardrail",
        )
        db.add(assistant_msg)
        db.commit()

        return {
            "response": blocked_msg,
            "agent_name": "Guardrail",
            "needs_approval": False,
            "approval_items": [],
        }

    except Exception as e:
        error_detail = str(e)
        print(f"⚠ Agent error: {error_detail}")
        traceback.print_exc()

        error_msg = f"Agent error: {error_detail}"
        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=error_msg,
            agent_name="System",
        )
        db.add(assistant_msg)
        db.commit()

        return {
            "response": error_msg,
            "agent_name": "System",
            "needs_approval": False,
            "approval_items": [],
        }
