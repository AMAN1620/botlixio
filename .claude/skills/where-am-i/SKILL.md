---
name: where-am-i
description: >
  Gives a quick, scannable briefing on where the Botlixio project stands — what's done,
  what's in progress, what to do next, and any drift between plan and code. Use this
  skill whenever the user wants a project status update, wants to know what to work on
  next, is returning to the project after a break, or wants a progress summary. Trigger
  on: "where am i", "what's done", "what should I work on next", "project status",
  "catch me up", "what's the next step", "where did I leave off".
---

# Where Am I

Quick project briefing — done, in progress, next steps, any drift. Fits in one screen.

---

## Process

Read in parallel:
- `docs/implementation-phases.md` — master plan with `[x]`/`[ ]` checkboxes
- `docs/README.md` — project overview

Then do a fast codebase scan:

```bash
ls backend/app/api/v1/        # which routes exist
ls backend/app/services/      # which services exist
ls backend/app/models/        # which models exist
ls backend/app/schemas/       # which schemas exist
ls backend/app/repositories/  # which repos exist
ls backend/app/core/          # config, database, security
ls backend/alembic/versions/  # migrations
ls backend/tests/unit/ backend/tests/integration/  # tests
ls frontend/app/ 2>/dev/null  # frontend pages
```

Compare scan results against plan checkboxes:
- `[x]` task but files don't exist or are empty stubs → **flag as drift**
- `[ ]` task but files DO exist and are functional → **flag as drift**

---

## Output

```
# Where You Are — {date}

## Project: Botlixio (AI Agent Builder SaaS)
{1 sentence — current state, e.g. "Phase 1 (Auth) complete, starting Phase 2 (Agents)."}

## ✅ Done
- Phase 0: Project setup, Docker, DB, config
- Phase 1: Auth — register, login, JWT, email verification

## 🔨 In Progress: Phase 2 — Agent Builder
{2–3 sentences on what's actively being built and any blockers}

## 📋 Next Steps
1. Create `backend/app/models/agent.py` — Agent SQLAlchemy model
2. Create `backend/app/schemas/agent.py` — CreateAgent / UpdateAgent schemas
3. Create `backend/app/repositories/agent_repo.py` — CRUD operations

## ⚠️ Drift Detected
- `[x]` auth_service.py marked done but is a stub (8 lines)
- `[ ]` billing_service.py marked incomplete but file exists

Run /plan-check for full drift analysis.
```

Omit the **Drift Detected** section entirely if no drift is found.

---

## Rules

- Keep it short — the whole briefing fits in one screen
- Be concrete — "Create `backend/app/core/config.py`" not "set up config"
- Don't list unbuilt future phases — show done, current, and next 3–5 tasks only
- Don't rehash the tech stack — the user knows the project
- Next steps must respect dependency order from the plan
- If drift found, mention briefly and point to /plan-check or /docs-sync for details
