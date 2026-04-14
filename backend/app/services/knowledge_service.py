"""Knowledge service — creates DB records and enqueues ARQ indexing jobs."""

import os
import uuid

from arq.connections import ArqRedis
from fastapi import HTTPException, UploadFile, status

from app.models.enums import IndexingStatus, KnowledgeSourceType
from app.models.knowledge import AgentKnowledge
from app.repositories.knowledge_repo import KnowledgeRepository
from app.services.embedder import delete_source_vectors
from app.workers.knowledge_worker import TEMP_UPLOAD_DIR

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_CHAR_COUNT = 100_000


class KnowledgeService:
    def __init__(self, repo: KnowledgeRepository, arq: ArqRedis) -> None:
        self._repo = repo
        self._arq = arq

    # ─── URL source ──────────────────────────────────────────────────────────

    async def add_url(
        self,
        *,
        agent_id: uuid.UUID,
        root_url: str,
        path_filter: str | None = None,
        max_pages: int = 10,
    ) -> AgentKnowledge:
        """Create a PENDING knowledge record and enqueue crawl job."""
        item = await self._repo.create(
            agent_id=agent_id,
            source_type=KnowledgeSourceType.URL,
            title=root_url,
            root_url=root_url,
            path_filter=path_filter,
            max_pages=max_pages,
        )
        await self._arq.enqueue_job(
            "index_url_source",
            knowledge_id=str(item.id),
            root_url=root_url,
            path_filter=path_filter,
            max_pages=max_pages,
            agent_id=str(agent_id),
        )
        return item

    async def add_single_page(
        self,
        *,
        knowledge_id: uuid.UUID,
        agent_id: uuid.UUID,
        page_url: str,
    ) -> AgentKnowledge:
        """Add a missing page to an existing URL source and enqueue a single-page crawl."""
        item = await self._repo.get_by_id(knowledge_id)
        if item is None or item.agent_id != agent_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
        if item.source_type != KnowledgeSourceType.URL:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only add pages to URL-type sources",
            )
        await self._arq.enqueue_job(
            "index_single_page",
            knowledge_id=str(knowledge_id),
            page_url=page_url,
            agent_id=str(agent_id),
        )
        return item

    async def remove_crawled_page(
        self,
        *,
        knowledge_id: uuid.UUID,
        agent_id: uuid.UUID,
        page_url: str,
    ) -> AgentKnowledge:
        """Remove a specific crawled page and delete its vectors from Qdrant."""
        item = await self._repo.get_by_id(knowledge_id)
        if item is None or item.agent_id != agent_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

        # Delete vectors for this specific page (keyed as knowledge_id::page_url)
        page_source_id = f"{knowledge_id}::{page_url}"
        await delete_source_vectors(str(agent_id), page_source_id)

        return await self._repo.remove_crawled_page(item, page_url)

    # ─── File source ─────────────────────────────────────────────────────────

    async def add_document(
        self, *, agent_id: uuid.UUID, file: UploadFile
    ) -> AgentKnowledge:
        """Save uploaded file to temp storage, create PENDING record, enqueue parse job."""
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File exceeds 10 MB limit",
            )

        filename = file.filename or "document"
        item = await self._repo.create(
            agent_id=agent_id,
            source_type=KnowledgeSourceType.FILE,
            title=filename,
            file_name=filename,
            file_size=len(content),
        )

        # Save bytes to temp path so the worker can read them
        os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)
        temp_path = os.path.join(TEMP_UPLOAD_DIR, str(item.id))
        with open(temp_path, "wb") as f:
            f.write(content)

        await self._arq.enqueue_job(
            "index_file_source",
            knowledge_id=str(item.id),
            agent_id=str(agent_id),
            filename=filename,
        )
        return item

    # ─── Text source ─────────────────────────────────────────────────────────

    async def add_text(
        self, *, agent_id: uuid.UUID, title: str, content: str
    ) -> AgentKnowledge:
        """Enqueue text indexing job."""
        if not content.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Content cannot be empty",
            )

        content = content[:MAX_CHAR_COUNT]
        item = await self._repo.create(
            agent_id=agent_id,
            source_type=KnowledgeSourceType.TEXT,
            title=title,
            content=content,
        )
        await self._arq.enqueue_job(
            "index_text_source",
            knowledge_id=str(item.id),
            agent_id=str(agent_id),
            text=content,
        )
        return item

    # ─── Read / delete ────────────────────────────────────────────────────────

    async def get_status(
        self, *, knowledge_id: uuid.UUID, agent_id: uuid.UUID
    ) -> AgentKnowledge:
        item = await self._repo.get_by_id(knowledge_id)
        if item is None or item.agent_id != agent_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
        return item

    async def list_sources(self, *, agent_id: uuid.UUID) -> list[AgentKnowledge]:
        return await self._repo.get_by_agent(agent_id)

    async def delete_source(
        self, *, source_id: uuid.UUID, agent_id: uuid.UUID
    ) -> None:
        item = await self._repo.get_by_id(source_id)
        if item is None or item.agent_id != agent_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

        await self._arq.enqueue_job(
            "remove_source_vectors",
            agent_id=str(agent_id),
            source_id=str(source_id),
        )
        await self._repo.delete(item)
