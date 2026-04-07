"""Knowledge base API routes — /api/v1/agents/{id}/knowledge"""

import uuid

from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.agent_repo import AgentRepository
from app.repositories.knowledge_repo import KnowledgeRepository
from app.schemas.knowledge import (
    AddTextRequest,
    AddUrlRequest,
    KnowledgeListResponse,
    KnowledgeResponse,
)
from app.services.agent_service import AgentService
from app.services.knowledge_service import KnowledgeService

router = APIRouter(tags=["knowledge"])


def _get_knowledge_svc(db: AsyncSession = Depends(get_db)) -> KnowledgeService:
    return KnowledgeService(KnowledgeRepository(db))


def _get_agent_svc(db: AsyncSession = Depends(get_db)) -> AgentService:
    return AgentService(AgentRepository(db))


async def _verify_agent_ownership(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    agent_svc: AgentService = Depends(_get_agent_svc),
) -> uuid.UUID:
    """Verify the current user owns the agent. Returns agent_id."""
    await agent_svc.get_agent(agent_id=agent_id, user=current_user)
    return agent_id


@router.post(
    "/agents/{agent_id}/knowledge/url",
    response_model=KnowledgeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_url(
    agent_id: uuid.UUID = Depends(_verify_agent_ownership),
    body: AddUrlRequest = ...,
    svc: KnowledgeService = Depends(_get_knowledge_svc),
) -> KnowledgeResponse:
    item = await svc.add_url(agent_id=agent_id, url=body.url)
    return KnowledgeResponse.model_validate(item)


@router.post(
    "/agents/{agent_id}/knowledge/upload",
    response_model=KnowledgeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    agent_id: uuid.UUID = Depends(_verify_agent_ownership),
    file: UploadFile = File(...),
    svc: KnowledgeService = Depends(_get_knowledge_svc),
) -> KnowledgeResponse:
    item = await svc.add_document(agent_id=agent_id, file=file)
    return KnowledgeResponse.model_validate(item)


@router.post(
    "/agents/{agent_id}/knowledge/text",
    response_model=KnowledgeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_text(
    agent_id: uuid.UUID = Depends(_verify_agent_ownership),
    body: AddTextRequest = ...,
    svc: KnowledgeService = Depends(_get_knowledge_svc),
) -> KnowledgeResponse:
    item = await svc.add_text(agent_id=agent_id, title=body.title, content=body.content)
    return KnowledgeResponse.model_validate(item)


@router.get("/agents/{agent_id}/knowledge", response_model=KnowledgeListResponse)
async def list_knowledge(
    agent_id: uuid.UUID = Depends(_verify_agent_ownership),
    svc: KnowledgeService = Depends(_get_knowledge_svc),
) -> KnowledgeListResponse:
    items = await svc.list_sources(agent_id=agent_id)
    return KnowledgeListResponse(
        data=[KnowledgeResponse.model_validate(i) for i in items],
        total=len(items),
    )


@router.delete(
    "/agents/{agent_id}/knowledge/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_knowledge(
    agent_id: uuid.UUID = Depends(_verify_agent_ownership),
    source_id: uuid.UUID = ...,
    svc: KnowledgeService = Depends(_get_knowledge_svc),
) -> None:
    await svc.delete_source(source_id=source_id, agent_id=agent_id)
