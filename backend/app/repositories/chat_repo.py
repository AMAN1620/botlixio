"""Chat repository — ChatSession and ChatMessage CRUD."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat_session import ChatMessage, ChatSession


class ChatRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_or_create_session(
        self, *, agent_id: uuid.UUID, session_identifier: str
    ) -> ChatSession:
        result = await self._db.execute(
            select(ChatSession).where(
                ChatSession.agent_id == agent_id,
                ChatSession.session_identifier == session_identifier,
            )
        )
        session = result.scalar_one_or_none()
        if session is None:
            session = ChatSession(
                agent_id=agent_id,
                session_identifier=session_identifier,
            )
            self._db.add(session)
            await self._db.flush()
            await self._db.refresh(session)
        return session

    async def get_recent_messages(
        self, *, session_id: uuid.UUID, limit: int = 10
    ) -> list[ChatMessage]:
        result = await self._db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        messages = list(result.scalars().all())
        return list(reversed(messages))

    async def add_message(
        self,
        *,
        session_id: uuid.UUID,
        role: str,
        content: str,
        response_time_ms: int | None = None,
    ) -> ChatMessage:
        msg = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            response_time_ms=response_time_ms,
        )
        self._db.add(msg)
        await self._db.flush()

        # Update session counters
        from sqlalchemy import update as sql_update
        await self._db.execute(
            sql_update(ChatSession)
            .where(ChatSession.id == session_id)
            .values(
                message_count=ChatSession.message_count + 1,
                last_message_at=datetime.now(timezone.utc),
            )
        )
        return msg
