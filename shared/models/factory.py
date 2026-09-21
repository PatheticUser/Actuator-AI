"""
shared/models/factory.py — Multi-Provider LLM Provider Factory

Supports:
1. Google AI Studio (Gemini Flash via OpenAI compatibility endpoint)
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
    gemini_key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
    omnirouter_key = (os.getenv("OMNIROUTER_API_KEY") or "").strip()
    openai_key = (os.getenv("OPENAI_API_KEY") or "").strip()

    if gemini_key:
        base_url = (os.getenv("GEMINI_BASE_URL") or "https://generativelanguage.googleapis.com/v1beta/openai/").strip()
        target_model = (model_name or os.getenv("GEMINI_MODEL") or "gemini-3.6-flash").strip()
        client = _get_client(base_url=base_url, api_key=gemini_key)
        return OpenAIChatCompletionsModel(model=target_model, openai_client=client)

    if omnirouter_key:
        base_url = (os.getenv("OMNIROUTER_BASE_URL") or "http://127.0.0.1:20128/v1").strip()
        target_model = (model_name or os.getenv("OMNIROUTER_MODEL") or "auto").strip()
        client = _get_client(base_url=base_url, api_key=omnirouter_key)
        return OpenAIChatCompletionsModel(model=target_model, openai_client=client)

    if openai_key:
        base_url = (os.getenv("OPENAI_BASE_URL") or "").strip() or None
        target_model = (model_name or os.getenv("OPENAI_MODEL") or "gpt-4o-mini").strip()
        client = _get_client(base_url=base_url, api_key=openai_key)
        return OpenAIChatCompletionsModel(model=target_model, openai_client=client)

    # Fallback to OmniRouter localhost defaults
    base_url = (os.getenv("OMNIROUTER_BASE_URL") or "http://127.0.0.1:20128/v1").strip()
    target_model = (model_name or "auto").strip()
    client = _get_client(base_url=base_url, api_key="missing")
    return OpenAIChatCompletionsModel(model=target_model, openai_client=client)
