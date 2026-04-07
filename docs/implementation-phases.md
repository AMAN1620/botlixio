# Implementation Phases

Phased build plan for the Botlixio. Each phase builds on completed previous phases. Follow TDD for all logic.

> **Active sprint** → See [customer-support-bot-plan.md](customer-support-bot-plan.md) for the focused 6-step plan to ship the Customer Support solution end-to-end (Docker auth verification → Agent CRUD → Crawl4AI knowledge ingestion → RAG chat engine → JS embed widget → Dashboard UI).

---

## Phase 0: Project Scaffolding & DevOps Foundation

**Goal**: Set up the monorepo, Docker Compose, and testing infrastructure.

- [x] Create monorepo structure (`backend/`, `frontend/`, `docker/`, `docs/`)
- [x] Backend: `pyproject.toml`, `app/__init__.py`, `app/main.py` (empty FastAPI app)
- [x] Backend: `pytest` + `pytest-asyncio` configured in `pyproject.toml`
- [x] Backend: `tests/conftest.py` with basic fixtures
- [x] Docker: `docker-compose.yml` for PostgreSQL + Redis (dev)
- [x] Backend: `.env.example` with all environment variables
- [x] Frontend: `npx create-next-app` with TypeScript + Tailwind CSS
- [x] Git: `.gitignore`, initial commit

**Done when**: `pytest` runs with 0 tests found, `docker compose up` starts PostgreSQL + Redis, `npm run dev` serves Next.js.

---

## Phase 1: Configuration & Database Foundation

**Goal**: Settings, database connection, and Alembic migrations.

- [x] `app/core/config.py` — Pydantic Settings (loads `.env`, validates all required vars)
- [x] `app/core/database.py` — Async engine, session maker, `Base`, `get_db` dependency
- [x] Alembic initialization: `alembic init`, `alembic.ini`, `env.py` using async engine
- [x] All SQLAlchemy models (`app/models/*.py`) — all enums and tables from `database-schema.md`
- [x] Initial Alembic migration: `alembic revision --autogenerate`
- [x] Test: config loads from `.env`, validates missing vars, type coercion
- [x] Test: database session creation and teardown

**Done when**: `alembic upgrade head` creates all tables, config tests pass.

---

## Phase 2: Authentication — Core

**Goal**: Register, login, JWT, and password hashing.

- [x] `app/core/security.py` — `hash_password`, `verify_password`, `create_access_token`, `create_refresh_token`, `decode_token`
- [x] `app/schemas/auth.py` — `RegisterRequest`, `LoginRequest`, `TokenResponse`, `UserResponse`
- [x] `app/repositories/user_repo.py` — `create_user`, `get_by_email`, `get_by_id`
- [x] `app/services/auth_service.py` — `register`, `login`, `get_current_user` (and accelerated `refresh_tokens`)
- [x] `app/api/v1/auth.py` — `POST /register`, `POST /login`, `GET /me` (and accelerated `POST /refresh`)
- [x] `app/api/deps.py` — `get_current_user` dependency (extracts JWT, returns User)
- [x] Test: security functions (hash, verify, JWT create/decode)
- [x] Test: auth service (register, login, duplicate email, accelerated refresh)
- [x] Test: auth API endpoints (register, login, me, unauthorized, accelerated refresh)

**Done when**: User can register, login, and access protected endpoints via JWT.

---

## Phase 3: Authentication — Extended

**Goal**: Email verification, password reset, refresh tokens, OAuth.

- [x] `app/services/email_service.py` — Resend integration (verification + reset emails)
- [x] `app/api/v1/auth.py` additions — `POST /verify-email`, `POST /forgot-password`, `POST /reset-password`
- [x] Auth service additions: `verify_email`, `forgot_password`, `reset_password`
- [x] OAuth: `GET /auth/google`, `GET /auth/google/callback`
- [x] Test: email verification flow
- [x] Test: password reset flow (valid token, expired token, invalid token)
- [x] Test: OAuth login (mock external provider)

**Done when**: Full auth lifecycle works — register, verify, login, refresh, forgot/reset password, Google OAuth.

---

## Phase 4: Agent Builder — CRUD

**Goal**: Create, read, update, delete AI agents with plan-based limits.

- [ ] `app/schemas/agent.py` — `AgentCreate`, `AgentUpdate`, `AgentResponse`
- [ ] `app/repositories/agent_repo.py` — Agent CRUD queries
- [ ] `app/services/agent_service.py` — Agent CRUD with plan limit checks
- [ ] `app/api/v1/agents.py` — All agent endpoints
- [ ] `app/repositories/subscription_repo.py` — subscription queries for limit checks
- [ ] Test: agent schema validation
- [ ] Test: agent service (create with limit, update, soft-delete)
- [ ] Test: agent API endpoints (CRUD, unauthorized, ownership)

