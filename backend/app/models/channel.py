"""Admin-managed channel config and pricing tables."""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import SubscriptionPlan


class ChannelConfig(Base):
    __tablename__ = "channel_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True)
    config: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class PricingConfig(Base):
    __tablename__ = "pricing_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    plan: Mapped[SubscriptionPlan] = mapped_column()
    name: Mapped[str] = mapped_column(String(100))
    price_monthly: Mapped[int] = mapped_column(default=0)
    price_yearly: Mapped[int] = mapped_column(default=0)
    max_agents: Mapped[int] = mapped_column(default=1)
    max_messages_per_month: Mapped[int] = mapped_column(default=100)
    max_knowledge_items: Mapped[int] = mapped_column(default=5)
    max_workflows: Mapped[int] = mapped_column(default=0)
    allowed_models: Mapped[list] = mapped_column(JSONB, default=list)
    allowed_tools: Mapped[list] = mapped_column(JSONB, default=list)
    features: Mapped[dict] = mapped_column(JSONB, default=dict)
    stripe_price_id_monthly: Mapped[str | None] = mapped_column(String(255))
    stripe_price_id_yearly: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)
    sort_order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
