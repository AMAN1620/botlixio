"""Knowledge repository — CRUD for agent_knowledge table."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import AgentKnowledge
from app.models.enums import KnowledgeSourceType


class KnowledgeRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self,
        *,
        agent_id: uuid.UUID,
        source_type: KnowledgeSourceType,
        title: str,
        content: str,
        file_name: str | None = None,
        file_size: int | None = None,
        chunk_count: int = 1,
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

    async def delete(self, item: AgentKnowledge) -> None:
        await self._db.delete(item)
        await self._db.flush()
