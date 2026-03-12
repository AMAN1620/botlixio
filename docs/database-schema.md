# Database Schema

Full SQLAlchemy 2.0 schema for the Botlixio platform. All models use PostgreSQL with UUID primary keys.

---

## Enums

```python
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
```

---

## Core Models

### User

```python
class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))  # None for OAuth-only
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(default=UserRole.USER)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_verified: Mapped[bool] = mapped_column(default=False)
    auth_provider: Mapped[AuthProvider] = mapped_column(default=AuthProvider.LOCAL)
    oauth_id: Mapped[str | None] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    verification_token: Mapped[str | None] = mapped_column(String(255))
    reset_token: Mapped[str | None] = mapped_column(String(255))
    reset_token_expires: Mapped[datetime | None]
    last_login_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    # Relationships
    agents: Mapped[list["Agent"]] = relationship(back_populates="user")
    subscription: Mapped["Subscription | None"] = relationship(back_populates="user")
    integrations: Mapped[list["UserIntegration"]] = relationship(back_populates="user")
    workflows: Mapped[list["Workflow"]] = relationship(back_populates="user")
```

---

### Agent

```python
class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    system_prompt: Mapped[str] = mapped_column(Text, default="You are a helpful assistant.")
    provider: Mapped[LLMProvider] = mapped_column(default=LLMProvider.OPENAI)
    model: Mapped[str] = mapped_column(String(100), default="gpt-4o-mini")
    temperature: Mapped[float] = mapped_column(default=0.7)
    max_tokens: Mapped[int] = mapped_column(default=1024)
    status: Mapped[AgentStatus] = mapped_column(default=AgentStatus.DRAFT)
    tools: Mapped[list] = mapped_column(JSONB, default=list)      # List of tool slugs
    channels: Mapped[list] = mapped_column(JSONB, default=list)    # List of channel configs
    welcome_message: Mapped[str | None] = mapped_column(Text)
    fallback_message: Mapped[str | None] = mapped_column(Text)
    primary_color: Mapped[str | None] = mapped_column(String(7))   # Hex color for widget
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    total_messages: Mapped[int] = mapped_column(default=0)
    total_sessions: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="agents")
    knowledge_items: Mapped[list["AgentKnowledge"]] = relationship(back_populates="agent")
    chat_sessions: Mapped[list["ChatSession"]] = relationship(back_populates="agent")
    leads: Mapped[list["Lead"]] = relationship(back_populates="agent")
```

---

### Subscription

```python
class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    plan: Mapped[SubscriptionPlan] = mapped_column(default=SubscriptionPlan.FREE)
    status: Mapped[SubscriptionStatus] = mapped_column(default=SubscriptionStatus.ACTIVE)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255))
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255))
    current_period_start: Mapped[datetime | None]
    current_period_end: Mapped[datetime | None]
    cancel_at_period_end: Mapped[bool] = mapped_column(default=False)

    # Usage tracking
    agents_used: Mapped[int] = mapped_column(default=0)
    messages_used: Mapped[int] = mapped_column(default=0)
    messages_reset_at: Mapped[datetime | None]   # Monthly reset

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="subscription")
```

---

### ChatSession + ChatMessage

```python
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id"), index=True)
    session_identifier: Mapped[str] = mapped_column(String(255), index=True)  # IP or user ID
    channel: Mapped[str] = mapped_column(String(50), default="widget")
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    message_count: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)
    last_message_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships
    agent: Mapped["Agent"] = relationship(back_populates="chat_sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="session", order_by="ChatMessage.created_at")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chat_sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))       # "user", "assistant", "system", "tool"
    content: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int | None]
    tool_calls: Mapped[list | None] = mapped_column(JSONB)
    tool_results: Mapped[list | None] = mapped_column(JSONB)
    response_time_ms: Mapped[int | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships
    session: Mapped["ChatSession"] = relationship(back_populates="messages")
```

---

### AgentKnowledge

```python
class AgentKnowledge(Base):
    __tablename__ = "agent_knowledge"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id"), index=True)
    source_type: Mapped[KnowledgeSourceType]
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)             # Extracted text
    raw_content: Mapped[str | None] = mapped_column(Text)  # Original URL or raw text
    file_name: Mapped[str | None] = mapped_column(String(255))
    file_size: Mapped[int | None]                           # Bytes
    chunk_count: Mapped[int] = mapped_column(default=1)
    char_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships
    agent: Mapped["Agent"] = relationship(back_populates="knowledge_items")
```

