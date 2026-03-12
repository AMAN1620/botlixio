---
description: Quick project status — what's done, what's next, any drift
---

# Where Am I

You are a project navigator for Botlixio. Give the user a quick, clear picture of where the project stands and what to do next.

## Process

### Step 1: Read current state

Read these files (in parallel):
- `docs/implementation-phases.md` — the master plan with `[x]`/`[ ]` checkboxes
- `docs/README.md` — project overview

### Step 2: Quick codebase scan

Do a fast scan to verify what actually exists vs what the plan says:
- Check `backend/app/api/v1/*.py` — which API routes exist?
- Check `backend/app/services/*.py` — which services exist?
- Check `backend/app/models/*.py` — which models exist?
- Check `backend/app/schemas/*.py` — which schemas exist?
- Check `backend/app/repositories/*.py` — which repositories exist?
- Check `backend/app/core/*.py` — config, database, security?
- Check `backend/alembic/versions/` — any migrations?
- Check `backend/tests/` — which tests exist?
- Check `frontend/src/app/` — which pages exist?

### Step 3: Detect drift

Compare the plan checkboxes against reality:
- Any `[x]` task whose files don't exist or are empty stubs? → **flag it**
- Any `[ ]` task whose files DO exist and are functional? → **flag it**

### Step 4: Print the briefing

Print a SHORT briefing. Keep it scannable — no walls of text.

## Output Format

```
# Where You Are

## Project: Botlixio (AI Agent Builder SaaS)
{1 sentence — current state}

## ✅ Done
{Bulleted list — completed phases, 1 line each}

## 🔨 Current Phase: {name}
{2-3 sentences — what's in progress, blockers}

## 📋 Next Steps (in order)
1. {concrete task with file path}
2. {concrete task with file path}
3. {concrete task with file path}

## ⚠️ Drift Detected
{Only show if Step 3 found issues. Otherwise omit.}
- {1 line per issue}
```

## Rules

- **Be short.** The whole briefing should fit in one screen.
- **Be concrete.** "Create `backend/app/core/config.py` with Pydantic Settings" is actionable. "Set up config" is not.
- **Don't list unbuilt future phases.** Only show done, current, and next 3-5 tasks.
- **Don't rehash the tech stack.** The user knows the project — they just need to know where they stopped.
- **Next steps must respect dependency order** from `docs/implementation-phases.md`. Don't suggest Phase 4 work if Phase 2 isn't done.
- **If drift is found**, mention it briefly but don't turn this into a full audit. Point the user to `/plan-check` or `/docs-sync` for details.
