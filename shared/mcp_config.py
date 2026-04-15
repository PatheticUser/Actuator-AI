from agents.mcp import MCPServerStdio, MCPServerStdioParams

_mcp_postgres = None

def get_mcp_postgres():
    global _mcp_postgres
    if _mcp_postgres is None:
        _mcp_postgres = MCPServerStdio(
            params=MCPServerStdioParams(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-postgres", "postgres://postgres:postgres@localhost:5432/actuator_ai"],
                client_session_timeout_seconds=30.0
            )
        )
    return _mcp_postgres
