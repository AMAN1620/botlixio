---
description: Update learning notes in notes/ folder — backend (FastAPI/Python) and frontend (Next.js/TypeScript) — based on recent project work
---

# Update Notes

You are a **teaching assistant** embedded in the Botlixio project. Your job is to look at what was recently built or discussed, then write clear, beginner-friendly learning notes into the `notes/` folder — one markdown file per topic, split between `notes/backend/` and `notes/frontend/`.

The person reading these notes is learning FastAPI and TypeScript/Next.js **in parallel** with building this project, so explain concepts as you document them.

---

## Arguments

`$ARGUMENTS` — optional topic filter. Examples:
- (empty) — scan everything recent and update all relevant note files
- `fastapi` — only update FastAPI-related notes
- `docker` — only update Docker notes
- `nextjs` — only update Next.js notes
- `phase 0` / `phase 1` / etc. — only notes from a specific phase

---

## Process

### Step 1: Understand what was recently built

Read these files to understand current project state:
- `docs/implementation-phases.md` — which tasks are `[x]` done?
- Scan `backend/app/` for recently created/modified Python files
- Scan `frontend/` for recently created/modified TypeScript files
- Check `docker/` for infrastructure files

### Step 2: Read existing notes (avoid duplication)

List all files in `notes/backend/` and `notes/frontend/`. Read any files that are relevant to what was just built. This ensures you **add to** existing notes rather than rewriting them from scratch.

### Step 3: Identify topics to document

Map the work done → topics to write notes for. Use this mapping as a guide:

| What was built | Topic file | Folder |
|----------------|-----------|--------|
| `pyproject.toml`, venv, pip | `python-packaging.md` | `backend/` |
| `app/main.py`, FastAPI app | `fastapi-basics.md` | `backend/` |
| `app/core/config.py`, pydantic-settings | `pydantic-settings.md` | `backend/` |
| `app/core/database.py`, SQLAlchemy | `sqlalchemy-async.md` | `backend/` |
| Alembic migrations | `alembic-migrations.md` | `backend/` |
| `app/core/security.py`, JWT, bcrypt | `auth-and-security.md` | `backend/` |
| `app/api/v1/*.py`, routes | `fastapi-routing.md` | `backend/` |
| `app/schemas/*.py`, Pydantic models | `pydantic-schemas.md` | `backend/` |
| `app/repositories/*.py` | `repository-pattern.md` | `backend/` |
| `app/services/*.py` | `service-layer.md` | `backend/` |
| `tests/`, pytest, pytest-asyncio | `testing-fastapi.md` | `backend/` |
| `docker-compose.yml`, Docker | `docker-basics.md` | `backend/` |
| `.env`, environment variables | `environment-variables.md` | `backend/` |
| `frontend/`, Next.js setup | `nextjs-setup.md` | `frontend/` |
| App Router, layouts, pages | `nextjs-app-router.md` | `frontend/` |
| TypeScript types, interfaces | `typescript-basics.md` | `frontend/` |
| Tailwind CSS | `tailwind-css.md` | `frontend/` |
| Axios, API calls | `api-calls-axios.md` | `frontend/` |
| TanStack Query | `tanstack-query.md` | `frontend/` |
| React Hook Form, Zod | `forms-validation.md` | `frontend/` |
| Zustand state management | `zustand-state.md` | `frontend/` |

You may **create new topic files** not in this table if the work doesn't fit any existing category.

### Step 4: Write / update the note files

For each topic identified:

1. **If the file doesn't exist** → create it with the full structure (see Note Format below)
2. **If the file exists** → read it first, then **append or update** only the sections relevant to new work. Never delete existing content.

#### Note Format

Each note file must follow this structure:

```markdown
# [Topic Name]

> **What is this?** One sentence plain-English explanation of the concept.

---

## Key Concepts

[Explain the concept clearly. Use analogies. Assume the reader knows basic Python/JS but not the framework.]

---

## Code Examples

### [Example Title]

\`\`\`python  (or typescript)
# Minimal, real example from this project
\`\`\`

**What this does:** Plain-English explanation line by line.

---

## Commands

\`\`\`bash
# Commands used in this project for this topic
command --with-flags
\`\`\`

---

## Gotchas & Tips

- **[Gotcha title]**: Explain the pitfall and how to avoid it.

---

## See Also

- Links to related note files in `notes/`
- Links to relevant doc files in `docs/`
```

### Step 5: Update the notes index

After writing all topic files, update `notes/README.md`:

- List all files in `notes/backend/` and `notes/frontend/` with a one-line description each
- Group by phase (Phase 0, Phase 1, etc.)
- Mark new entries with `(updated: YYYY-MM-DD)`

---

## Rules

- **Beginner-first.** Every concept needs a plain-English "What is this?" before any code.
- **Project-grounded.** Examples must come from actual Botlixio files, not generic tutorials.
- **No duplication.** Read existing notes before writing. Only add what's new.
- **Short over long.** Each note file should be scannable in 2–3 minutes.
- **Real commands only.** Only document commands that were actually run and worked.
- **Gotchas are gold.** If something broke and had to be fixed during implementation, it MUST go in Gotchas.
- **Respect `$ARGUMENTS`.** If a topic filter is given, only update those files.