**Done when**: User can create agents up to plan limit, update config, deploy/pause.

---

## Phase 5: Knowledge Base — Upload & Parse

**Goal**: Upload files, scrape URLs, add text — all stored and associated with agents.

- [ ] `app/services/document_parser.py` — PDF, TXT, CSV, DOCX text extraction
- [ ] `app/schemas/knowledge.py` — `KnowledgeCreate`, `KnowledgeResponse`
- [ ] `app/repositories/knowledge_repo.py` — Knowledge CRUD
- [ ] `app/services/knowledge_service.py` — File parsing, URL scraping, text storage with plan limits
- [ ] `app/api/v1/knowledge.py` — Upload, scrape, add text, list, delete endpoints
- [ ] Test: document parser (PDF, TXT, CSV, DOCX)
- [ ] Test: knowledge service (add, limit check, delete)
- [ ] Test: knowledge API endpoints (upload, scrape, list)

**Done when**: Agent owner can upload files, scrape URLs, add text; content is extracted and stored.

---

## Phase 6: Chat Engine — Core LLM Pipeline

**Goal**: Send messages, get LLM responses, with session management and history.

- [ ] `app/services/llm_client.py` — LiteLLM wrapper (async, testable)
- [ ] `app/schemas/chat.py` — `ChatRequest`, `ChatResponse`, `SessionResponse`
- [ ] `app/repositories/chat_repo.py` — ChatSession + ChatMessage queries
- [ ] `app/services/chat_engine.py` — Full pipeline: session → history → knowledge → LLM → save
- [ ] `app/api/v1/chat.py` — Chat endpoints (authenticated)
- [ ] Test: LLM client (mock LiteLLM responses)
- [ ] Test: chat engine (session creation, history loading, knowledge injection, message saving)
- [ ] Test: chat API (send message, list sessions, get history)

**Done when**: User can chat with their agent via API; history is saved; knowledge context is injected.

---

## Phase 7: Tool System — Function Calling

**Goal**: LLM can call tools (web search, weather, lead catcher) during conversations.

- [ ] `app/services/tools/base.py` — Abstract Tool interface
- [ ] `app/services/tools/registry.py` — Tool registration and dispatch
- [ ] `app/services/tools/web_search.py` — DuckDuckGo search + page fetch
- [ ] `app/services/tools/weather.py` — Weather API integration
- [ ] `app/services/tools/lead_catcher.py` — Lead extraction from conversations
- [ ] `app/repositories/lead_repo.py` — Lead CRUD
- [ ] Chat engine integration: tool calling loop, max iterations, error handling
- [ ] Test: tool registry (register, dispatch, unknown tool)
- [ ] Test: web search tool (mock HTTP)
- [ ] Test: lead catcher (extract, save, no lead)
- [ ] Test: chat engine tool loop (mock tools, max iterations)

**Done when**: LLM can call tools during chat; leads are captured; tool errors handled gracefully.

---

## Phase 8: Widget — Public Chat Endpoint

**Goal**: Public endpoints for embeddable chat widget with rate limiting.

- [ ] `app/api/v1/chat.py` additions — Widget endpoints (GET status, POST chat, GET session)
- [ ] Rate limiting with SlowAPI for public endpoints
- [ ] CORS configuration for widget embedding
- [ ] IP-based session management
- [ ] Test: widget endpoints (rate limiting, CORS headers)
- [ ] Test: widget chat flow (session creation, message limits)

**Done when**: Widget endpoints work without auth, are rate-limited, and CORS-enabled.

---

## Phase 9: Billing & Subscriptions

**Goal**: Stripe integration with checkout, webhook handling, and plan enforcement.

- [ ] `app/schemas/billing.py` — `PlanResponse`, `SubscriptionResponse`, `CheckoutRequest`
- [ ] `app/services/billing_service.py` — Stripe checkout, webhook handling, plan management
- [ ] `app/api/v1/billing.py` — Plans, checkout, portal, cancel, webhook
- [ ] `app/models/subscription.py` — ensure monthly message reset logic
- [ ] Plan limit enforcement integrated into agent/chat/knowledge/workflow services
- [ ] Test: billing service (checkout creation, webhook handling, plan transition)
- [ ] Test: billing API endpoints
- [ ] Test: plan limit enforcement (create agent over limit, send message over limit)

