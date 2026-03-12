---
description: Full TDD pipeline — generate test cases from spec, analyze coverage, write test code, and generate reports
---

# TDD Pipeline

You are a senior test engineer for the Botlixio project. This workflow is the complete TDD pipeline — it takes a SPEC.md and produces test cases, analyzes coverage gaps, generates actual test code, runs the tests, and produces a report. Use the appropriate sub-command based on where you are in the TDD cycle.

## Input

Arguments: $ARGUMENTS

Supported sub-commands:
- `plan <path/to/SPEC.md>` — Generate test cases from a SPEC.md → writes TEST-CASES.md
- `analyze <path/to/SPEC.md>` — Analyze coverage gaps between SPEC.md and TEST-CASES.md → writes COVERAGE-ANALYSIS.md
- `generate <path/to/TEST-CASES.md>` — Generate actual pytest test code from TEST-CASES.md
- `report` — Run all tests and produce an HTML report
- `full <path/to/SPEC.md>` — Run the entire pipeline: plan → analyze → generate → report

If no sub-command given, ask the user which step to run.

---

## Sub-Command: `plan`

### Purpose
Read a SPEC.md and produce a structured test case document (descriptions only, NOT code).

### Process

1. Read the SPEC.md file completely
2. Extract all testable scenarios from:
   - **Happy flows** — each step with an observable outcome
   - **Edge cases** — each row in the edge cases table = at least one test case
   - **API contracts** — each endpoint + each response code = one test case
   - **Pydantic schemas** — each field validation rule (regex, min, max, required)
   - **Business rules** — any rule stated in prose (e.g., "only ADMIN can access")
3. Categorize each test case by layer:
   - **Unit** — pure logic, schema validation, utility functions (pytest)
   - **Service** — service functions with mocked repositories (pytest)
   - **API** — route handlers with mocked services (pytest + httpx.AsyncClient)
4. For each test case, define:
   - **ID**: `{LAYER}-{FEATURE}-{NNN}` (e.g., `UNIT-AUTH-001`, `SVC-AGENT-003`, `API-CHAT-007`)
   - **Title**: Short description
   - **Preconditions**: What must be true before the test runs
   - **Steps**: Numbered actions
   - **Expected Result**: Observable outcome
   - **Priority**: P0 (blocks release), P1 (important), P2 (nice to have)

### Output
Write to the same directory as the SPEC.md, named `TEST-CASES.md`.

```markdown
# Test Cases: {Feature Name}

Generated from: `{path/to/SPEC.md}`
Generated on: {date}

## Summary

| Layer | Count | P0 | P1 | P2 |
|-------|-------|----|----|-----|
| Unit  |       |    |    |     |
| Service |     |    |    |     |
| API   |       |    |    |     |
| **Total** |   |    |    |     |

---

## Unit Tests

### UNIT-{FEATURE}-001: {Title}
- **Priority**: P0
- **Preconditions**: None
- **Steps**:
  1. Call `function_name` with input X
- **Expected**: Returns Y

## Service Tests
(same format)

## API Tests
(same format)
```

### Rules for Lean Test Cases
- **Consolidate related scenarios** into one test case when they share setup (e.g., "schema rejects invalid email AND invalid password formats" = ONE test case)
- **Skip testing framework defaults** — Pydantic's `min_length`, `email` validators don't need individual tests. Focus on custom validators, `.model_validator()`, and conditional logic.
- **One test case per distinct behaviour**, not per input value
- **Auth/security tests are always P0**
- Mark all categories: P0 = security + data integrity, P1 = core flows, P2 = nice-to-have

---

## Sub-Command: `analyze`

### Purpose
Verify that every testable requirement in a SPEC.md has a matching test case in TEST-CASES.md.

### Process

1. **Extract all testable requirements from SPEC.md** and assign each a reference ID:
   `SPEC-{SECTION}-{NNN}` (e.g., `SPEC-EDGE-003`, `SPEC-API-007`)

   Sources:
   - Happy flows → each step with an observable outcome
   - Edge cases → each row
   - API contracts → each endpoint + each response code
   - Pydantic schemas → each custom validation rule
   - Business rules → each stated rule

2. **Map TEST-CASES.md back to SPEC requirements** — for each test case, identify which SPEC requirement(s) it covers

3. **Gap analysis** — produce three lists:
   - **Uncovered**: SPEC requirements with zero matching test cases
   - **Weakly covered**: Test case exists but doesn't fully verify the requirement
   - **Orphaned**: Test cases that don't map to any SPEC requirement

4. **Risk assessment** for each gap:
   - **Critical** — auth, security, data integrity, billing
   - **High** — core user flows, validation preventing bad data
   - **Medium** — error messages, edge cases with workarounds
   - **Low** — cosmetic, non-functional

### Output
Write `COVERAGE-ANALYSIS.md` in the same directory as the SPEC.md.

