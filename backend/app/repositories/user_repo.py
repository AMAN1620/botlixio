"""
Botlixio — User repository.

All database queries for the User model live here.
Services call this layer; never SQLAlchemy directly from service code.
"""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Data-access layer for the users table."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Return a User by primary key, or None."""
        result = await self._db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Return a User by email (case-insensitive), or None."""
        result = await self._db.execute(
            select(User).where(User.email == email.lower().strip())
        )
        return result.scalar_one_or_none()

    # ── Write ─────────────────────────────────────────────────────────────

    async def create(
        self,
        *,
        email: str,
        password_hash: str | None,
        full_name: str,
        auth_provider: str = "LOCAL",
        oauth_id: str | None = None,
        avatar_url: str | None = None,
        is_verified: bool = False,
        verification_token: str | None = None,
        verification_token_expires: datetime | None = None,
    ) -> User:
        """Insert a new User row and return the persisted object."""
        user = User(
            email=email.lower().strip(),
            password_hash=password_hash,
            full_name=full_name,
            auth_provider=auth_provider,
            oauth_id=oauth_id,
            avatar_url=avatar_url,
            is_verified=is_verified,
            verification_token=verification_token,
            verification_token_expires=verification_token_expires,
        )
        self._db.add(user)
        await self._db.flush()   # assign id without committing
        await self._db.refresh(user)
        return user

    async def update(self, user: User, **fields) -> User:
        """
        Apply arbitrary field updates to an existing User via explicit SQL UPDATE.

        Uses a direct UPDATE statement (not ORM change tracking) for reliability
        across all execution contexts, including async ASGI test paths.
        """
        from sqlalchemy import update as sql_update

        stmt = (
            sql_update(User)
            .where(User.id == user.id)
            .values(**fields)
            .execution_options(synchronize_session="fetch")
        )
        await self._db.execute(stmt)
        # Re-fetch to return the updated object
        result = await self._db.execute(select(User).where(User.id == user.id))
        return result.scalar_one()
