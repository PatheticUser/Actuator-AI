"""backend/api/routes/agents.py — Agent info & management endpoints"""

from fastapi import APIRouter

from backend.api.schemas import AgentInfoResponse
from backend.services.agent_service import list_agents, get_agent_info

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.get("/", response_model=list[dict])
def get_all_agents():
    """List all registered agents with metadata."""
    return list_agents()


@router.get("/{agent_key}", response_model=AgentInfoResponse)
def get_agent(agent_key: str):
    """Get detailed info about a specific agent."""
    info = get_agent_info(agent_key)
    if not info:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Agent '{agent_key}' not found.")
    return info
