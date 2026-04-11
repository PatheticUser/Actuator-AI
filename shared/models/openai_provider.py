"""
shared/models/openai_provider.py — OpenAI Cloud Models

Usage:
    from shared.models.openai_provider import get_model
    model = get_model()                  # Default: gpt-5.4-mini
    model = get_model("gpt-5.4-mini")        # Specific model

Requires: OPENAI_API_KEY environment variable
"""


def get_model(model_name: str = "gpt-5.4-mini") -> str:
    """Return model string for OpenAI (SDK uses it natively)."""
    return model_name
