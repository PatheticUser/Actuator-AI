"""shared/schemas/common.py — Reusable Pydantic Models for Agents"""

from typing import Literal
from pydantic import BaseModel, Field


class TicketClassification(BaseModel):
    category: Literal["billing", "technical", "account", "general"] = Field(
        description="Which department handles this"
    )
    priority: Literal["P1-critical", "P2-high", "P3-medium", "P4-low"] = Field(
        description="Ticket priority"
    )
    sentiment: Literal["angry", "frustrated", "neutral", "positive"] = Field(
        description="Customer sentiment"
    )
    summary: str = Field(description="One-line summary")


class ProductClassification(BaseModel):
    category: Literal["electronics", "clothing", "food", "books", "other"] = Field(
        description="Product category"
    )
    urgency: Literal["low", "medium", "high"] = Field(description="Urgency level")
    price_range: Literal["budget", "mid", "premium"] = Field(description="Price range")
    search_query: str = Field(description="Optimized catalog search query")
    confidence: float = Field(description="Confidence 0.0-1.0")


class UserProfile(BaseModel):
    name: str = Field(description="User's name")
    email: str = Field(description="User's email")
    plan: Literal["free", "pro", "enterprise"] = Field(description="Subscription plan")
    is_active: bool = Field(description="Account active status")
