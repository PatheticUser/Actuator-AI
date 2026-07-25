"""
shared/models/factory.py — Unified Cloud & Local LLM Provider Factory

Supports:
  1. ModelScope (Qwen)          -> LLM_PROVIDER=modelscope  (DEFAULT)
  2. Groq (FREE tier, ultra fast) -> LLM_PROVIDER=groq
  3. OpenRouter (FREE models)    -> LLM_PROVIDER=openrouter
  4. OpenAI                     -> LLM_PROVIDER=openai
  5. Ollama (Local)              -> LLM_PROVIDER=ollama
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
    """Factory returning an OpenAI-compatible model based on LLM_PROVIDER env variable.

    Default provider: modelscope (Qwen)
    """
    provider = os.getenv("LLM_PROVIDER", "modelscope").lower().strip()

    if provider == "modelscope":
        api_key = os.getenv("MODELSCOPE_TOKEN", "")
        if not api_key:
            print("⚠️ WARNING: MODELSCOPE_TOKEN is missing in environment variables.")
        target_model = model_name or os.getenv("MODELSCOPE_MODEL", "Qwen-Ambassador/Qwen3.7-Max")
        client = _get_client(
            base_url="https://api-inference.modelscope.ai/v1",
            api_key=api_key or "ms_missing",
        )
        return OpenAIChatCompletionsModel(model=target_model, openai_client=client)

    elif provider == "groq":
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            print("⚠️ WARNING: GROQ_API_KEY is missing in environment variables.")
        target_model = model_name or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        client = _get_client(base_url="https://api.groq.com/openai/v1", api_key=api_key or "gsk_missing")
        return OpenAIChatCompletionsModel(model=target_model, openai_client=client)

    elif provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        if not api_key:
            print("⚠️ WARNING: OPENROUTER_API_KEY is missing in environment variables.")
        target_model = model_name or os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
        client = _get_client(base_url="https://openrouter.ai/api/v1", api_key=api_key or "or_missing")
        return OpenAIChatCompletionsModel(model=target_model, openai_client=client)

    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
        target_model = model_name or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        client = _get_client(base_url=None, api_key=api_key or "sk_missing")
        return OpenAIChatCompletionsModel(model=target_model, openai_client=client)

    else:  # "ollama" fallback
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        target_model = model_name or os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        api_key = os.getenv("OLLAMA_API_KEY") or os.getenv("OPENAI_API_KEY") or "ollama"
        client = _get_client(base_url=base_url, api_key=api_key)
        return OpenAIChatCompletionsModel(model=target_model, openai_client=client)
