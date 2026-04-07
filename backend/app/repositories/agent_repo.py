"""Agent repository — all database queries for the agents table."""

import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.enums import AgentStatus


class AgentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        name: str,
        description: str | None = None,
        system_prompt: str = "You are a helpful customer support assistant.",
        welcome_message: str | None = None,
        fallback_message: str | None = None,
        primary_color: str | None = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> Agent:
        agent = Agent(
            user_id=user_id,
            name=name,
            description=description,
            system_prompt=system_prompt,
            welcome_message=welcome_message,
            fallback_message=fallback_message,
            primary_color=primary_color,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        self._db.add(agent)
        await self._db.flush()
        await self._db.refresh(agent)
        return agent

    async def get_by_id(self, agent_id: uuid.UUID) -> Agent | None:
        result = await self._db.execute(select(Agent).where(Agent.id == agent_id))
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: uuid.UUID) -> list[Agent]:
        result = await self._db.execute(
            select(Agent).where(Agent.user_id == user_id).order_by(Agent.created_at.desc())
        )
        return list(result.scalars().all())

    async def count_by_user(self, user_id: uuid.UUID) -> int:
        result = await self._db.execute(
            select(func.count()).select_from(Agent).where(Agent.user_id == user_id)
        )
        return result.scalar_one()

    async def update(self, agent: Agent, **fields) -> Agent:
        from sqlalchemy import update as sql_update

        stmt = (
            sql_update(Agent)
            .where(Agent.id == agent.id)
            .values(**fields)
            .execution_options(synchronize_session="fetch")
        )
        await self._db.execute(stmt)
        result = await self._db.execute(select(Agent).where(Agent.id == agent.id))
        return result.scalar_one()

    async def delete(self, agent: Agent) -> None:
        await self._db.delete(agent)
        await self._db.flush()
