---
name: notes
description: >
  Writes beginner-friendly learning notes into the notes/ folder based on what was
  recently built in the Botlixio project. Covers FastAPI/Python (backend) and
  Next.js/TypeScript (frontend) concepts, with real code examples from the project.
  Use this skill whenever the user wants to document what they learned, update their
  notes after implementing a feature, or write a tutorial-style explanation of something
  they just built. Trigger on: "notes", "update notes", "document what I learned",
  "write notes for X", "add notes about JWT", "explain what we built".
---

# Notes — Write Learning Notes

Writes clear, beginner-friendly learning notes into `notes/` based on what was recently
built. The reader is learning FastAPI and Next.js/TypeScript while building this project.

## Input

`$ARGUMENTS` — optional topic filter:

| Argument | What gets updated |
|---|---|
| (empty) | Scan everything recent, update all relevant notes |
| `fastapi` | FastAPI-related notes only |
| `docker` | Docker notes only |
| `nextjs` | Next.js notes only |
| `phase 0` / `phase 1` / etc. | Notes from a specific phase only |

---

## Process

### 1. Understand what was recently built

Read in parallel:
- `docs/implementation-phases.md` — which tasks are `[x]` done?
- Scan `backend/app/` for recently modified Python files
- Scan `frontend/` for recently modified TypeScript files

### 2. Read existing notes first (avoid duplication)

```bash
ls notes/backend/ notes/frontend/ 2>/dev/null
```

Read any files relevant to what was just built — add to existing notes, don't rewrite from scratch.

### 3. Map work to topic files

| What was built | Note file | Folder |
|---|---|---|
| `pyproject.toml`, venv | `python-packaging.md` | `backend/` |
| `app/main.py`, FastAPI app | `fastapi-basics.md` | `backend/` |
| `app/core/config.py`, pydantic-settings | `pydantic-settings.md` | `backend/` |
| `app/core/database.py`, SQLAlchemy | `sqlalchemy-async.md` | `backend/` |
| Alembic migrations | `alembic-migrations.md` | `backend/` |
| `app/core/security.py`, JWT, bcrypt | `auth-and-security.md` | `backend/` |
| `app/api/v1/*.py` routes | `fastapi-routing.md` | `backend/` |
| `app/schemas/*.py` | `pydantic-schemas.md` | `backend/` |
| `app/repositories/*.py` | `repository-pattern.md` | `backend/` |
| `app/services/*.py` | `service-layer.md` | `backend/` |
| `tests/`, pytest | `testing-fastapi.md` | `backend/` |
| `docker-compose.yml` | `docker-basics.md` | `backend/` |
| `.env`, environment vars | `environment-variables.md` | `backend/` |
| Next.js setup | `nextjs-setup.md` | `frontend/` |
| App Router, layouts | `nextjs-app-router.md` | `frontend/` |
| TypeScript types | `typescript-basics.md` | `frontend/` |
| Tailwind CSS | `tailwind-css.md` | `frontend/` |
| TanStack Query | `tanstack-query.md` | `frontend/` |
| React Hook Form, Zod | `forms-validation.md` | `frontend/` |
| Zustand | `zustand-state.md` | `frontend/` |

Create new topic files for anything not in this table.

### 4. Write or update each note file

**Note format** — every file follows this structure:

```markdown
# [Topic Name]

> **What is this?** One sentence plain-English explanation.

---

## Key Concepts

[Explain clearly. Use analogies. Assume basic Python/JS but not the framework.]

---

## Code Examples

### [Example Title]

\```python
# Real example from this project
\```

**What this does:** Plain-English explanation.

---

## Commands

\```bash
# Commands actually used in this project
\```

---

## Gotchas & Tips

- **[Gotcha title]**: Explain the pitfall and how to avoid it.

---

## See Also

- Links to related notes in `notes/`
- Links to relevant docs in `docs/`
```

### 5. Update the notes index

After writing all topic files, update `notes/README.md`:
- List all files in `notes/backend/` and `notes/frontend/` with one-line descriptions
- Group by phase
- Mark new/updated entries with `(updated: YYYY-MM-DD)`

---

## Rules

- **Beginner-first** — every concept needs a plain-English "What is this?" before any code
- **Project-grounded** — examples must come from actual Botlixio files, not generic tutorials
- **No duplication** — read existing notes before writing; only add what's new
- **Short over long** — each note should be scannable in 2–3 minutes
- **Gotchas are gold** — if something broke and had to be fixed, it goes in Gotchas
- **Real commands only** — document commands that actually ran and worked
- **Respect `$ARGUMENTS`** — if a topic filter is given, only update those files
