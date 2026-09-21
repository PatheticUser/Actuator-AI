"""
shared/models/factory.py — Multi-Provider LLM Provider Factory

Supports:
1. Google AI Studio (Gemini 2.5 Flash / 1.5 Flash via OpenAI compatibility endpoint)
2. OmniRouter (self-hosted AI gateway auto-routing across 290+ providers)
3. Direct OpenAI or compatible endpoints
"""

import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel, set_tracing_disabled

load_dotenv()
set_tracing_disabled(True)

_client_cache = {}


def _get_client(base_url: str | None, api_key: str) -> AsyncOpenAI:
    cache_key = f"{base_url}:{api_key}"
    if cache_key not in _client_cache:
        if base_url:
            _client_cache[cache_key] = AsyncOpenAI(base_url=base_url, api_key=api_key)
        else:
            _client_cache[cache_key] = AsyncOpenAI(api_key=api_key)
    return _client_cache[cache_key]


def get_model(model_name: str | None = None) -> OpenAIChatCompletionsModel:
    """Get LLM model instance for OpenAI Agents SDK.

    Priority:
    1. GEMINI_API_KEY or GOOGLE_API_KEY (Google AI Studio OpenAI endpoint)
    2. OMNIROUTER_API_KEY (OmniRouter self-hosted gateway)
    3. OPENAI_API_KEY (direct OpenAI endpoint)
    """
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    omnirouter_key = os.getenv("OMNIROUTER_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if gemini_key:
        base_url = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
        target_model = model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        client = _get_client(base_url=base_url, api_key=gemini_key)
        return OpenAIChatCompletionsModel(model=target_model, openai_client=client)

    if omnirouter_key:
        base_url = os.getenv("OMNIROUTER_BASE_URL", "http://127.0.0.1:20128/v1")
        target_model = model_name or os.getenv("OMNIROUTER_MODEL", "auto")
        client = _get_client(base_url=base_url, api_key=omnirouter_key)
        return OpenAIChatCompletionsModel(model=target_model, openai_client=client)

    if openai_key:
        base_url = os.getenv("OPENAI_BASE_URL")
        target_model = model_name or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        client = _get_client(base_url=base_url, api_key=openai_key)
        return OpenAIChatCompletionsModel(model=target_model, openai_client=client)

    # Fallback to OmniRouter localhost defaults
    base_url = os.getenv("OMNIROUTER_BASE_URL", "http://127.0.0.1:20128/v1")
    target_model = model_name or "auto"
    client = _get_client(base_url=base_url, api_key="missing")
    return OpenAIChatCompletionsModel(model=target_model, openai_client=client)
