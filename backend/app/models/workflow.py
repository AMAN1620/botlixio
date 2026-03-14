"""Workflow + WorkflowStep + WorkflowExecution models."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ExecutionStatus, WorkflowStatus


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    trigger_type: Mapped[str] = mapped_column(String(100))
    trigger_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[WorkflowStatus] = mapped_column(default=WorkflowStatus.DRAFT)
    execution_count: Mapped[int] = mapped_column(default=0)
    last_executed_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="workflows")  # noqa: F821
    steps: Mapped[list["WorkflowStep"]] = relationship(
        back_populates="workflow", order_by="WorkflowStep.order"
    )
    executions: Mapped[list["WorkflowExecution"]] = relationship(
        back_populates="workflow"
    )


class WorkflowStep(Base):
    __tablename__ = "workflow_steps"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workflow_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workflows.id"))
    order: Mapped[int] = mapped_column()
    integration_provider: Mapped[str] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(100))
    config: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Relationships
    workflow: Mapped["Workflow"] = relationship(back_populates="steps")


class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workflow_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workflows.id"))
    status: Mapped[ExecutionStatus] = mapped_column(
        default=ExecutionStatus.PENDING
    )
    trigger_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    results: Mapped[dict] = mapped_column(JSONB, default=dict)
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column()
    completed_at: Mapped[datetime | None] = mapped_column()
    retry_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships
    workflow: Mapped["Workflow"] = relationship(back_populates="executions")
