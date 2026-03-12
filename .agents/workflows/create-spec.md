---
description: Create a detailed SPEC.md for a feature module
---

# Create Spec

You are a senior technical writer for the Botlixio project. Your job is to create a detailed SPEC.md file for a feature module by reading the project docs and the actual codebase, then writing a comprehensive specification.

## Input

Arguments: $ARGUMENTS

Supported arguments:
- A module name (e.g., `auth`, `agents`, `chat`, `billing`, `knowledge`)
- A route path (e.g., `/auth`, `/agents`, `/chat`)
- A feature doc path (e.g., `docs/features/01-authentication.md`)
- `all` — generate specs for all modules that have a feature doc but no SPEC.md yet

If no argument is provided, ask the user which module to create a spec for.

## Process

### Step 1: Identify the module

From the argument, determine:
- **Module name** (e.g., "Authentication", "Agent Builder")
- **Feature doc path**: `docs/features/{NN}-{name}.md`
- **Backend directory**: `backend/app/api/v1/{module}.py`, `backend/app/services/{module}_service.py`
- **Phase number**: from `docs/implementation-phases.md`

If a SPEC.md already exists at `backend/app/api/v1/{module}/SPEC.md` or `backend/specs/{module}.SPEC.md`:
- Tell the user: "SPEC.md already exists at {path}. Use `redo` to regenerate, or edit it manually."
- Stop unless the user passed `redo` or confirmed overwrite.

### Step 2: Determine spec mode

Check if the module has been implemented yet:
- Does `backend/app/api/v1/{module}.py` exist with actual route handlers?
- Does `backend/app/services/{module}_service.py` exist?
- Does `backend/app/schemas/{module}.py` exist?
- Does `backend/app/repositories/{module}_repo.py` exist?

If implementation files exist → **Retroactive mode**: Document what was *actually built*.
If no implementation files exist → **Proactive mode**: Write a forward-looking design guide.

### Step 3: Read all source material

Read these files (skip any that don't exist):

**Always read:**
- `docs/features/{NN}-{name}.md` — business requirements (REQUIRED — stop if missing)
- `docs/api-routes.md` — endpoint contracts
- `docs/business-rules.md` — domain rules
- `docs/database-schema.md` — data model
- `docs/implementation-phases.md` — phase/layer info

**Retroactive mode — also read:**
- `backend/app/schemas/{module}.py` — Pydantic schemas
- `backend/app/services/{module}_service.py` — service functions
- `backend/app/api/v1/{module}.py` — route handlers
- `backend/app/repositories/{module}_repo.py` — data access
- `backend/tests/**/*{module}*` — all tests

### Step 4: Analyze and plan the spec

Before writing, analyze:
1. **Routes**: List all routes for this module
2. **Access control**: Which roles can access
3. **Files**: List all source files  
4. **User stories**: Extract from feature doc
5. **Edge cases**: Identify from validation rules, error handling
6. **API contracts**: Document each endpoint with request/response shapes
7. **Test counts**: Count actual tests (retroactive) or plan categories (proactive)

### Step 5: Write the SPEC.md

Follow this structure:

```markdown
# Spec: {Module Name}

**Phase**: {N}
**Routes**: {list}
**Access**: {roles}

**Files**:
- {each source file with description}

---

## Overview
{2-3 sentences}

## User Stories
| ID | As a... | I want to... | So that... |

## Happy Flows
{Numbered steps}

## Edge Cases
| Scenario | Expected Behaviour |

## Pydantic Schemas
{Actual or proposed schema code}

## API Contract
{Each endpoint with method, route, body, response codes}

## Test Scenarios
{Group by test layer}

## Acceptance Criteria
{Checklist}

## Deferred / Not Yet Implemented (retroactive only)
```

### Step 6: Verify the spec

Verify all file paths exist, schemas match code, API response codes match handlers.

### Step 7: Report

Print summary of what was created.

## Rules

- **Feature doc is required.** Stop if missing.
- **Be accurate, not aspirational.** In retroactive mode, document what IS built.
- **Embed actual code.** Schemas should be copied verbatim.
- **Don't invent requirements.** Requirements come from docs only.
