"""Knowledge repository — CRUD for agent_knowledge table."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import IndexingStatus, KnowledgeSourceType
from app.models.knowledge import AgentKnowledge


class KnowledgeRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self,
        *,
        agent_id: uuid.UUID,
        source_type: KnowledgeSourceType,
        title: str,
        content: str = "",
        file_name: str | None = None,
        file_size: int | None = None,
        chunk_count: int = 0,
        # URL-specific
        root_url: str | None = None,
        path_filter: str | None = None,
        max_pages: int | None = None,
    ) -> AgentKnowledge:
        item = AgentKnowledge(
            agent_id=agent_id,
            source_type=source_type,
            title=title,
            content=content,
            file_name=file_name,
            file_size=file_size,
            chunk_count=chunk_count,
            char_count=len(content),
            indexing_status=IndexingStatus.PENDING,
            root_url=root_url,
            path_filter=path_filter,
            max_pages=max_pages,
        )
        self._db.add(item)
        await self._db.flush()
        await self._db.refresh(item)
        return item

    async def get_by_id(self, source_id: uuid.UUID) -> AgentKnowledge | None:
        result = await self._db.execute(
            select(AgentKnowledge).where(AgentKnowledge.id == source_id)
        )
        return result.scalar_one_or_none()

    async def get_by_agent(self, agent_id: uuid.UUID) -> list[AgentKnowledge]:
        result = await self._db.execute(
            select(AgentKnowledge)
            .where(AgentKnowledge.agent_id == agent_id)
            .order_by(AgentKnowledge.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        item: AgentKnowledge,
        status: IndexingStatus,
        *,
        error_message: str | None = None,
        chunk_count: int | None = None,
        content: str | None = None,
        content_hash: str | None = None,
        crawled_pages: list[dict] | None = None,
    ) -> AgentKnowledge:
        item.indexing_status = status
        if error_message is not None:
            item.error_message = error_message
        if chunk_count is not None:
            item.chunk_count = chunk_count
        if content is not None:
            item.content = content
            item.char_count = len(content)
        if content_hash is not None:
            item.content_hash = content_hash
        if crawled_pages is not None:
            item.crawled_pages = crawled_pages
        if status == IndexingStatus.INDEXED:
            item.indexed_at = datetime.now(timezone.utc)
        await self._db.flush()
        await self._db.refresh(item)
        return item

    async def remove_crawled_page(
        self, item: AgentKnowledge, url: str
    ) -> AgentKnowledge:
        """Remove one URL entry from crawled_pages list."""
        if item.crawled_pages:
            item.crawled_pages = [
                p for p in item.crawled_pages if p.get("url") != url
            ]
        await self._db.flush()
        await self._db.refresh(item)
        return item

    async def append_crawled_page(
        self, item: AgentKnowledge, page: dict
    ) -> AgentKnowledge:
        """Append a newly scraped page to crawled_pages list."""
        pages = list(item.crawled_pages or [])
        pages.append(page)
        item.crawled_pages = pages
        await self._db.flush()
        await self._db.refresh(item)
        return item

    async def delete(self, item: AgentKnowledge) -> None:
        await self._db.delete(item)
        await self._db.flush()
