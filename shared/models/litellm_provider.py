"""
shared/models/litellm_provider.py — LiteLLM Multi-Provider (100+ LLMs)

Only use for direct LiteLLM routing outside OmniRouter.
Most consumers should use shared.models.ollama_provider which routes
everything through OmniRouter automatically.
"""

from agents import set_tracing_disabled


set_tracing_disabled(True)

def get_model(model_string: str, base_url: str | None = None):
    """Get a LiteLLM-backed model.

    Args:
        model_string: LiteLLM model string, e.g. 'openai/gpt-4o'
        base_url: Override base URL
    """
    from agents.extensions.models.litellm_model import LitellmModel
    kwargs = {"model": model_string}
    if base_url:
        kwargs["base_url"] = base_url
    return LitellmModel(**kwargs)
