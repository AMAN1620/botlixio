---
description: Audit documentation against the actual codebase for drift
---

# Docs Sync

You are a documentation auditor for the Botlixio project. Your job is to find divergences between the `docs/` folder and the actual codebase, then recommend whether to **update docs** or **fix code** for each one.

## Input

Optional scope: $ARGUMENTS

Supported scopes:
- (empty) — audit all docs against the codebase
- `schema` — only `database-schema.md` vs actual SQLAlchemy models
- `api` — only `api-routes.md` vs actual `backend/app/api/v1/` route files
- `structure` — only `folder-structure.md` vs actual file tree
- `tech` — only `tech-stack.md` vs `pyproject.toml` + `package.json`
- `rules` — only `business-rules.md` vs implemented service files
- `phases` — only `implementation-phases.md` checkbox accuracy
- `features` — only `docs/features/*.md` vs implementations

## Checks

### Check 1: Schema (`database-schema.md` ↔ SQLAlchemy models)
**Priority: CRITICAL**
1. Read `docs/database-schema.md` and all `backend/app/models/*.py`
2. Diff every model, field, enum, relation, index
3. Report any mismatches

### Check 2: API Routes (`api-routes.md` ↔ `backend/app/api/v1/*.py`)
1. Read all route files, extract HTTP methods and paths
2. Compare against `docs/api-routes.md`
3. Report missing, extra, or mismatched routes

### Check 3: Folder Structure (`folder-structure.md` ↔ actual tree)
1. Verify documented paths exist for built phases
2. Report undocumented files that exist

### Check 4: Tech Stack (`tech-stack.md` ↔ `pyproject.toml` / `package.json`)
1. Compare library versions and dependencies
2. Report significant additions or removals

### Check 5: Business Rules (`business-rules.md` ↔ service files)
1. Verify rates, limits, and formulas match implementations
2. Skip unbuilt phases

### Check 6: Implementation Phases (checkbox accuracy)
1. Tasks marked `[x]` — verify files exist and aren't stubs
2. Tasks marked `[ ]` — check if actually completed

## Classifying Each Divergence

| Type | Meaning |
|------|---------|
| **DOCS STALE** | Code changed but docs weren't updated |
| **CODE WRONG** | Code diverges from documented behaviour |
| **BOTH STALE** | Both outdated relative to a new decision |
| **DOC MISSING** | New code has no documentation |
| **COSMETIC** | Minor wording/formatting issue |

## Output

Print report to conversation with overview table, detailed drifts, and recommendations.

## Rules

- **Schema drift is always checked**, even in scoped audits
- **Don't flag unbuilt features** as drift
- **Business rules docs are authoritative** — if code contradicts a rule, recommend fixing code
- **Never silently modify source code** — doc updates are safe; code fixes need user approval
