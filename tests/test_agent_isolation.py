import pytest
from backend.services.agent_service import create_isolated_agent_pipeline
from actuator_agents.supervisor_router.agent import supervisor

def test_create_isolated_agent_pipeline_separate_references():
    sup1, all1 = create_isolated_agent_pipeline()
    sup2, all2 = create_isolated_agent_pipeline()

    # Verify not same reference as original
    assert sup1 is not supervisor
    assert sup2 is not supervisor
    assert sup1 is not sup2

    # Verify mutating one isolated pipeline does not affect the other or global
    fake_mcp_1 = "mcp_client_1"
    for ag in all1:
        ag.mcp_servers = [fake_mcp_1]

    assert sup1.mcp_servers == [fake_mcp_1]
    assert sup2.mcp_servers == []
    assert supervisor.mcp_servers == []

    # Cleanup
    for ag in all1:
        ag.mcp_servers = []
    assert sup1.mcp_servers == []
