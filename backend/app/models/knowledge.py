"""AgentKnowledge model — file/url/text content for RAG."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import IndexingStatus, KnowledgeSourceType


class AgentKnowledge(Base):
    __tablename__ = "agent_knowledge"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id"), index=True
    )
    source_type: Mapped[KnowledgeSourceType] = mapped_column()
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    raw_content: Mapped[str | None] = mapped_column(Text)
    file_name: Mapped[str | None] = mapped_column(String(255))
    file_size: Mapped[int | None] = mapped_column()
    chunk_count: Mapped[int] = mapped_column(default=1)
    char_count: Mapped[int] = mapped_column(default=0)

    # Indexing status tracking
    indexing_status: Mapped[IndexingStatus] = mapped_column(
        default=IndexingStatus.PENDING
    )
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    indexed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # URL crawl metadata (only set for source_type == URL)
    root_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    path_filter: Mapped[str | None] = mapped_column(String(255), nullable=True)
    max_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # List of { url, title, char_count } — populated after indexing
    crawled_pages: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    agent: Mapped["Agent"] = relationship(back_populates="knowledge_items")  # noqa: F821
