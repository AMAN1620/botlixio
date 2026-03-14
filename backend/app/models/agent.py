"""Agent model — name, provider, model, prompt, tools, channels."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AgentStatus, LLMProvider


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    system_prompt: Mapped[str] = mapped_column(
        Text, default="You are a helpful assistant."
    )
    provider: Mapped[LLMProvider] = mapped_column(default=LLMProvider.OPENAI)
    model: Mapped[str] = mapped_column(String(100), default="gpt-4o-mini")
    temperature: Mapped[float] = mapped_column(default=0.7)
    max_tokens: Mapped[int] = mapped_column(default=1024)
    status: Mapped[AgentStatus] = mapped_column(default=AgentStatus.DRAFT)
    tools: Mapped[list] = mapped_column(JSONB, default=list)
    channels: Mapped[list] = mapped_column(JSONB, default=list)
    welcome_message: Mapped[str | None] = mapped_column(Text)
    fallback_message: Mapped[str | None] = mapped_column(Text)
    primary_color: Mapped[str | None] = mapped_column(String(7))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    total_messages: Mapped[int] = mapped_column(default=0)
    total_sessions: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="agents")  # noqa: F821
    knowledge_items: Mapped[list["AgentKnowledge"]] = relationship(  # noqa: F821
        back_populates="agent"
    )
    chat_sessions: Mapped[list["ChatSession"]] = relationship(  # noqa: F821
        back_populates="agent"
    )
    leads: Mapped[list["Lead"]] = relationship(back_populates="agent")  # noqa: F821
