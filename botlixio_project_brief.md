# Botlixio v2 — Project Brief for New Sessions

> **Copy-paste this into any new conversation to give full context for building from scratch.**

---

## 🎯 What We're Building

**Botlixio** is a full-stack **AI Agent Builder SaaS platform** — think of it as a white-label "build your own ChatGPT bot" product. Users sign up, create custom AI agents (choosing LLM provider, model, system prompt, tools), upload knowledge bases for RAG, and deploy those agents across multiple channels (website chat widget, WhatsApp, Discord, Slack).

It's a **rebuild** of an existing working project. The original code works but is messy — giant route files mixing business logic with data access, no tests, no database migrations, and no clean separation of concerns. We're rebuilding it from scratch with **clean architecture** and **Test-Driven Development (TDD)**.

---

## 🏗️ Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Backend** | FastAPI + Python 3.12 | Async, modern, great for APIs |
| **Frontend** | Next.js + React + TypeScript + Tailwind CSS | App Router, server/client components |
| **Database** | PostgreSQL 16 (via SQLAlchemy 2.0 async) | Robust, JSONB support |
| **Cache** | Redis 7 | Rate limiting, session cache |
| **AI/LLM** | LiteLLM | Single interface for OpenAI, Anthropic, Google |
| **Auth** | JWT (python-jose) + bcrypt | Access + refresh tokens |
| **Payments** | Stripe | Subscriptions, checkout, webhooks |
| **Email** | Resend | Verification, password reset |
| **WhatsApp** | Baileys (Node.js bridge) | QR-pairing, message relay |
| **Infra** | Docker Compose + Nginx + Certbot | Containerization, reverse proxy, SSL |
| **Testing** | pytest + pytest-asyncio + httpx | Async test client for FastAPI |
| **Migrations** | Alembic | Schema versioning |

---

## 📦 The 10 Core Features

1. **User Auth** — Register, login, JWT tokens, email verification, password reset, OAuth (Google)
2. **Agent Builder** — CRUD for AI agents (name, provider, model, system prompt, temperature, tools)
3. **Knowledge Base (RAG)** — Upload PDF/TXT/CSV/DOCX, scrape URLs, add raw text → injected as LLM context
4. **Chat Engine** — Session-tracked LLM conversations with conversation history, token accounting
5. **Tool System** — LLM function-calling: web search (DuckDuckGo), weather, lead catcher
6. **Multi-Channel Deploy** — Website widget (public, no auth), WhatsApp (QR), Discord, Slack webhooks
7. **Lead Capture** — Auto-extract contact info from conversations, save as leads, export CSV
8. **Workflow Engine** — Trigger → Action automation with integrations (Gmail, Telegram, Notion, Slack)
9. **Admin Panel** — User management, global API keys, analytics, pricing config, tools/channels CRUD
10. **Billing** — Stripe subscriptions with plan-based limits (free/starter/growth/business)

---

## 🧱 Architecture Principles (How It Differs from Original)

### Clean 4-Layer Architecture
```
Routes (thin controllers) → Services (business logic) → Repositories (data access) → Models (SQLAlchemy)
```

### Key Improvements Over Original
- **Separate schemas**: Pydantic models in `schemas/` (not inline in route files)
- **Repository pattern**: Data access in `repositories/` (not raw queries in route handlers)
- **Service layer**: Business logic in `services/` (not 1000-line route files)
- **API versioning**: `/api/v1/...` prefix
- **SQLAlchemy 2.0**: `Mapped[]` + `mapped_column()` instead of legacy `Column()`
- **Alembic migrations**: Schema versioning from day one
- **Modern Python**: `pyproject.toml`, `datetime.now(UTC)`, full type hints
- **Structured logging**: `logging` module instead of `print()`
- **Testable design**: Every service is independently testable with mocks

---

## 🗂️ Target Project Structure

```
botlixio-v2/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI app factory
│   │   ├── core/                      # Config, DB, security
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── security.py
│   │   ├── models/                    # SQLAlchemy 2.0 models
│   │   ├── schemas/                   # Pydantic request/response
│   │   ├── repositories/             # Data access layer
│   │   ├── services/                  # Business logic
│   │   │   ├── tools/                 # Tool system (web_search, weather, etc.)
│   │   │   └── integrations/          # Third-party integrations
│   │   ├── api/v1/                    # Versioned route handlers
│   │   └── utils/                     # Encryption, email helpers
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── unit/
│   │   └── integration/
│   ├── alembic/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/                          # Next.js + TypeScript
├── whatsapp-bridge/                   # Node.js Baileys service
├── docker/                            # Compose files + nginx
└── docs/
```

---

## 🧪 TDD Approach

Every feature follows **Red → Green → Refactor**:
1. **Write a failing test** for the feature
2. **Write minimal code** to make the test pass
3. **Refactor** for clean code (tests still pass)

**Testing layers**:
- **Unit tests**: Individual functions/services (mock dependencies)
- **Integration tests**: API endpoints hitting test DB (httpx.AsyncClient)

---

## 📍 Development Phases (16 Phases)

| # | Phase | What It Covers | Status |
|---|-------|---------------|--------|
| 0 | Project Scaffolding | Repo, Docker, pytest, Alembic setup | ⬜ Not started |
| 1 | Config & Database | Pydantic Settings, async engine, Base | ⬜ |
| 2 | Authentication | JWT, register, login, email verify, password reset | ⬜ |
| 3 | Agent CRUD | Agent model, schemas, CRUD endpoints | ⬜ |
| 4 | Chat Engine | LLM pipeline, session tracking, message history | ⬜ |
| 5 | Tool System | Web search, weather, lead catcher, function calling | ⬜ |
| 6 | Knowledge Base | File upload, URL scrape, RAG context injection | ⬜ |
| 7 | Widget (Public Chat) | Public endpoints, rate limiting, CORS | ⬜ |
| 8 | Billing | Stripe subscriptions, plan limits, webhooks | ⬜ |
| 9 | Integrations & Workflows | Plugin system, workflow engine, step execution | ⬜ |
| 10 | Admin Panel API | User mgmt, API keys, analytics, pricing config | ⬜ |
| 11 | Multi-Channel Webhooks | WhatsApp, Discord, Slack webhook handlers | ⬜ |
| 12 | Frontend: Landing + Auth | Landing page, login, register, email verify | ⬜ |
| 13 | Frontend: Dashboard | Agent mgmt, chat UI, knowledge base UI | ⬜ |
| 14 | Frontend: Admin + Billing | Admin panel, Stripe checkout, analytics | ⬜ |
| 15 | Production Deploy | Docker, Nginx, SSL, environment configs | ⬜ |

---

## 📎 Reference Files

The full detailed plan with per-phase tests, concepts, and code examples is in:
- **[botlixio_rebuild_plan.md](file:///Users/aman/.gemini/antigravity/brain/7842fa5c-af2b-4002-83b6-bff8fa17f706/botlixio_rebuild_plan.md)** — Attach this file for the detailed breakdown

The original project source code is at:
- **`/Users/aman/Documents/botlixio/`** — Can be referenced as a guide, but we rebuild from scratch

---

## 💬 How to Use This in a New Session

Paste this brief and say something like:

> *"I'm rebuilding the Botlixio AI Agent Platform from scratch with clean architecture and TDD. Here's the project brief and the detailed rebuild plan. Let's start Phase [X]. The project should be at `/Users/aman/Documents/botlixio-v2/`."*

Replace `[X]` with whichever phase you want to work on. Update the **Status** column in the phases table above as you complete each phase.
