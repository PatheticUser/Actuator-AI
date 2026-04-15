"""backend/services/agent_service.py — Agent orchestration service

Bridges FastAPI ↔ OpenAI Agents SDK. Handles:
  - Loading the supervisor + all specialist agents
  - Running conversations through the agent pipeline
  - Persisting messages to database
"""

import asyncio
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

from backend.models.conversation import Conversation, Message


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

    Returns dict with: response, agent_name, needs_approval, approval_items
    """
    # Save user message
    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=message,
    )
    db.add(user_msg)
    db.flush()

    try:
        # Rebuild conversation history from DB for context continuity
        prior_messages = db.exec(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        ).all()

        input_list = []
        for msg in prior_messages:
            role = msg.role if msg.role in ("user", "assistant") else "user"
            input_list.append({"role": role, "content": msg.content})

        # Run through supervisor with full conversation history
        result = await Runner.run(supervisor, input_list)

        response_text = result.final_output or "No response generated."
        agent_name = result.last_agent.name if result.last_agent else "Supervisor Router"

        # Check for HITL approvals
        needs_approval = bool(result.interruptions)
        approval_items = []
        if needs_approval:
            for interruption in result.interruptions:
                approval_items.append(interruption.raw_item.name)

        # Save assistant message
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
        blocked_msg = f"Message blocked by safety guardrail: {e}"
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
        error_msg = f"Agent error: {str(e)}"
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
