"""Pydantic schemas for knowledge base."""

import uuid
from datetime import datetime

from pydantic import BaseModel, HttpUrl

from app.models.enums import KnowledgeSourceType


class AddUrlRequest(BaseModel):
    url: str  # validated by crawler at runtime


class AddTextRequest(BaseModel):
    title: str
    content: str


class KnowledgeResponse(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    source_type: KnowledgeSourceType
    title: str
    file_name: str | None
    file_size: int | None
    chunk_count: int
    char_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeListResponse(BaseModel):
    data: list[KnowledgeResponse]
    total: int
