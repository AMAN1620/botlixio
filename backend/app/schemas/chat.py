"""Pydantic schemas for widget chat API."""

import uuid
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str | None = Field(None, max_length=255)
    message: str = Field(..., min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    sources: list[str] = []


class WidgetStatusResponse(BaseModel):
    agent_id: uuid.UUID
    name: str
    welcome_message: str
    primary_color: str
    is_live: bool
