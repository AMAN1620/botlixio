"""
Botlixio — SQLAlchemy model registry.

Import all models here so that ``Base.metadata`` includes every table
when Alembic runs ``--autogenerate``.
"""

from app.models.agent import Agent
from app.models.channel import ChannelConfig, PricingConfig
from app.models.chat_session import ChatMessage, ChatSession
from app.models.enums import (
    AgentStatus,
    AuthProvider,
    ChannelType,
    ExecutionStatus,
    IntegrationProvider,
    KnowledgeSourceType,
    LLMProvider,
    SubscriptionPlan,
    SubscriptionStatus,
    UserRole,
    WorkflowStatus,
)
from app.models.integration import UserIntegration
from app.models.knowledge import AgentKnowledge
from app.models.lead import Lead
from app.models.subscription import Subscription
from app.models.tool import PlatformAPIKey, ToolConfig
from app.models.user import User
from app.models.workflow import Workflow, WorkflowExecution, WorkflowStep

__all__ = [
    # Core models
    "User",
    "Agent",
    "Subscription",
    "ChatSession",
    "ChatMessage",
    "AgentKnowledge",
    "Lead",
    "Workflow",
    "WorkflowStep",
    "WorkflowExecution",
    "UserIntegration",
    # Admin-config models
    "PlatformAPIKey",
    "ToolConfig",
    "ChannelConfig",
    "PricingConfig",
    # Enums
    "UserRole",
    "AuthProvider",
    "AgentStatus",
    "LLMProvider",
    "SubscriptionPlan",
    "SubscriptionStatus",
    "KnowledgeSourceType",
    "WorkflowStatus",
    "ExecutionStatus",
    "IntegrationProvider",
    "ChannelType",
]
