---
name: plan-check
description: >
  Audits the implementation plan (docs/implementation-phases.md) against the actual
  codebase state. Finds tasks marked done but not actually implemented, code that exists
  outside the plan, dependency order violations, and stubs masquerading as completions.
  Use this skill whenever the user wants to verify plan accuracy, check what's really
  done, find drift between plan and code, or get a reality check on progress. Trigger on:
  "plan-check", "check the plan", "is the plan accurate", "what's actually done",
  "verify implementation status", "find plan drift".
---

# Plan Check

Audits `docs/implementation-phases.md` against the actual codebase. Flags deviations and
recommends fixes — diagnostic only, never modifies code.

## Scope

`$ARGUMENTS` — optional: `phase 2`, `phase 3`, etc. to limit to a specific phase.
Default: audit all phases.

---

## Process

### 1. Read the plan
Read `docs/implementation-phases.md`. Build two lists: done (`[x]`) and incomplete (`[ ]`).

### 2. Scan the codebase
For each planned task, check:

```bash
# File existence
ls backend/app/api/v1/ backend/app/services/ backend/app/models/ backend/app/schemas/ backend/app/repositories/

# Tests exist
ls backend/tests/unit/ backend/tests/integration/

# File is not a stub (has real content)
wc -l <file>   # stubs are usually < 10 lines
grep -c "pass\|TODO\|NotImplemented\|raise NotImplementedError" <file>
```

Also check:
- **Spec alignment** — if `SPEC.md` exists for a feature, does the code match it?
- **Dependency violations** — is Phase 3 work started before Phase 2 is complete?
- **Unplanned work** — files that exist but aren't in the plan at all

### 3. Classify each deviation

| Type | Meaning |
|---|---|
| **MISSING** | Plan says `[x]` done, file doesn't exist |
| **STUB** | File exists but contains only `pass` / placeholder logic |
| **DRIFT** | Implementation doesn't match plan or SPEC.md |
| **UNPLANNED** | Code exists outside the plan entirely |
| **OUT OF ORDER** | Work done before its dependencies |
| **PLAN GAP** | Something in code/spec not mentioned in plan |

### 4. Recommend action per deviation

| Deviation | Typical recommendation |
|---|---|
| MISSING | Re-implement or uncheck `[x]` |
| STUB | Complete implementation or uncheck `[x]` |
| DRIFT | Fix code to match spec, or update spec with approval |
| UNPLANNED | Add to plan retroactively, or remove if premature |
| OUT OF ORDER | Flag risk — may need to finish dependencies first |
| PLAN GAP | Add missing task to plan |

---

## Output

Print to conversation:

```
# Plan Check Report — {date}
Scope: {all phases | phase N}

## Progress Overview
| Phase | Tasks | Done | Incomplete | Deviations |
|-------|-------|------|------------|-----------|
| Phase 0: Foundation | N | N | N | N |
| Phase 1: Auth | N | N | N | N |
| ...
| **Total** | N | N | N | N |

## Deviations

### [STUB] Phase 1 — `backend/app/services/auth_service.py`
- Plan says: [x] complete
- Reality: file is 8 lines, contains only `pass` statements
- Recommendation: uncheck [x], implement, re-check when tests pass

### [OUT OF ORDER] Phase 3 work started before Phase 2 complete
- `backend/app/services/agent_service.py` exists
- Phase 2 tasks still incomplete: [list them]
- Risk: agent service may depend on incomplete Phase 2 infrastructure

## Risk Assessment
- High: N items (block forward progress)
- Medium: N items (should fix soon)
- Low: N items (cosmetic / minor)

## Recommended Actions
1. {highest priority fix}
2. ...

## Next
Run /docs-sync to check if documentation matches code.
```

---

## Rules

- Never modify source code — diagnostic only
- Don't flag MISSING items in phases that haven't started yet
- Focus on deviations that could cause problems downstream
- Always check SQLAlchemy models match `docs/database-schema.md`
