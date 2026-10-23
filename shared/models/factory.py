"""OpenAI-compatible LLM provider factory."""

import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel, set_tracing_disabled

_env_file = ".env.production" if os.path.isfile(".env.production") else ".env"
load_dotenv(_env_file)
set_tracing_disabled(True)

_client_cache = {}


# Transient provider failures (503 high demand, 429 rate limit) retry with
# exponential backoff. OpenAI SDK default is only 2 attempts.
_MAX_PROVIDER_RETRIES = 5


def _get_client(base_url: str | None, api_key: str) -> AsyncOpenAI:
    cache_key = f"{base_url}:{api_key}"
    if cache_key not in _client_cache:
        if base_url:
            _client_cache[cache_key] = AsyncOpenAI(
                base_url=base_url, api_key=api_key, max_retries=_MAX_PROVIDER_RETRIES
            )
        else:
            _client_cache[cache_key] = AsyncOpenAI(api_key=api_key, max_retries=_MAX_PROVIDER_RETRIES)
    return _client_cache[cache_key]


def get_model(model_name: str | None = None) -> OpenAIChatCompletionsModel:
    """Create a model for the configured OpenAI-compatible endpoint."""
    openai_key = (os.getenv("OPENAI_API_KEY") or "").strip()

    if openai_key:
        base_url = (os.getenv("OPENAI_BASE_URL") or "").strip() or None
        target_model = (
            model_name
            or os.getenv("OPENAI_MODEL")
            or "gpt-4o-mini"
        ).strip()
        client = _get_client(base_url=base_url, api_key=openai_key)
        return OpenAIChatCompletionsModel(model=target_model, openai_client=client)

    raise RuntimeError(
        "OPENAI_API_KEY is not configured. Set OPENAI_API_KEY, "
        "OPENAI_BASE_URL, and OPENAI_MODEL for the configured provider."
    )
