"""backend/models/conversation.py — Conversation & Message DB Models"""

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql.sqltypes import String
from typing import Optional
from datetime import datetime, timezone
import uuid


class Conversation(SQLModel, table=True):
    """Track each chat session."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    customer_email: Optional[str] = Field(default=None, index=True)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None
    status: str = Field(default="active")  # active, resolved, escalated
    last_agent: Optional[str] = None
    summary: Optional[str] = None


class Message(SQLModel, table=True):
    """Individual messages in a conversation."""
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: str = Field(index=True)
    role: str  # user, assistant, system, tool
    content: str
    agent_name: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Customer(SQLModel, table=True):
    """Customer records."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: Optional[str] = None
    plan: str = Field(default="free")  # free, pro, enterprise
    status: str = Field(default="active")  # active, locked, suspended
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SupportTicket(SQLModel, table=True):
    """Support ticket — mirrors backend/db/schema.sql `support_tickets`.

    MUST match that shape exactly: the same table is written by the agents'
    db_tools (create_support_ticket) and seeded from schema.sql. Keeping the
    two in sync prevents SQLModel's create_all from conflicting with the
    business schema at startup.
    """
    __tablename__ = "support_tickets"
    id: str = Field(primary_key=True)
    customer_id: Optional[int] = Field(default=None)
    contact_email: Optional[str] = Field(default=None, index=True)
    category: str
    priority: str  # P1, P2, P3, P4
    subject: str
    description: Optional[str] = None
    status: str = Field(default="open")  # open, in_progress, waiting, resolved, closed
    assigned_to: Optional[str] = None
    sla_deadline: Optional[datetime] = None
    first_response_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    satisfaction: Optional[int] = None
    tags: Optional[list[str]] = Field(default=None, sa_column=Column(ARRAY(String)))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
