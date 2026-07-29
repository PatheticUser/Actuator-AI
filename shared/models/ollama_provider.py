"""
shared/models/ollama_provider.py — LLM Provider (OmniRouter-backed)

All agents import from here. Delegates to unified factory which routes
everything through OmniRouter for auto provider selection + failover.

Usage:
    from shared.models.ollama_provider import get_model
    agent = Agent(name="My Agent", instructions="...", model=get_model())
"""

from shared.models.factory import get_model as factory_get_model


def get_model(model_name: str | None = None):
    """Get model from OmniRouter via unified factory."""
    return factory_get_model(model_name)
