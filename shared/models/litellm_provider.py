"""
shared/models/litellm_provider.py — LiteLLM Multi-Provider (100+ LLMs)

Usage:
    from shared.models.litellm_provider import get_model
    model = get_model("ollama_chat/qwen2.5:7b")       # Ollama
    model = get_model("groq/llama-3.1-8b-instant")     # Groq
    model = get_model("together_ai/meta-llama/...")     # Together

Requires: uv add litellm
"""

from agents import set_tracing_disabled


set_tracing_disabled(True)

def get_model(model_string: str, base_url: str | None = None):
    """Get a LiteLLM-backed model.

    Args:
        model_string: LiteLLM model string, e.g. 'ollama_chat/qwen2.5:7b'
        base_url: Override base URL (e.g. for Ollama: 'http://localhost:11434')
    """
    from agents.extensions.models.litellm_model import LitellmModel
    kwargs = {"model": model_string}
    if base_url:
        kwargs["base_url"] = base_url
    return LitellmModel(**kwargs)
