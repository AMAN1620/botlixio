---
name: notes
description: >
  Writes beginner-friendly learning notes directly to Notion based on what was
  recently built in the Botlixio project. Covers FastAPI/Python (backend) and
  Next.js/TypeScript (frontend) concepts, with real code examples from the project.
  Use this skill whenever the user wants to document what they learned, update their
  notes after implementing a feature, or write a tutorial-style explanation of something
  they just built. Trigger on: "notes", "update notes", "document what I learned",
  "write notes for X", "add notes about JWT", "explain what we built".
---

# Notes — Write Learning Notes to Notion

Writes clear, beginner-friendly learning notes **directly to Notion** based on what was recently
built. The reader is learning FastAPI and Next.js/TypeScript while building this project.

No local files are written. Notion is the single source of truth.

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

### 2. Set up Notion structure (first run only)

Search Notion for an existing "Botlixio Notes" page:
- Use `notion-search` with query `"Botlixio Notes"`
- If **found**: note the page ID, then fetch it to find "Backend" and "Frontend" sub-page IDs
- If **not found**: create a top-level page titled "Botlixio Notes" with icon 📚, then immediately create two child pages under it: "Backend" (icon 🐍) and "Frontend" (icon ⚛️)

Store the Backend and Frontend page IDs — all notes go under one of these two parents.

### 3. Map work to topic pages

| What was built | Page title | Parent |
|---|---|---|
| `pyproject.toml`, venv | `python-packaging` | Backend |
| `app/main.py`, FastAPI app | `fastapi-basics` | Backend |
| `app/core/config.py`, pydantic-settings | `pydantic-settings` | Backend |
| `app/core/database.py`, SQLAlchemy | `sqlalchemy-async` | Backend |
| Alembic migrations | `alembic-migrations` | Backend |
| `app/core/security.py`, JWT, bcrypt | `auth-and-security` | Backend |
| `app/api/v1/*.py` routes | `fastapi-routing` | Backend |
| `app/schemas/*.py` | `pydantic-schemas` | Backend |
| `app/repositories/*.py` | `repository-pattern` | Backend |
| `app/services/*.py` | `service-layer` | Backend |
| `tests/`, pytest | `testing-fastapi` | Backend |
| `docker-compose.yml` | `docker-basics` | Backend |
| `.env`, environment vars | `environment-variables` | Backend |
| Next.js setup | `nextjs-setup` | Frontend |
| App Router, layouts | `nextjs-app-router` | Frontend |
| TypeScript types | `typescript-basics` | Frontend |
| Tailwind CSS | `tailwind-css` | Frontend |
| TanStack Query | `tanstack-query` | Frontend |
| React Hook Form, Zod | `forms-validation` | Frontend |
| Zustand | `zustand-state` | Frontend |

Create new topic pages for anything not in this table.

### 4. For each topic — create or update the Notion page

**Check if the page exists:**
- Use `notion-search` with the topic title (e.g. `"auth-and-security"`)
- Scope the search to within the "Botlixio Notes" page if possible

**If exists → update:**
- Use `notion-update-page` with `replace_content` command
- Replace the full content with the freshly written note

**If not exists → create:**
- Use `notion-create-pages` with the appropriate parent (Backend or Frontend page ID)
- Set `title` to the topic name (e.g. `auth-and-security`)
- Set `content` to the full note content in Notion markdown

**Note content format** — every page follows this structure:

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

- Links to related Notion pages in Botlixio Notes
- Links to relevant docs in `docs/`
```

### 5. Report to the user

After all pages are saved to Notion, print a summary:
- Which pages were **created** (new) vs **updated** (existing)
- Direct Notion page titles listed
- Example: "Saved 3 notes to Notion: created `auth-and-security`, updated `fastapi-basics`, `pydantic-schemas`"

---

## Rules

- **Notion only** — do NOT write any local files; Notion is the sole destination
- **Beginner-first** — every concept needs a plain-English "What is this?" before any code
- **Project-grounded** — examples must come from actual Botlixio files, not generic tutorials
- **No duplication** — search Notion before creating; update existing pages, don't duplicate
- **Short over long** — each note should be scannable in 2–3 minutes
- **Gotchas are gold** — if something broke and had to be fixed, it goes in Gotchas
- **Real commands only** — document commands that actually ran and worked
- **Respect `$ARGUMENTS`** — if a topic filter is given, only update those pages