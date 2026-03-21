---
name: docs-sync
description: >
  Audits the docs/ folder against the actual codebase and flags drift — places where
  docs are stale, code diverged from documented behaviour, or new code has no docs.
  Use this skill whenever the user wants to check if docs are up to date, find
  documentation drift, verify the schema docs match the models, or audit API docs
  against actual routes. Trigger on: "are my docs up to date", "check for doc drift",
  "sync the docs", "docs-sync", "is the schema doc accurate", "audit documentation".
---

# Docs Sync

Finds divergences between `docs/` and the actual codebase, then recommends whether to
**update docs** or **fix code** for each one.

## Scope

`$ARGUMENTS` — optional filter:

| Argument | What gets checked |
|---|---|
| (empty) | All checks below |
| `schema` | `database-schema.md` vs SQLAlchemy models |
| `api` | `api-routes.md` vs `backend/app/api/v1/` route files |
| `structure` | `folder-structure.md` vs actual file tree |
| `tech` | `tech-stack.md` vs `pyproject.toml` + `package.json` |
| `rules` | `business-rules.md` vs service files |
| `phases` | `implementation-phases.md` checkbox accuracy |
| `features` | `docs/features/*.md` vs implementations |

Schema drift is always checked regardless of scope.

---

## Checks

### Schema — `database-schema.md` ↔ SQLAlchemy models
Read `docs/database-schema.md` and all `backend/app/models/*.py`. Diff every model,
field type, enum value, relationship, and index. Any mismatch = finding.

### API Routes — `api-routes.md` ↔ route files
Read all `backend/app/api/v1/*.py`, extract HTTP methods and paths with:
```bash
grep -n "@router\." backend/app/api/v1/*.py
```
Compare against every route in `docs/api-routes.md`. Report missing, extra, or renamed routes.

### Folder Structure — `folder-structure.md` ↔ file tree
Verify documented paths exist. Flag undocumented files that exist in built phases.

### Tech Stack — `tech-stack.md` ↔ dependencies
```bash
grep -E "^\[" backend/pyproject.toml   # package versions
cat frontend/package.json | grep '"dependencies"' -A 30
```
Report significant version differences or added/removed packages.

### Business Rules — `business-rules.md` ↔ service files
Check rates, limits, and formulas in `backend/app/services/*.py` match what the doc says.
Skip checks for services that don't exist yet (unbuilt phases).

### Implementation Phases — checkbox accuracy
- Tasks marked `[x]` → verify the files exist and contain real logic (not stubs)
- Tasks marked `[ ]` → check if files actually exist (accidentally done early?)

### Feature Docs — `docs/features/*.md` ↔ implementations
For each feature doc, check if the described endpoints, schemas, and behaviours exist in code.

---

## Classifying each divergence

| Type | Meaning |
|---|---|
| **DOCS STALE** | Code changed but docs weren't updated |
| **CODE WRONG** | Code diverges from documented behaviour |
| **BOTH STALE** | Both outdated relative to a new decision |
| **DOC MISSING** | New code has no documentation |
| **COSMETIC** | Minor wording/formatting issue only |

---

## Output

Print report to conversation:

```
# Docs Sync Report — {date}
Scope: {full | specific}

## Overview
| Check | Status | Issues Found |
|-------|--------|-------------|
| Schema | ✅ / ⚠️ | N |
| API Routes | ✅ / ⚠️ | N |
| ...

## Findings

### [DOCS STALE] `database-schema.md` — User model missing `is_verified` field
- **Doc says:** field not mentioned
- **Code has:** `is_verified: Mapped[bool]` in `backend/app/models/user.py:34`
- **Recommendation:** Add field to schema doc

### [CODE WRONG] `business-rules.md` — Free plan message limit
- **Doc says:** 100 messages/month
- **Code has:** `max_messages = 50` in `backend/app/services/billing_service.py:87`
- **Recommendation:** Fix code to match docs (docs are authoritative for business rules)

## Summary
- N docs stale
- N code wrong
- N doc missing
- Recommend running /plan-check for deeper implementation drift
```

---

## Rules

- Business rules docs are authoritative — if code contradicts a rule, recommend fixing code
- Don't flag unbuilt features as drift
- Doc updates are safe to suggest; code fixes need user approval before touching anything
- Never silently modify source code or docs — diagnostic only
