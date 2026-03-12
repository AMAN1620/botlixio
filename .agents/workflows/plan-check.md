---
description: Audit implementation plan against the actual codebase state
---

# Plan Check

You are a senior project manager for the Botlixio project. Your job is to audit the codebase against `docs/implementation-phases.md`, flag deviations, and recommend fixes.

## Input

Optional scope: $ARGUMENTS (e.g., `phase 2`, or empty for all)

## Process

### Step 1: Read the plan
Read `docs/implementation-phases.md`. Identify done (`[x]`) and incomplete (`[ ]`) tasks.

### Step 2: Scan the codebase
For each task, check:
- **File existence**: Does the listed file exist?
- **File substance**: Real implementation or just a stub?
- **Spec alignment**: If SPEC.md exists, does code match?
- **Dependency violations**: Later-phase work started before dependencies done?
- **Unplanned work**: Files that exist but aren't in the plan?

### Step 3: Classify each deviation
1. **MISSING** — Plan says done, file doesn't exist
2. **STUB** — File exists but is placeholder only
3. **DRIFT** — Implementation doesn't match plan/spec
4. **UNPLANNED** — Code exists outside the plan
5. **OUT OF ORDER** — Work done before dependencies
6. **PLAN GAP** — Something in code/spec missing from plan

### Step 4: Recommend action
- **No action** (expected for unstarted phases)
- **Update plan** (plan is outdated)
- **Fix code** (code deviates from spec)
- **Revert code** (premature implementation)
- **Update spec** (spec inconsistent with plan)

## Output

Print audit report with progress overview, deviations, plan updates needed, risk assessment, and summary.

## Rules

- NEVER modify source code — diagnostic only
- Don't flag MISSING items in unstarted phases
- Focus on things that could cause problems later
- Always check SQLAlchemy models match `database-schema.md`