**Done when**: User can subscribe, upgrade, downgrade, cancel via Stripe; limits enforced.

---

## Phase 10: Integrations & Workflows

**Goal**: OAuth-based third-party integrations + sequential workflow engine.

- [ ] `app/utils/encryption.py` — Fernet encrypt/decrypt
- [ ] `app/services/integrations/base.py` — Abstract integration interface
- [ ] `app/services/integrations/registry.py` — Integration registry
- [ ] `app/services/integrations/{provider}.py` — Telegram, Gmail, Slack, Notion
- [ ] `app/schemas/workflow.py` — Workflow schemas
- [ ] `app/repositories/workflow_repo.py` — Workflow CRUD
- [ ] `app/services/workflow_engine.py` — Sequential step execution
- [ ] `app/api/v1/workflows.py` — Workflow CRUD + execution endpoints
- [ ] `app/api/v1/integrations.py` — Connect, disconnect endpoints
- [ ] Test: encryption (encrypt, decrypt, invalid key)
- [ ] Test: integration registry + mock providers
- [ ] Test: workflow engine (execute steps, handle failures, retries)
- [ ] Test: workflow API endpoints

**Done when**: Users can connect integrations and create workflows that execute actions automatically.

---

## Phase 11: Admin Panel — Backend

**Goal**: Admin endpoints for user management, API keys, analytics, pricing config.

- [ ] `app/schemas/admin.py` — Admin schemas
- [ ] `app/repositories/admin_repo.py` — Admin aggregate queries
- [ ] `app/api/v1/admin.py` — All admin endpoints
- [ ] Admin middleware: verify `role == ADMIN` on all admin routes
- [ ] Test: admin API endpoints (user management, API keys, analytics)
- [ ] Test: admin authorization (non-admin blocked)

**Done when**: Admin can manage users, API keys, pricing, and view analytics.

---

## Phase 12: Multi-Channel — WhatsApp, Discord, Slack

**Goal**: Receive and respond to messages from external channels.

- [ ] `app/api/v1/webhooks.py` — Webhook handlers for each channel
- [ ] WhatsApp Bridge: Node.js Baileys service with QR auth
- [ ] Discord bot setup with message webhook
- [ ] Slack app setup with events subscription
- [ ] Message normalization → chat engine → response routing
- [ ] Test: webhook handlers (valid/invalid payload, message routing)
- [ ] Test: message normalization for each channel

**Done when**: Messages from WhatsApp/Discord/Slack are processed and responses sent back.

---

## Phase 13: Frontend — Auth & Dashboard

**Goal**: Login/register pages, dashboard shell, and basic navigation.

- [ ] Auth pages: Login, Register, Verify Email, Forgot Password
- [ ] Dashboard layout: Sidebar, Topbar, route structure
- [ ] Dashboard page: Overview stats cards
- [ ] Protected route middleware (check JWT, redirect to login)
- [ ] Axios instance with auth interceptors
- [ ] TanStack Query provider

**Done when**: Users can register, login, see dashboard with real data from backend API.

---

## Phase 14: Frontend — Agent Builder & Chat

**Goal**: Agent creation wizard, agent list, test chat, knowledge management.

- [ ] Agent list page with status toggles
- [ ] Agent creation wizard (multi-step form)
- [ ] Agent detail/edit page
- [ ] Knowledge management page (upload, scrape, list, delete)
- [ ] Test chat component
- [ ] Leads page with export

**Done when**: Full agent builder workflow works end-to-end in the browser.

---

## Phase 15: Frontend — Billing, Workflows, Admin

**Goal**: Billing page, workflow builder, admin panel, settings.

- [ ] Billing page: Plan comparison cards, Stripe checkout integration
- [ ] Workflow builder page: Create, edit, view executions
- [ ] Integrations page: Connect/disconnect with status
- [ ] Admin pages: Users, API keys, Pricing, Analytics
- [ ] Settings page: Profile, password change, BYOK key

**Done when**: All dashboard pages are functional and connected to backend APIs.

---

## Phase 16: Production Deploy & Polish

**Goal**: Docker production build, SSL, performance, monitoring.

- [ ] Multi-stage Dockerfiles for backend, frontend, WhatsApp bridge
- [ ] `docker-compose.prod.yml` with all services
- [ ] Nginx reverse proxy with SSL (Certbot)
- [ ] Environment variable documentation for production
- [ ] Health check endpoints for each service
- [ ] Logging configuration
- [ ] Error tracking integration (Sentry or equivalent)
- [ ] Performance review and optimization

**Done when**: Platform is running in production with SSL, monitoring, and error tracking.
