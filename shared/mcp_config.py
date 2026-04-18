"""shared/mcp_config.py — MCP PostgreSQL Server Factory

Each agent MUST get its own MCPServerStdio instance.
Sharing a singleton causes lifecycle conflicts during handoffs
(connect/disconnect race → "Server not initialized" errors).
"""

import os
from dotenv import load_dotenv
from agents.mcp import MCPServerStdio, MCPServerStdioParams

load_dotenv()


def create_mcp_postgres() -> MCPServerStdio:
    """Create a fresh MCP PostgreSQL server instance.

    Each agent must call this separately — never share instances.
    The SDK manages connect/disconnect lifecycle per Runner.run() call.
    """
    db_url = (
        f"postgres://{os.getenv('POSTGRES_USER', 'postgres')}:"
        f"{os.getenv('POSTGRES_PASSWORD', 'postgres')}@"
        f"{os.getenv('POSTGRES_SERVER', 'localhost')}:"
        f"{os.getenv('POSTGRES_PORT', '5432')}/"
        f"{os.getenv('POSTGRES_DB', 'actuator_ai')}"
    )
    return MCPServerStdio(
        params=MCPServerStdioParams(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-postgres", db_url],
            client_session_timeout_seconds=30.0,
        )
    )
