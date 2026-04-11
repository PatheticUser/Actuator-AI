"""shared/tools/web_tools.py — Web Search & Fetch Tools (stubs)"""
from agents import function_tool


@function_tool
def web_search(query: str) -> str:
    """Search the web for information. (Stub — integrate with real API)."""
    return f"[Stub] Search results for: {query}. Integrate DuckDuckGo, Tavily, or SerpAPI."