---

### Lead

```python
class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id"), index=True)
    session_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("chat_sessions.id"))
    name: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    company: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)
    source_channel: Mapped[str | None] = mapped_column(String(50))
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships
    agent: Mapped["Agent"] = relationship(back_populates="leads")
```

---

### Workflow + WorkflowStep + WorkflowExecution

```python
class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    trigger_type: Mapped[str] = mapped_column(String(100))   # "new_lead", "new_message", etc.
    trigger_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[WorkflowStatus] = mapped_column(default=WorkflowStatus.DRAFT)
    execution_count: Mapped[int] = mapped_column(default=0)
    last_executed_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="workflows")
    steps: Mapped[list["WorkflowStep"]] = relationship(back_populates="workflow", order_by="WorkflowStep.order")
    executions: Mapped[list["WorkflowExecution"]] = relationship(back_populates="workflow")

class WorkflowStep(Base):
    __tablename__ = "workflow_steps"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workflows.id"))
    order: Mapped[int]
    integration_provider: Mapped[str] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(100))
    config: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Relationships
    workflow: Mapped["Workflow"] = relationship(back_populates="steps")

class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workflows.id"))
    status: Mapped[ExecutionStatus] = mapped_column(default=ExecutionStatus.PENDING)
    trigger_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    results: Mapped[dict] = mapped_column(JSONB, default=dict)
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None]
    completed_at: Mapped[datetime | None]
    retry_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships
    workflow: Mapped["Workflow"] = relationship(back_populates="executions")
```

---

### UserIntegration

```python
class UserIntegration(Base):
    __tablename__ = "user_integrations"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    provider: Mapped[IntegrationProvider]
    credentials_encrypted: Mapped[str] = mapped_column(Text)   # Fernet-encrypted JSON
    is_active: Mapped[bool] = mapped_column(default=True)
    connected_at: Mapped[datetime] = mapped_column(server_default=func.now())
    last_used_at: Mapped[datetime | None]

    # Relationships
    user: Mapped["User"] = relationship(back_populates="integrations")

    @@unique = UniqueConstraint("user_id", "provider")
```

---

### Admin-Managed Config Tables

```python
class PlatformAPIKey(Base):
    __tablename__ = "platform_api_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(100))        # "openai", "anthropic", etc.
    key_name: Mapped[str] = mapped_column(String(255))
    encrypted_key: Mapped[str] = mapped_column(Text)          # Fernet-encrypted
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

class ToolConfig(Base):
    __tablename__ = "tool_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(100), unique=True)  # "web_search", "weather"
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True)
    config: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

class ChannelConfig(Base):
    __tablename__ = "channel_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(100), unique=True)  # "widget", "whatsapp"
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True)
    config: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

class PricingConfig(Base):
    __tablename__ = "pricing_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    plan: Mapped[SubscriptionPlan]
    name: Mapped[str] = mapped_column(String(100))
    price_monthly: Mapped[int] = mapped_column(default=0)       # In cents
    price_yearly: Mapped[int] = mapped_column(default=0)         # In cents
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
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
```

---

## Relationships Summary

```
User          → Agent[] (1:many)
User          → Subscription (1:1)
User          → UserIntegration[] (1:many)
User          → Workflow[] (1:many)
Agent         → AgentKnowledge[] (1:many)
Agent         → ChatSession[] (1:many)
Agent         → Lead[] (1:many)
ChatSession   → ChatMessage[] (1:many)
Workflow      → WorkflowStep[] (1:many, ordered)
Workflow      → WorkflowExecution[] (1:many)
```

---

## Indexes

```python
# User
Index("ix_users_email", "email", unique=True)

# Agent
Index("ix_agents_user_id", "user_id")
Index("ix_agents_status", "status")

# ChatSession
Index("ix_chat_sessions_agent_id", "agent_id")
Index("ix_chat_sessions_session_identifier", "session_identifier")

# ChatMessage
Index("ix_chat_messages_session_id", "session_id")

# AgentKnowledge
Index("ix_agent_knowledge_agent_id", "agent_id")

# Lead
Index("ix_leads_agent_id", "agent_id")

# Subscription
Index("ix_subscriptions_user_id", "user_id", unique=True)

# Workflow
Index("ix_workflows_user_id", "user_id")
```
