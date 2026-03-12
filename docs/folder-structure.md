# Folder Structure

Complete directory layout for the Botlixio v2 monorepo.

```
botlixio-v2/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                        # FastAPI app factory, middleware, router includes
│   │   │
│   │   ├── core/                          # Cross-cutting concerns
│   │   │   ├── __init__.py
│   │   │   ├── config.py                  # Pydantic Settings (env loading, validation)
│   │   │   ├── database.py                # Async engine, session maker, Base, get_db dependency
│   │   │   └── security.py                # JWT creation/verification, password hashing
│   │   │
│   │   ├── models/                        # SQLAlchemy 2.0 models (Mapped[] style)
│   │   │   ├── __init__.py
│   │   │   ├── user.py                    # User model (email, role, is_active, oauth)
│   │   │   ├── agent.py                   # Agent model (name, provider, model, prompt, tools)
│   │   │   ├── subscription.py            # Subscription model (plan, stripe_id, limits)
│   │   │   ├── chat_session.py            # ChatSession + ChatMessage models
│   │   │   ├── knowledge.py               # AgentKnowledge model (file/url/text content)
│   │   │   ├── lead.py                    # Lead model (name, email, phone, agent_id)
│   │   │   ├── workflow.py                # Workflow + WorkflowStep + WorkflowExecution
│   │   │   ├── integration.py             # UserIntegration model (provider, encrypted creds)
│   │   │   ├── tool.py                    # ToolConfig model (admin-managed tool registry)
│   │   │   └── channel.py                 # ChannelConfig model (admin-managed channels)
│   │   │
│   │   ├── schemas/                       # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                    # Register, Login, Token, UserResponse
│   │   │   ├── agent.py                   # AgentCreate, AgentUpdate, AgentResponse
│   │   │   ├── chat.py                    # ChatRequest, ChatResponse, SessionResponse
│   │   │   ├── knowledge.py               # KnowledgeCreate, KnowledgeResponse
│   │   │   ├── billing.py                 # PlanResponse, SubscriptionResponse, CheckoutRequest
│   │   │   ├── workflow.py                # WorkflowCreate, WorkflowResponse, ExecutionResponse
│   │   │   ├── admin.py                   # AdminUserResponse, APIKeyCreate, AnalyticsResponse
│   │   │   └── webhook.py                 # WhatsAppMessage, DiscordMessage, SlackMessage
│   │   │
│   │   ├── repositories/                  # Data access layer (SQL queries only)
│   │   │   ├── __init__.py
│   │   │   ├── base.py                    # BaseRepository with common CRUD
│   │   │   ├── user_repo.py               # User queries
│   │   │   ├── agent_repo.py              # Agent queries
│   │   │   ├── chat_repo.py               # ChatSession + ChatMessage queries
│   │   │   ├── knowledge_repo.py          # Knowledge queries
│   │   │   ├── subscription_repo.py       # Subscription queries
│   │   │   ├── lead_repo.py               # Lead queries
│   │   │   ├── workflow_repo.py           # Workflow queries
│   │   │   └── admin_repo.py              # Admin aggregate queries
│   │   │
│   │   ├── services/                      # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py            # Register, login, verify email, reset password
│   │   │   ├── agent_service.py           # Agent CRUD, deploy/pause, plan limit checks
│   │   │   ├── chat_engine.py             # Full LLM pipeline: session → context → LLM → save
│   │   │   ├── llm_client.py              # LiteLLM wrapper (testable, mockable)
│   │   │   ├── knowledge_service.py       # File parsing, URL scraping, text storage
│   │   │   ├── document_parser.py         # PDF, TXT, CSV, DOCX text extraction
│   │   │   ├── billing_service.py         # Stripe integration, plan management
│   │   │   ├── email_service.py           # Verification & reset emails via Resend
│   │   │   ├── workflow_engine.py         # Sequential step execution engine
│   │   │   │
│   │   │   ├── tools/                     # Tool system (LLM function-calling)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py               # Abstract tool interface
│   │   │   │   ├── registry.py            # Tool registration & dispatch
│   │   │   │   ├── web_search.py          # DuckDuckGo search + webpage fetching
│   │   │   │   ├── weather.py             # Weather lookup
│   │   │   │   └── lead_catcher.py        # Lead extraction from conversations
│   │   │   │
│   │   │   └── integrations/              # Third-party integrations
│   │   │       ├── __init__.py
│   │   │       ├── base.py               # Abstract integration interface
│   │   │       ├── registry.py            # Integration registry & dispatch
│   │   │       ├── telegram.py            # Telegram Bot API
│   │   │       ├── gmail.py               # Gmail API
│   │   │       ├── slack_integration.py   # Slack API
│   │   │       └── notion.py              # Notion API
│   │   │
│   │   ├── api/                           # Route handlers (thin controllers)
│   │   │   ├── __init__.py
│   │   │   └── v1/                        # Versioned API
│   │   │       ├── __init__.py
│   │   │       ├── auth.py                # Register, login, verify, reset, OAuth
│   │   │       ├── agents.py              # Agent CRUD, deploy, pause
│   │   │       ├── chat.py                # Chat endpoints (authenticated + public widget)
│   │   │       ├── knowledge.py           # File upload, URL scrape, text add, list, delete
│   │   │       ├── billing.py             # Plans, checkout, webhook, cancel
│   │   │       ├── workflows.py           # Workflow CRUD + execution
│   │   │       ├── integrations.py        # Connect, disconnect, list integrations
│   │   │       ├── admin.py               # User mgmt, API keys, analytics, pricing
│   │   │       ├── webhooks.py            # WhatsApp, Discord, Slack incoming
│   │   │       └── profile.py             # User profile, settings
│   │   │
│   │   └── utils/                         # Shared utilities
│   │       ├── __init__.py
│   │       ├── encryption.py              # Fernet encrypt/decrypt for credentials
│   │       └── email.py                   # Email template helpers
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py                    # Shared fixtures (db, client, auth, factories)
│   │   ├── unit/
│   │   │   ├── test_security.py
│   │   │   ├── test_auth_service.py
│   │   │   ├── test_agent_service.py
│   │   │   ├── test_chat_engine.py
│   │   │   ├── test_llm_client.py
│   │   │   ├── test_tool_registry.py
│   │   │   ├── test_web_search.py
│   │   │   ├── test_lead_catcher.py
│   │   │   ├── test_document_parser.py
│   │   │   ├── test_knowledge_service.py
│   │   │   ├── test_billing_service.py
│   │   │   ├── test_workflow_engine.py
│   │   │   └── test_encryption.py
│   │   └── integration/
│   │       ├── test_auth_api.py
│   │       ├── test_agents_api.py
│   │       ├── test_chat_api.py
│   │       ├── test_knowledge_api.py
│   │       ├── test_billing_api.py
│   │       ├── test_widget_api.py
│   │       ├── test_workflows_api.py
│   │       ├── test_admin_api.py
│   │       └── test_webhooks.py
│   │
│   ├── alembic/                           # Database migrations
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   ├── alembic.ini
│   ├── pyproject.toml                     # Modern Python packaging
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/                              # Next.js 16 + React 19 + TypeScript
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx                 # Root layout (fonts, providers)
│   │   │   ├── page.tsx                   # Landing page
│   │   │   ├── globals.css
│   │   │   │
│   │   │   ├── (auth)/                    # Auth pages (no sidebar)
│   │   │   │   ├── layout.tsx             # Centered card layout
│   │   │   │   ├── login/page.tsx
│   │   │   │   ├── register/page.tsx
│   │   │   │   ├── verify-email/page.tsx
│   │   │   │   └── forgot-password/page.tsx
│   │   │   │
│   │   │   └── (dashboard)/              # Protected pages (with sidebar)
│   │   │       ├── layout.tsx             # Sidebar + Topbar shell
│   │   │       ├── dashboard/page.tsx     # Stats cards, recent agents
│   │   │       ├── agents/
│   │   │       │   ├── page.tsx           # Agent list with status toggles
│   │   │       │   ├── new/page.tsx       # Agent creation wizard
│   │   │       │   └── [id]/
│   │   │       │       ├── page.tsx       # Agent detail/edit
│   │   │       │       ├── knowledge/page.tsx
│   │   │       │       ├── test/page.tsx  # Test chat component
│   │   │       │       └── leads/page.tsx
│   │   │       ├── billing/page.tsx       # Plan comparison + upgrade
│   │   │       ├── workflows/
│   │   │       │   ├── page.tsx
│   │   │       │   └── [id]/page.tsx
│   │   │       ├── integrations/page.tsx
│   │   │       ├── settings/page.tsx      # Profile settings
│   │   │       └── admin/                 # Admin-only
│   │   │           ├── page.tsx           # Admin dashboard
│   │   │           ├── users/page.tsx
│   │   │           ├── api-keys/page.tsx
│   │   │           ├── pricing/page.tsx
│   │   │           └── analytics/page.tsx
│   │   │
│   │   ├── components/
│   │   │   ├── ui/                        # shadcn/ui primitives
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── Topbar.tsx
│   │   │   │   └── LandingNav.tsx
│   │   │   └── shared/
│   │   │       ├── ChatWidget.tsx         # Embeddable chat component
│   │   │       ├── AgentCard.tsx
│   │   │       └── PlanCard.tsx
│   │   │
│   │   ├── hooks/
│   │   │   ├── use-agents.ts
│   │   │   ├── use-auth.ts
│   │   │   └── use-billing.ts
│   │   │
│   │   ├── lib/
│   │   │   └── api.ts                     # Axios instance with auth interceptors
│   │   │
│   │   └── types/
│   │       └── index.ts                   # Shared TypeScript interfaces
│   │
│   ├── tests/                             # Frontend tests (Vitest + RTL)
│   ├── package.json
│   └── Dockerfile
│
├── whatsapp-bridge/                       # Node.js Baileys service
│   ├── src/
│   │   ├── index.js                       # Express server + Baileys client
│   │   └── qr-server.js                   # QR code SSE streaming
│   ├── package.json
│   └── Dockerfile
│
├── docker/
│   ├── docker-compose.yml                 # Dev: PostgreSQL + Redis
│   ├── docker-compose.prod.yml            # Production: all services
│   └── nginx/
│       └── nginx.conf                     # Reverse proxy + SSL + WebSocket
│
├── docs/                                  # This documentation
│   ├── README.md
│   ├── tech-stack.md
│   ├── folder-structure.md
│   ├── database-schema.md
│   ├── business-rules.md
│   ├── api-routes.md
│   ├── implementation-phases.md
│   └── features/
│       ├── 01-authentication.md
│       ├── 02-agent-builder.md
│       ├── 03-chat-engine.md
│       ├── 04-tool-system.md
│       ├── 05-knowledge-base.md
│       ├── 06-widget.md
│       ├── 07-billing.md
│       ├── 08-integrations-workflows.md
│       ├── 09-admin-panel.md
│       └── 10-multi-channel.md
│
├── .agents/                               # Agent workflow definitions
│   └── workflows/
│       ├── create-spec.md
│       ├── docs-sync.md
│       ├── execute-next.md
│       ├── plan-check.md
│       ├── spec-test-case-analyzer.md
│       ├── spec-to-test-case.md
│       ├── test-case-to-test.md
│       ├── test-report.md
│       └── where-am-i.md
│
├── .env.example
├── .gitignore
└── README.md
```

---

## Key Conventions

### Backend Architecture
- **Routes** (`api/v1/*.py`): Thin controllers — validate input, call service, return response
- **Services** (`services/*.py`): All business logic — plan checks, orchestration, validation
- **Repositories** (`repositories/*.py`): Data access only — SQL queries, no business logic
- **Models** (`models/*.py`): SQLAlchemy 2.0 `Mapped[]` + `mapped_column()` style

### API Response Shape
```python
# Success (list)
{"data": [...], "total": 100, "page": 1, "page_size": 20}

# Success (single)
{"data": { ... }}

# Error
{"detail": "Error message"}
# or
{"detail": [{"field": "email", "message": "Required"}]}
```

### File Naming
- Python: `snake_case.py`
- TypeScript components: `PascalCase.tsx`
- TypeScript utilities: `camelCase.ts`
- Config files: `kebab-case.ts`
