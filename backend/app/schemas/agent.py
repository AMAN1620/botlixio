"""Pydantic schemas for Agent CRUD."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import AgentStatus, LLMProvider


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    system_prompt: str = "You are a helpful customer support assistant."
    welcome_message: str | None = "Hi! How can I help you today?"
    fallback_message: str | None = "I'm sorry, I didn't understand that. Could you rephrase?"
    primary_color: str | None = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    model: str = "gpt-4o-mini"
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(1024, ge=64, le=4096)


class AgentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    system_prompt: str | None = None
    welcome_message: str | None = None
    fallback_message: str | None = None
    primary_color: str | None = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    model: str | None = None
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(None, ge=64, le=4096)


class AgentResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str | None
    system_prompt: str
    welcome_message: str | None
    fallback_message: str | None
    primary_color: str | None
    model: str
    provider: LLMProvider
    temperature: float
    max_tokens: int
    status: AgentStatus
    total_messages: int
    total_sessions: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgentListResponse(BaseModel):
    data: list[AgentResponse]
    total: int
