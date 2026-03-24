# Implementation Checklist — {feature}

## Prerequisites
- [ ] SPEC exists: `docs/specs/{feature}.SPEC.md`
- [ ] TEST-CASES exist: `docs/tdd/{feature}.TEST-CASES.md`
- [ ] Pytest files exist: `backend/tests/unit/test_{feature}.py`
- [ ] RED phase confirmed (tests fail with ImportError)

## Files Created/Modified
- [ ] `backend/app/models/{feature}.py` — SQLAlchemy model
- [ ] `backend/app/schemas/{feature}.py` — Pydantic schemas
- [ ] `backend/app/repositories/{feature}_repo.py` — data access
- [ ] `backend/app/services/{feature}_service.py` — business logic
- [ ] `backend/app/api/v1/{feature}.py` — route handlers

## Verification
- [ ] Feature tests pass (GREEN)
- [ ] Full test suite passes (no regressions)
- [ ] Plan updated: `docs/implementation-phases.md`

## Next Steps
- Run `/tdd-report` for full HTML report
- Run `/tdd-implement` for next task
