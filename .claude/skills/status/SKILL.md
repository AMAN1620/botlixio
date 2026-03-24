---
name: status
description: >
  Gives a quick, scannable briefing on where the Botlixio project stands — what's done,
  what's in progress, what to do next, and any drift between plan and code. Use this
  skill whenever the user wants a project status update, wants to know what to work on
  next, is returning to the project after a break, or wants a progress summary. Trigger
  on: "status", "where am i", "what's done", "what should I work on next", "project
  status", "catch me up", "what's the next step", "where did I leave off".
---

# Status — Quick Project Briefing

Quick project briefing — done, in progress, next steps, any drift. Fits in one screen.

---

## Process

Read in parallel:
- `docs/implementation-phases.md` — master plan with `[x]`/`[ ]` checkboxes
- `docs/README.md` — project overview

Then do a fast codebase scan:

```bash
ls backend/app/api/v1/
ls backend/app/services/
ls backend/app/models/
ls backend/app/schemas/
ls backend/app/repositories/
ls backend/app/core/
ls backend/alembic/versions/
ls backend/tests/unit/ backend/tests/integration/
ls frontend/app/ 2>/dev/null
```

Also check TDD pipeline state:

```bash
ls docs/specs/*.SPEC.md 2>/dev/null
ls docs/tdd/*.TEST-CASES.md 2>/dev/null
ls docs/tdd/reports/*.html 2>/dev/null
```

Compare scan results against plan checkboxes:
- `[x]` task but files don't exist or are empty stubs → **flag as drift**
- `[ ]` task but files DO exist and are functional → **flag as drift**

---

## Output

```
# Status — {date}

## Project: Botlixio (AI Agent Builder SaaS)
{1 sentence — current state}

## Done
- Phase 0: Project setup, Docker, DB, config
- Phase 1: Auth — register, login, JWT, email verification

## In Progress: Phase 2 — Agent Builder
{2–3 sentences on what's actively being built and any blockers}

## TDD Pipeline
| Feature | Spec | Test Cases | Tests | Implemented |
|---------|------|------------|-------|-------------|
| auth    | done | done       | done  | done        |
| agents  | done | pending    | -     | -           |

## Next Steps
1. Run `/tdd-plan docs/specs/agents.SPEC.md` — plan test cases
2. Run `/tdd-generate` — write pytest files
3. Run `/tdd-implement` — implement agent CRUD

## Drift Detected
- `[x]` auth_service.py marked done but is a stub (8 lines)

Run `/plan-audit` for full drift analysis.
```

Omit **Drift Detected** section entirely if no drift is found.
Omit **TDD Pipeline** table if no specs exist yet.

---

## Rules

- Keep it short — the whole briefing fits in one screen
- Be concrete — "Run `/tdd-plan docs/specs/agents.SPEC.md`" not "plan tests"
- Don't list unbuilt future phases — show done, current, and next 3–5 tasks only
- Don't rehash the tech stack — the user knows the project
- Next steps must respect dependency order from the plan
- Next steps should reference the correct skill to run (e.g., `/spec-writer`, `/tdd-plan`, `/tdd-implement`)
- If drift found, mention briefly and point to `/plan-audit` for details
