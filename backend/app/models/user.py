"""User model — email, role, auth provider, verification."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AuthProvider, UserRole


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(default=UserRole.USER)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_verified: Mapped[bool] = mapped_column(default=False)
    auth_provider: Mapped[AuthProvider] = mapped_column(default=AuthProvider.LOCAL)
    oauth_id: Mapped[str | None] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    verification_token: Mapped[str | None] = mapped_column(String(255))
    # Required to enforce 24h expiry on email verification tokens.
    # Set at registration time: datetime.utcnow() + timedelta(hours=24)
    verification_token_expires: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reset_token: Mapped[str | None] = mapped_column(String(255))
    reset_token_expires: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Stores SHA-256 hash of the latest valid refresh token.
    # On refresh: incoming token hash must match this field.
    # Set to None on logout. Updated on every refresh.
    refresh_token_hash: Mapped[str | None] = mapped_column(String(64))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    agents: Mapped[list["Agent"]] = relationship(back_populates="user")  # noqa: F821
    subscription: Mapped["Subscription | None"] = relationship(  # noqa: F821
        back_populates="user"
    )
    integrations: Mapped[list["UserIntegration"]] = relationship(  # noqa: F821
        back_populates="user"
    )
    workflows: Mapped[list["Workflow"]] = relationship(  # noqa: F821
        back_populates="user"
    )
