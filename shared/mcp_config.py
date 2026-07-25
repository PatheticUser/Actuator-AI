import os
import shutil
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

    # Prefer globally installed binary for instant startup (<100ms) without npx network overhead
    mcp_bin = shutil.which("mcp-server-postgres")
    if mcp_bin:
        command = mcp_bin
        args = [db_url]
    else:
        command = "npx"
        args = ["-y", "@modelcontextprotocol/server-postgres", db_url]

    return MCPServerStdio(
        params=MCPServerStdioParams(
            command=command,
            args=args,
            client_session_timeout_seconds=30.0,
        )
    )

