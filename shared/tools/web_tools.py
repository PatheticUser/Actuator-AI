"""shared/tools/web_tools.py — Web Search via Tavily API"""

import os
import httpx
from agents import function_tool


TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
TAVILY_URL = "https://api.tavily.com/search"


@function_tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web using Tavily. Returns relevant results with snippets.

    Args:
        query: Search query string.
        max_results: Number of results to return (1-10).
    """
    if not TAVILY_API_KEY:
        return "[ERROR] TAVILY_API_KEY not set. Add it to .env file."

    try:
        response = httpx.post(
            TAVILY_URL,
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "max_results": min(max_results, 10),
                "search_depth": "basic",
                "include_answer": True,
            },
            timeout=15.0,
        )
        response.raise_for_status()
        data = response.json()

        # Format results
        parts = []
        if data.get("answer"):
            parts.append(f"Summary: {data['answer']}")

        for i, result in enumerate(data.get("results", []), 1):
            title = result.get("title", "Untitled")
            url = result.get("url", "")
            snippet = result.get("content", "")[:200]
            parts.append(f"\n[{i}] {title}\n    URL: {url}\n    {snippet}")

        return "\n".join(parts) if parts else "No results found."

    except httpx.HTTPError as e:
        return f"[ERROR] Tavily search failed: {e}"
    except Exception as e:
        return f"[ERROR] Unexpected error: {e}"


@function_tool
def fetch_url_content(url: str) -> str:
    """Fetch and extract text content from a URL.

    Args:
        url: Full URL to fetch content from.
    """
    try:
        response = httpx.get(
            url,
            timeout=15.0,
            headers={"User-Agent": "ActuatorAI/1.0"},
            follow_redirects=True,
        )
        response.raise_for_status()
        # Return first 3000 chars of text content
        text = response.text[:3000]
        return f"Content from {url}:\n{text}"
    except httpx.HTTPError as e:
        return f"[ERROR] Failed to fetch {url}: {e}"
