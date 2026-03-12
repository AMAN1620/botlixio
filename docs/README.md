# Botlixio — AI Agent Builder SaaS Platform

## Overview

Botlixio is a full-stack **AI Agent Builder SaaS platform** that lets users create, configure, and deploy custom AI chatbot agents across multiple channels. Users sign up, build AI agents (choosing LLM provider, model, system prompt, tools), upload knowledge bases for RAG, and deploy those agents to website widgets, WhatsApp, Discord, and Slack.

---

## Core Modules

| Module | Purpose |
|--------|---------|
| [Authentication](features/01-authentication.md) | Register, login, JWT, email verification, OAuth |
| [Agent Builder](features/02-agent-builder.md) | CRUD for AI agents with custom configs |
| [Chat Engine](features/03-chat-engine.md) | LLM pipeline, session tracking, message history |
| [Tool System](features/04-tool-system.md) | LLM function-calling: web search, weather, lead catcher |
| [Knowledge Base](features/05-knowledge-base.md) | File upload, URL scrape, RAG context injection |
| [Widget (Public Chat)](features/06-widget.md) | Public endpoints, rate limiting, CORS |
| [Billing & Subscriptions](features/07-billing.md) | Stripe subscriptions, plan-based limits |
| [Integrations & Workflows](features/08-integrations-workflows.md) | Plugin system, workflow automation |
| [Admin Panel](features/09-admin-panel.md) | User mgmt, API keys, analytics, pricing config |
| [Multi-Channel Deploy](features/10-multi-channel.md) | WhatsApp, Discord, Slack webhook handlers |

---

## Key Design Decisions

### Clean 4-Layer Architecture
```
Routes (thin controllers) → Services (business logic) → Repositories (data access) → Models (SQLAlchemy)
```

### API Versioning
All API routes prefixed with `/api/v1/` for future compatibility.

### Role-Based Access
| Role | Access |
|------|--------|
| ADMIN | Full platform access, user management, API keys, pricing |
| USER | Own agents, knowledge bases, billing, channels |

### BYOK (Bring Your Own Key)
Platform uses admin-configured API keys by default. Users on higher plans can optionally bring their own LLM API keys.

### Multi-Provider LLM
LiteLLM provides a single interface for OpenAI, Anthropic, and Google models. The platform admin configures which providers/models are available per subscription plan.

---

## Reference Docs

- [Tech Stack & Setup](tech-stack.md)
- [Folder Structure](folder-structure.md)
- [Database Schema](database-schema.md)
- [Business Rules](business-rules.md)
- [API Routes](api-routes.md)
- [Implementation Phases](implementation-phases.md)
