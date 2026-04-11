"""
shared/models/groq_provider.py — Groq Cloud (Fast Inference)

Usage:
    from shared.models.groq_provider import get_model
    model = get_model()                          # Default: llama-3.1-8b-instant
    model = get_model("llama-3.3-70b-versatile") # Larger model

Requires: GROQ_API_KEY environment variable
"""

import os
from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel, set_tracing_disabled


set_tracing_disabled(True)

def get_model(model_name: str = "llama-3.1-8b-instant") -> OpenAIChatCompletionsModel:
    """Get a Groq-backed model for the Agents SDK."""
    client = AsyncOpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=os.getenv("GROQ_API_KEY"),
    )
    return OpenAIChatCompletionsModel(model=model_name, openai_client=client)
