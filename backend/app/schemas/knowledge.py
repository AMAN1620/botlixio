"""Pydantic schemas for knowledge base."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.enums import IndexingStatus, KnowledgeSourceType


class KnowledgeUrlRequest(BaseModel):
    root_url: str
    path_filter: str | None = None   # e.g. "/docs" — only crawl URLs with this prefix
    max_pages: int = Field(10, ge=1, le=20)

    @field_validator("root_url")
    @classmethod
    def must_be_http(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("root_url must start with http:// or https://")
        return v.rstrip("/")

    @field_validator("path_filter")
    @classmethod
    def normalise_path_filter(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if v and not v.startswith("/"):
            v = "/" + v
        return v or None


class RemovePageRequest(BaseModel):
    url: str


class AddPageRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def must_be_http(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("url must start with http:// or https://")
        return v


class AddTextRequest(BaseModel):
    title: str
    content: str


class CrawledPage(BaseModel):
    url: str
    title: str
    char_count: int


class KnowledgeResponse(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    source_type: KnowledgeSourceType
    title: str
    file_name: str | None
    file_size: int | None
    chunk_count: int
    char_count: int
    indexing_status: IndexingStatus
    error_message: str | None
    indexed_at: datetime | None
    root_url: str | None
    path_filter: str | None
    max_pages: int | None
    crawled_pages: list[CrawledPage] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeStatusResponse(BaseModel):
    id: uuid.UUID
    indexing_status: IndexingStatus
    chunk_count: int
    error_message: str | None
    indexed_at: datetime | None
    crawled_pages: list[CrawledPage] | None

    model_config = {"from_attributes": True}


class KnowledgeListResponse(BaseModel):
    data: list[KnowledgeResponse]
    total: int