```markdown
# Coverage Analysis: {Feature Name}

**Spec**: `{path/to/SPEC.md}`
**Test Cases**: `{path/to/TEST-CASES.md}`
**Analyzed on**: {date}

## Coverage Summary

| Category | Total Reqs | Covered | Weakly Covered | Uncovered |
|----------|-----------|---------|----------------|-----------|
| Happy Flow |          |         |                |           |
| Edge Cases |          |         |                |           |
| API Contracts |       |         |                |           |
| Schema Validations |  |         |                |           |
| Business Rules |      |         |                |           |
| **Total** |           |         |                |           |

**Overall Coverage**: {covered / total}%

## Uncovered Requirements (Gaps)
| Ref | Risk | Section | Requirement | Suggested Test |

## Weakly Covered Requirements
| Ref | Risk | Requirement | Test Case ID | What's Missing |

## Orphaned Test Cases
| Test Case ID | Title | Recommendation |

## Full Traceability Matrix
| SPEC Ref | Requirement (short) | Test Case ID(s) | Status |
```

---

## Sub-Command: `generate`

### Purpose
Transform TEST-CASES.md into actual runnable pytest test code.

### Context
Before generating, read these project files for patterns:
- `backend/tests/conftest.py` — shared fixtures
- Any existing test files to follow established patterns

Also read the corresponding SPEC.md for Pydantic schemas, API contracts, and service function signatures.

### Output File Paths
- Unit tests: `backend/tests/unit/test_{feature}.py`
- Service tests: `backend/tests/unit/test_{feature}_service.py`
- API tests: `backend/tests/integration/test_{feature}_api.py`

### Test Patterns

```python
# Unit test — pure functions
import pytest
from app.core.security import hash_password, verify_password

class TestHashPassword:
    def test_returns_hash_different_from_input(self):  # UNIT-AUTH-001
        hashed = hash_password("mypassword123")
        assert hashed != "mypassword123"
        assert len(hashed) > 50

# Service test — mock repository
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.auth_service import AuthService

class TestAuthService:
    @pytest.fixture
    def mock_user_repo(self):
        repo = AsyncMock()
        repo.get_by_email.return_value = None  # no existing user
        return repo

    @pytest.fixture
    def service(self, mock_user_repo):
        return AuthService(user_repo=mock_user_repo)

    async def test_register_creates_user(self, service, mock_user_repo):  # SVC-AUTH-001
        result = await service.register(email="test@example.com", password="pass1234", full_name="Test")
        mock_user_repo.create.assert_called_once()

# API test — httpx.AsyncClient
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

class TestAuthAPI:
    @pytest.fixture
    def client(self):
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    async def test_register_success(self, client):  # API-AUTH-001
        response = await client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User"
        })
        assert response.status_code == 201
```

### Code Style Rules
- Use `class TestFeatureName` grouping with methods
- Add test case ID as a comment: `# UNIT-AUTH-001`
- Import paths use full module paths: `from app.services.auth_service import AuthService`
- Write tests as if implementation does NOT exist yet (TDD)
- Group P0 tests first within each class

---

## Sub-Command: `report`

### Purpose
Run the test suite and produce a readable summary.

### Process

1. **Run tests**:
   ```bash
   cd backend && python -m pytest --tb=short -v 2>&1
   ```

2. **Parse results**: Extract total, passed, failed, skipped, duration

3. **For each failure**: Extract test file, test name, error message, assertion

4. **Cross-reference with TEST-CASES.md** (if exists): Map tests to IDs, find gaps

5. **Print report** to conversation:

```
# Test Report

**Date**: {date}
**Duration**: {time}

## Summary
| Status | Count |
|--------|-------|
| ✅ Passed | {N} |
| ❌ Failed | {N} |
| ⏭️ Skipped | {N} |
| **Total** | {N} |
| **Pass Rate** | {N}% |

## Failed Tests
### 1. {test_file}::{test_name}
- **Error**: {assertion message}
- **Probable Cause**: {brief analysis}
- **Suggested Fix**: {actionable suggestion}

## Coverage by Module
| Module | Unit | Service | API | Total |
|--------|------|---------|-----|-------|
| Auth   |      |         |     |       |
| Agent  |      |         |     |       |

## Missing Coverage
- {list of features with no tests}

## Recommendations
1. {highest priority action}
2. {second}
3. {third}
```

---

## Sub-Command: `full`

Run the entire pipeline in sequence:
1. `plan` → generates TEST-CASES.md
2. `analyze` → generates COVERAGE-ANALYSIS.md
3. If Critical gaps found → update TEST-CASES.md first
4. `generate` → generates test files
5. Verify tests fail (RED phase confirmation)
6. Print summary of what was created

---

## Global Rules

- **Read BOTH files completely** before analysis — don't stream partial results
- **Be strict about coverage** — a test case only "covers" a requirement if it actually verifies the stated behaviour
- **Do NOT write implementation code** — this workflow produces only test-related files
- **Do NOT modify SPEC.md** — it's the source of truth
- **Each test case ID must appear in exactly one test** function/method
- **Tests must be runnable immediately** — correct imports, no placeholder logic
- **When in doubt, test it** — err on the side of more coverage for auth, billing, and data integrity
