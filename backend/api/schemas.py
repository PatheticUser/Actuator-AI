"""backend/api/schemas.py — API Request/Response Schemas"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# --- Chat ---
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    conversation_id: Optional[str] = None  # None = new conversation
    customer_email: Optional[str] = None


class ChatResponse(BaseModel):
    conversation_id: str
    response: str
    agent_name: str
    needs_approval: bool = False
    approval_items: list[str] = []


# --- Conversations ---
class ConversationResponse(BaseModel):
    id: str
    customer_email: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    status: str
    last_agent: Optional[str]
    summary: Optional[str]


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    agent_name: Optional[str]
    created_at: datetime


# --- Agents ---
class AgentInfoResponse(BaseModel):
    name: str
    description: str
    tool_count: int
    tools: list[str]


# --- Tickets ---
class TicketCreateRequest(BaseModel):
    customer_email: str
    category: str
    priority: str = "P3"
    subject: str
    description: Optional[str] = None
