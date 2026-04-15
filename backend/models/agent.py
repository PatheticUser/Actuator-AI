from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone

class AgentBase(SQLModel):
    name: str = Field(index=True)
    description: Optional[str] = None
    model_name: str = "qwen2.5:7b"
    is_active: bool = True

class Agent(AgentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AgentCreate(AgentBase):
    pass

class AgentRead(AgentBase):
    id: int
    created_at: datetime
