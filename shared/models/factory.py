"""
shared/models/factory.py — OmniRouter LLM Provider Factory

Routes all LLM calls through OmniRouter (self-hosted AI gateway).
OmniRouter auto-routes to 290+ providers with smart failover.
Model is set to "auto" so OmniRouter picks the best provider per request.

Requires: OMNIROUTER_BASE_URL and OMNIROUTER_API_KEY in .env
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
    """Get OmniRouter-backed model for Agents SDK.

    OmniRouter handles provider selection, failover, and compression.
    Default model "auto" lets OmniRouter pick the best provider per request.
    """
    base_url = os.getenv("OMNIROUTER_BASE_URL", "http://127.0.0.1:20128/v1")
    api_key = os.getenv("OMNIROUTER_API_KEY", "")
    target_model = model_name or os.getenv("OMNIROUTER_MODEL", "auto")
    if not api_key:
        print("⚠️  WARNING: OMNIROUTER_API_KEY is missing in environment variables.")
    client = _get_client(base_url=base_url, api_key=api_key or "missing")
    return OpenAIChatCompletionsModel(model=target_model, openai_client=client)
