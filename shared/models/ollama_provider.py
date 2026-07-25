"""
shared/models/ollama.py — Ollama Local/Cloud Model Provider

Usage:
    from shared.models.ollama_provider import get_model
    agent = Agent(name="My Agent", instructions="...", model=get_model())

Best cloud models for tool-calling + handoffs (no local GPU needed):
    1. deepseek-v3.1:671b-cloud  ← RECOMMENDED (strongest tool calls, agentic chains)
    2. gpt-oss:120b-cloud        ← GPT architecture, native tool schema support
    3. qwen3-coder:480b-cloud    ← Great for structured output & code reasoning
    4. nemotron-3-super:cloud    ← NVIDIA, strong instruction following
    5. qwen3.5:cloud             ← Fast, lighter option for simpler tasks
"""

import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel, set_tracing_disabled


load_dotenv()
set_tracing_disabled(True)

_client = None
_client_base_url = None

def _get_client() -> AsyncOpenAI:
    global _client, _client_base_url
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    api_key = os.getenv("OLLAMA_API_KEY") or os.getenv("OPENAI_API_KEY") or "ollama"
    
    if _client is None or _client_base_url != base_url:
        _client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        _client_base_url = base_url
    return _client


from shared.models.factory import get_model as factory_get_model


def get_model(model_name: str | None = None) -> OpenAIChatCompletionsModel:
    """Get model from unified factory (defaults to LLM_PROVIDER env variable)."""
    return factory_get_model(model_name)


