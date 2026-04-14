"""
Botlixio — Shared enums used across SQLAlchemy models.

All enums inherit from (str, enum.Enum) so they serialize to
their string values in JSON responses automatically.
"""

import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class AuthProvider(str, enum.Enum):
    LOCAL = "local"
    GOOGLE = "google"
    GITHUB = "github"
    APPLE = "apple"


class AgentStatus(str, enum.Enum):
    DRAFT = "draft"
    LIVE = "live"
    PAUSED = "paused"


class LLMProvider(str, enum.Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class SubscriptionPlan(str, enum.Enum):
    FREE = "free"
    STARTER = "starter"
    GROWTH = "growth"
    BUSINESS = "business"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"


class KnowledgeSourceType(str, enum.Enum):
    FILE = "file"
    URL = "url"
    TEXT = "text"


class WorkflowStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    DRAFT = "draft"


class ExecutionStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class IntegrationProvider(str, enum.Enum):
    TELEGRAM = "telegram"
    GMAIL = "gmail"
    SLACK = "slack"
    NOTION = "notion"


class ChannelType(str, enum.Enum):
    WIDGET = "widget"
    WHATSAPP = "whatsapp"
    DISCORD = "discord"
    SLACK = "slack"


class IndexingStatus(str, enum.Enum):
    PENDING    = "pending"     # added, not yet processed
    PROCESSING = "processing"  # ARQ job running
    INDEXED    = "indexed"     # chunks in Qdrant, ready
    FAILED     = "failed"      # error during processing
    STALE      = "stale"       # source changed, needs re-index


class AgentTone(str, enum.Enum):
    PROFESSIONAL = "professional"
    FRIENDLY     = "friendly"
    CASUAL       = "casual"
    EMPATHETIC   = "empathetic"
