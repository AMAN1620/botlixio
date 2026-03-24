---
name: spec-writer
description: >
  Creates a detailed SPEC.md for a feature module by reading project docs and the actual
  codebase. Works in two modes: Retroactive (document what was built) or Proactive
  (design guide before implementation). Does NOT include test scenarios — that's tdd-plan's
  job. Use this skill whenever the user wants to document a feature, write a spec before
  starting to code, generate a spec from existing code, design an API contract, or produce
  a structured feature specification. Trigger on: "write a spec", "spec writer", "spec out
  the auth module", "I need a spec before I start coding", "document this feature",
  "create a spec for X", or when the user references a feature doc and wants a formal spec.
---

# Spec Writer — Create a Feature Spec

Produces a `SPEC.md` for a feature module — the single source of truth for what that feature does, what the API looks like, and what the schemas contain.

Does NOT plan tests — instead you can ask user to run `/tdd-plan` after this skill.

## Input

`$ARGUMENTS` — one of:
- Module name: `auth`, `agents`, `chat`, `billing`
- Route path: `/auth`, `/agents`
- Feature doc path: `docs/features/01-authentication.md`
- `all` — generate specs for all modules missing a SPEC.md

If no argument, ask the user which module to spec.

---

## Step 1 — Detect project structure

```bash
ls backend/app/api/v1/ 2>/dev/null
ls backend/app/services/ backend/app/schemas/ backend/app/repositories/ 2>/dev/null
ls docs/features/ 2>/dev/null
ls docs/specs/ 2>/dev/null
```

Use discovered paths throughout — never hardcode.

---

## Step 2 — Identify module and mode

1. Map the argument to a module name and locate its feature doc in `docs/features/`.
2. Check if implementation files exist with real logic (not just stubs):
   - **Retroactive** → route handlers, service functions, and schemas exist → document what IS built
   - **Proactive** → files don't exist yet → write a forward-looking design guide
3. State the mode before proceeding.
4. Check for existing SPEC.md in `docs/specs/` — if found, tell the user and stop (unless `redo` was passed).

---

## Step 3 — Read sources in parallel, starting with the feature doc:

**Always read** (stop if feature doc is missing):
- Feature doc — business requirements and user stories
- `docs/api-routes.md` — API surface area
- `docs/business-rules.md` — role and limit rules
- `docs/database-schema.md` — data model

**Retroactive — also read:**
- Schema/Pydantic files for this module
- Service file(s)
- Route/controller file(s)
- Repository file(s)

---

## Step 4 — Write the SPEC

Output to `docs/specs/{module}.SPEC.md`.

Use the template from [template.md](template.md) for the exact output format.

For a real example, see [examples/sample.md](examples/sample.md).

---

## Step 5 — Verify before finishing

- All listed file paths exist (retroactive) or are reasonable (proactive)
- Response codes match actual route handlers
- Schema field names match actual code
- Flag any mismatch found

---

## Gotchas

- Feature doc is required — stop if you can't find it.
- Retroactive mode: document what IS built, not what was planned. If the feature doc says "OAuth login" but the code doesn't have it, put it in "Deferred".
- Copy schemas verbatim from source (retroactive) — never paraphrase field names or types.
- Don't invent requirements — all content comes from the feature doc or actual code.
- If the module spans multiple route files (e.g., auth has `/login`, `/register`, `/verify`), cover all of them in one spec.

---

## Rules

- Feature doc is required — stop if you can't find it
- Do NOT include test scenarios — that's `/tdd-plan`'s job
- Do NOT modify any source code — this skill produces SPEC.md only
- Don't invent requirements — derive everything from feature doc or code
- Copy schemas verbatim — never paraphrase field names or types
- After writing, tell the user: "Run `/tdd-plan docs/specs/{module}.SPEC.md` to plan test cases."
