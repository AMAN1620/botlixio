"""Knowledge base API routes — /api/v1/agents/{id}/knowledge"""

import uuid

from arq.connections import ArqRedis
from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.arq_pool import get_arq_pool
from app.core.database import get_db
from app.models.user import User
from app.repositories.agent_repo import AgentRepository
from app.repositories.knowledge_repo import KnowledgeRepository
from app.schemas.knowledge import (
    AddPageRequest,
    AddTextRequest,
    KnowledgeListResponse,
    KnowledgeResponse,
    KnowledgeStatusResponse,
    KnowledgeUrlRequest,
    RemovePageRequest,
)
from app.services.agent_service import AgentService
from app.services.knowledge_service import KnowledgeService

router = APIRouter(tags=["knowledge"])


# ─── Dependencies ─────────────────────────────────────────────────────────────

def _get_knowledge_svc(
    db: AsyncSession = Depends(get_db),
    arq: ArqRedis = Depends(get_arq_pool),
) -> KnowledgeService:
    return KnowledgeService(KnowledgeRepository(db), arq)


def _get_agent_svc(db: AsyncSession = Depends(get_db)) -> AgentService:
    return AgentService(AgentRepository(db))


async def _verify_agent_ownership(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    agent_svc: AgentService = Depends(_get_agent_svc),
) -> uuid.UUID:
    await agent_svc.get_agent(agent_id=agent_id, user=current_user)
    return agent_id


# ─── URL source ───────────────────────────────────────────────────────────────

@router.post(
    "/agents/{agent_id}/knowledge/url",
    response_model=KnowledgeResponse,
    status_code=status.HTTP_202_ACCEPTED,  # 202: accepted for async processing
)
async def add_url(
    agent_id: uuid.UUID = Depends(_verify_agent_ownership),
    body: KnowledgeUrlRequest = ...,
    svc: KnowledgeService = Depends(_get_knowledge_svc),
) -> KnowledgeResponse:
    """Start crawling a URL. Returns immediately with status=pending."""
    item = await svc.add_url(
        agent_id=agent_id,
        root_url=body.root_url,
        path_filter=body.path_filter,
        max_pages=body.max_pages,
    )
    return KnowledgeResponse.model_validate(item)


@router.post(
    "/agents/{agent_id}/knowledge/{knowledge_id}/pages",
    response_model=KnowledgeResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def add_page(
    agent_id: uuid.UUID = Depends(_verify_agent_ownership),
    knowledge_id: uuid.UUID = ...,
    body: AddPageRequest = ...,
    svc: KnowledgeService = Depends(_get_knowledge_svc),
) -> KnowledgeResponse:
    """Add a specific missing URL to an existing URL-type source."""
    item = await svc.add_single_page(
        knowledge_id=knowledge_id,
        agent_id=agent_id,
        page_url=body.url,
    )
    return KnowledgeResponse.model_validate(item)


@router.delete(
    "/agents/{agent_id}/knowledge/{knowledge_id}/pages",
    status_code=status.HTTP_200_OK,
    response_model=KnowledgeResponse,
)
async def remove_page(
    agent_id: uuid.UUID = Depends(_verify_agent_ownership),
    knowledge_id: uuid.UUID = ...,
    body: RemovePageRequest = ...,
    svc: KnowledgeService = Depends(_get_knowledge_svc),
) -> KnowledgeResponse:
    """Remove one crawled page from a URL source and delete its vectors."""
    item = await svc.remove_crawled_page(
        knowledge_id=knowledge_id,
        agent_id=agent_id,
        page_url=body.url,
    )
    return KnowledgeResponse.model_validate(item)


# ─── File source ──────────────────────────────────────────────────────────────

@router.post(
    "/agents/{agent_id}/knowledge/upload",
    response_model=KnowledgeResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_document(
    agent_id: uuid.UUID = Depends(_verify_agent_ownership),
    file: UploadFile = File(...),
    svc: KnowledgeService = Depends(_get_knowledge_svc),
) -> KnowledgeResponse:
    """Upload a file. Returns immediately with status=pending."""
    item = await svc.add_document(agent_id=agent_id, file=file)
    return KnowledgeResponse.model_validate(item)


# ─── Text source ──────────────────────────────────────────────────────────────

@router.post(
    "/agents/{agent_id}/knowledge/text",
    response_model=KnowledgeResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def add_text(
    agent_id: uuid.UUID = Depends(_verify_agent_ownership),
    body: AddTextRequest = ...,
    svc: KnowledgeService = Depends(_get_knowledge_svc),
) -> KnowledgeResponse:
    """Add raw text content. Returns immediately with status=pending."""
    item = await svc.add_text(
        agent_id=agent_id, title=body.title, content=body.content
    )
    return KnowledgeResponse.model_validate(item)


# ─── Status polling ───────────────────────────────────────────────────────────

@router.get(
    "/agents/{agent_id}/knowledge/{knowledge_id}/status",
    response_model=KnowledgeStatusResponse,
)
async def get_knowledge_status(
    agent_id: uuid.UUID = Depends(_verify_agent_ownership),
    knowledge_id: uuid.UUID = ...,
    svc: KnowledgeService = Depends(_get_knowledge_svc),
) -> KnowledgeStatusResponse:
    """Poll indexing status. Frontend calls this every 3s until indexed/failed."""
    item = await svc.get_status(knowledge_id=knowledge_id, agent_id=agent_id)
    return KnowledgeStatusResponse.model_validate(item)


# ─── List / delete ────────────────────────────────────────────────────────────

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
