"""Widget chat API — public endpoints, no authentication required."""

import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.enums import AgentStatus
from app.repositories.agent_repo import AgentRepository
from app.repositories.chat_repo import ChatRepository
from app.schemas.chat import ChatRequest, ChatResponse, WidgetStatusResponse
from app.services.chat_engine import process_message

router = APIRouter(prefix="/widget", tags=["widget"])


def _get_agent_repo(db: AsyncSession = Depends(get_db)) -> AgentRepository:
    return AgentRepository(db)


def _get_chat_repo(db: AsyncSession = Depends(get_db)) -> ChatRepository:
    return ChatRepository(db)


@router.get("/{agent_id}/status", response_model=WidgetStatusResponse)
async def widget_status(
    agent_id: uuid.UUID,
    agent_repo: AgentRepository = Depends(_get_agent_repo),
) -> WidgetStatusResponse:
    agent = await agent_repo.get_by_id(agent_id)
    if agent is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return WidgetStatusResponse(
        agent_id=agent.id,
        name=agent.name,
        welcome_message=agent.welcome_message or "Hi! How can I help you?",
        primary_color=agent.primary_color or "#2513EC",
        is_live=agent.status == AgentStatus.LIVE,
    )


@router.post("/{agent_id}/chat", response_model=ChatResponse)
async def widget_chat(
    agent_id: uuid.UUID,
    body: ChatRequest,
    request: Request,
    agent_repo: AgentRepository = Depends(_get_agent_repo),
    chat_repo: ChatRepository = Depends(_get_chat_repo),
) -> ChatResponse:
    from fastapi import HTTPException

    agent = await agent_repo.get_by_id(agent_id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    # Use provided session_id or fall back to client IP
    session_identifier = body.session_id or request.client.host or "anonymous"

    result = await process_message(
        agent=agent,
        session_identifier=session_identifier,
        user_message=body.message,
        chat_repo=chat_repo,
    )
    return ChatResponse(reply=result["reply"], session_id=result["session_id"], sources=result.get("sources", []))
