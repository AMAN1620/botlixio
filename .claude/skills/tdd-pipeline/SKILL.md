---
name: tdd-pipeline
description: >
  Full TDD (Test-Driven Development) pipeline for Python/FastAPI projects. Generates
  structured test cases from a SPEC.md, analyzes coverage gaps, writes runnable pytest
  code, and produces test reports. Use this skill whenever the user wants to write tests
  before implementation, generate test cases from a spec or feature doc, check test
  coverage gaps, produce pytest files from a test plan, or run tests and get a structured
  report. Trigger on: "write tests first", "TDD pipeline", "generate test cases for X",
  "what tests do I need", "check my coverage", "run the test pipeline",
  "red-green-refactor", or when the user shares a spec and asks how to test it.
---

# TDD Pipeline

Complete TDD pipeline: spec → test cases → coverage analysis → pytest code → test report.

## Sub-commands

Pass as `$ARGUMENTS`:

| Sub-command | What it does | Output |
|---|---|---|
| `plan <SPEC.md>` | Extract test cases from spec | `TEST-CASES.md` |
| `analyze <SPEC.md>` | Gap analysis: spec vs test cases | `COVERAGE-ANALYSIS.md` |
| `generate <TEST-CASES.md>` | Write runnable pytest code | test `.py` files |
| `report` | Run tests, produce summary | printed report |
| `full <SPEC.md>` | All of the above in sequence | all outputs |

If no sub-command given, ask the user which step to run.

---

## Detecting project structure (do this first, every time)

Before writing any paths, discover the actual project layout:

```bash
# Find pytest config
cat pytest.ini 2>/dev/null || grep -A5 "\[tool.pytest" pyproject.toml 2>/dev/null

# Find test directories
find . -type d -name "tests" -o -name "test" | head -10

# Find the import root (package name)
ls backend/app/ 2>/dev/null || ls src/ 2>/dev/null || ls app/ 2>/dev/null
```

Use discovered paths throughout — never hardcode `backend/tests/` or `app/`.

---

## `plan` — Generate TEST-CASES.md from a spec

Read the spec completely, then extract:

- **Happy flows** → one test case per observable outcome
- **Edge cases** → one test case per table row
- **API contracts** → one test case per endpoint × response code
- **Schema validations** → focus on custom validators and conditional logic (skip framework defaults like `min_length`)
- **Business rules** → one test case per stated rule

**Test case format:**

```markdown
### {LAYER}-{FEATURE}-{NNN}: {Short title}
- **Priority**: P0 | P1 | P2
- **Preconditions**: what must be true
- **Steps**: numbered actions
- **Expected**: observable outcome
```

Layer prefixes: `UNIT` (pure logic), `SVC` (service + mocked repo), `API` (route + mocked service)

Priority: P0 = auth/security/data integrity · P1 = core flows · P2 = nice-to-have

**Output file:** `TEST-CASES.md` in the same directory as the spec.

Summary table at top:

```markdown
| Layer | Count | P0 | P1 | P2 |
|-------|-------|----|----|-----|
| Unit  |       |    |    |     |
| Service |     |    |    |     |
| API   |       |    |    |     |
```

---

## `analyze` — Coverage gap analysis

Map every testable requirement in the spec to test cases in TEST-CASES.md.

**Assign each spec requirement a ref:** `SPEC-{SECTION}-{NNN}`

**Produce three lists:**
- **Uncovered** — spec requirement with no test case
- **Weakly covered** — test exists but doesn't fully verify the requirement
- **Orphaned** — test case not tied to any spec requirement

**Risk per gap:** Critical (auth/billing/data) · High (core flows) · Medium (error messages) · Low (cosmetic)

**Output file:** `COVERAGE-ANALYSIS.md` in the same directory as the spec.

Key table:

```markdown
| Category | Total | Covered | Weakly | Uncovered |
|----------|-------|---------|--------|-----------|
| Happy Flow |     |         |        |           |
| Edge Cases |     |         |        |           |
| API Contracts |  |         |        |           |
| Business Rules | |         |        |           |
```

---

## `generate` — Write pytest code from TEST-CASES.md

Read before writing:
- `tests/conftest.py` (or discovered equivalent) — fixtures
- 1–2 existing test files — style reference
- The SPEC.md — schemas and signatures

**Output paths** (adapt to discovered structure):
- `tests/unit/test_{feature}.py` — unit tests
- `tests/unit/test_{feature}_service.py` — service tests
- `tests/integration/test_{feature}_api.py` — API tests

**Patterns:**

```python
# Unit — pure function
class TestHashPassword:
    def test_returns_bcrypt_hash(self):  # UNIT-AUTH-001
        result = hash_password("secret123")
        assert result != "secret123" and len(result) > 50

# Service — mock the repository
class TestAuthService:
    @pytest.fixture
    def user_repo(self):
        repo = AsyncMock()
        repo.get_by_email.return_value = None
        return repo

    @pytest.fixture
    def svc(self, user_repo):
        return AuthService(user_repo=user_repo)

    async def test_register_creates_user(self, svc, user_repo):  # SVC-AUTH-001
        await svc.register(email="a@b.com", password="pass1234")
        user_repo.create.assert_called_once()

# API — httpx AsyncClient
class TestAuthAPI:
    async def test_register_201(self, client):  # API-AUTH-001
        r = await client.post("/api/v1/auth/register",
                              json={"email": "a@b.com", "password": "pass1234"})
        assert r.status_code == 201
```

**Rules:** Group by `class Test{Feature}` · Add test ID as comment · P0 tests first · No placeholder logic — must be runnable immediately.

---

## `report` — Run tests and summarise

```bash
python -m pytest --tb=short -v 2>&1
```

Print to conversation:

```
## Test Report — {date}

| Status | Count |
|--------|-------|
| ✅ Passed | N |
| ❌ Failed | N |
| ⏭️ Skipped | N |
| Pass Rate | N% |

## Failures
### {file}::{test}
- Error: {message}
- Probable cause: {analysis}
- Fix: {actionable suggestion}

## Coverage gaps
- {features with no tests}

## Recommendations
1. {highest priority}
```

---

## `full` — Complete pipeline

Run in order:
1. `plan` → TEST-CASES.md
2. `analyze` → COVERAGE-ANALYSIS.md · if Critical gaps found, update TEST-CASES.md first
3. `generate` → test files
4. Verify RED phase: `python -m pytest {new files} -v` — tests should fail
5. Print summary of all files created

---

## Rules

- Read the spec completely before extracting anything — don't stream partial reads
- A test only "covers" a requirement if it actually verifies the stated behaviour — be strict
- Do NOT write implementation code — only test files
- Do NOT modify the spec — it is the source of truth
- Err toward more coverage for auth, billing, and data integrity
