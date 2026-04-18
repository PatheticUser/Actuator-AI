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

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

_client = None

def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
    return _client


def get_model(model_name: str | None = None) -> OpenAIChatCompletionsModel:
    """Get an Ollama-backed model for the Agents SDK.

    Args:
        model_name: Ollama model name (must be pulled first).
                    Defaults to OLLAMA_MODEL env var or 'qwen2.5:7b'.

    Returns:
        Model ready to use with Agent(model=...). 

    Requires:
        ollama pull <model_name>
        Models with tool-calling support: qwen2.5, llama3.1, mistral, qwen3
    """
    return OpenAIChatCompletionsModel(
        model=model_name or OLLAMA_DEFAULT_MODEL,
        openai_client=_get_client(),
    )
