"""Internal channel endpoints — WhatsApp and future channels.

Auth: every request must supply the X-Internal-Secret header matching
the INTERNAL_SECRET environment variable. If the env var is not set
the endpoint is treated as always-unauthorized (fail-closed).
"""

import os
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.agent_repo import AgentRepository
from app.repositories.chat_repo import ChatRepository
from app.services.chat_engine import process_message

router = APIRouter(prefix="/channels", tags=["channels"])


# ── Dependency helpers ────────────────────────────────────────────────────────

def _get_agent_repo(db: AsyncSession = Depends(get_db)) -> AgentRepository:
    return AgentRepository(db)


def _get_chat_repo(db: AsyncSession = Depends(get_db)) -> ChatRepository:
    return ChatRepository(db)


def _verify_internal_secret(x_internal_secret: str = Header(default="")) -> None:
    """Validate the X-Internal-Secret header against the env var.

    Fails closed: if INTERNAL_SECRET is not configured in the environment
    every request is rejected with 401.
    """
    expected = os.getenv("INTERNAL_SECRET")
    if not expected or x_internal_secret != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Internal-Secret header",
        )


# ── Schemas ───────────────────────────────────────────────────────────────────

class WhatsAppMessageRequest(BaseModel):
    agent_id: uuid.UUID
    sender_phone: str
    message: str
    user_id: str


class WhatsAppMessageResponse(BaseModel):
    reply: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/whatsapp/message",
    response_model=WhatsAppMessageResponse,
    status_code=status.HTTP_200_OK,
)
async def whatsapp_message(
    body: WhatsAppMessageRequest,
    _: None = Depends(_verify_internal_secret),
    agent_repo: AgentRepository = Depends(_get_agent_repo),
    chat_repo: ChatRepository = Depends(_get_chat_repo),
) -> WhatsAppMessageResponse:
    """Process an inbound WhatsApp message and return the agent reply."""
    agent = await agent_repo.get_by_id(body.agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    result = await process_message(
        agent=agent,
        session_identifier=body.sender_phone,
        user_message=body.message,
        chat_repo=chat_repo,
    )
    return WhatsAppMessageResponse(reply=result["reply"])
