"""
shared/models/groq_provider.py — LLM Provider (OmniRouter-backed)

Everything routes through OmniRouter. Kept for backward compatibility.
"""

from shared.models.factory import get_model as factory_get_model


def get_model(model_name: str | None = None):
    """Get model from OmniRouter via unified factory."""
    return factory_get_model(model_name)
