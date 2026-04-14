---
name: Botlixio Project Context
description: Architecture, completed phases, and key security-relevant facts about the Botlixio platform
type: project
---

Botlixio is a FastAPI + Next.js AI Agent Builder SaaS. Phases 0-3 are complete (auth, database, email verification). Phases 4-6 are partially complete (agents, knowledge base, chat engine with widget but no rate limiting). Phases 7-16 not yet built.

**Why:** This context determines audit scope — only flag code that exists.

**How to apply:** Do not flag missing rate limiting, billing enforcement, or OAuth as unimplemented if the phase is not yet complete. However, DO flag security bugs in phases that ARE implemented.

Key security-relevant facts observed in 2026-04-06 audit:
- `backend/.env` contains a live OpenAI API key (sk-proj-rOg06...), Gmail app password, Google OAuth secret, and a real DB password. File is gitignored but present on disk — rotate immediately.
- CORS is set to `allow_origins=["*"]` with no production gate — authenticating routes will fail with this config when cookies are needed.
- OAuth callback leaks JWT tokens in URL query parameters (redirect to /auth/callback?access_token=...&refresh_token=...).
- No OAuth state parameter (CSRF protection missing for Google OAuth flow).
- API docs (Swagger/ReDoc) are exposed in all environments — not gated on `is_production`.
- Widget chat accepts a client-supplied `session_id` without validation — any string becomes a session identifier, enabling session hijacking between widget users.
- Email verification is NOT checked before agent creation (business rule violated).
- Plan limit check in `agent_service.py` is hardcoded to `FREE_PLAN_AGENT_LIMIT = 3` — ignores actual subscription; wrong limit for FREE plan (should be 1).
- `system_prompt` and text knowledge content have no `max_length` validators in schemas, enabling unbounded LLM context injection.
- Chat message schema has no `max_length` on message field — unlimited tokens can be sent.
- `AddUrlRequest.url` is unvalidated (comment says "validated at runtime by crawler") — no scheme/host validation at schema level.
- `document_parser.py` dispatches by file extension only — no MIME type validation, zip bombs possible.
- DEV reset link is logged to WARNING level with plaintext reset token (auth_service.py:312).
- Qdrant and Redis ports are exposed on host network in docker-compose.yml.
- Next.js frontend is on version 16.1.6 which has 5 known CVEs including HTTP request smuggling and CSRF bypass.
- `asyncio.get_event_loop()` (deprecated Python 3.10+) used in email_service.py.
