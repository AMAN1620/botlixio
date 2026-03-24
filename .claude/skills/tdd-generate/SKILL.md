---
name: tdd-generate
description: >
  Writes runnable pytest code from a TEST-CASES.md file. Reads test cases,
  examines existing test files and conftest.py for style reference, then
  generates unit, service, and integration test files following the project's
  patterns. Use after tdd-plan has produced test cases. Trigger on: "generate
  tests", "write the pytest code", "tdd generate", "create test files from
  test cases", "turn test cases into code", or when the user has a
  TEST-CASES.md and wants actual pytest files.
---

# TDD Generate — Write Pytest Code from Test Cases

Read a TEST-CASES.md and produce runnable pytest files matching the project's style.

## Input

`$ARGUMENTS` — path to a TEST-CASES.md file (e.g., `docs/tdd/auth.TEST-CASES.md`).

If no path given, ask the user.

---

## Step 1 — Discover project layout

```bash
find . -type d -name "tests" | head -5
cat pytest.ini 2>/dev/null || grep -A5 "\[tool.pytest" pyproject.toml 2>/dev/null
ls backend/app/ 2>/dev/null || ls app/ 2>/dev/null || ls src/ 2>/dev/null
```

---

## Step 2 — Read style references (before writing anything)

Read these files to learn the project's test conventions:

1. **`tests/conftest.py`** — fixtures, async setup, factory patterns
2. **1-2 existing test files** — class structure, import style, assertion patterns
3. **The SPEC.md** (in `docs/specs/`) — schemas, function signatures, endpoint paths. Extract the feature name from the TEST-CASES filename and look for `docs/specs/{feature}.SPEC.md`.

Adapt to what you find. If existing tests use `class TestX:` grouping, use that. If they use bare functions, use that.

---

## Step 3 — Plan output files

Map test case layers to files (adapt paths to discovered structure):

| Layer | Output file |
|-------|-------------|
| `UNIT-*` | `tests/unit/test_{feature}.py` |
| `SVC-*` | `tests/unit/test_{feature}_service.py` |
| `API-*` | `tests/integration/test_{feature}_api.py` |

If a file already exists, **append new tests** — do not overwrite existing tests. Read the file first and add only missing test cases.

---

## Step 4 — Write the test code

For each test case in TEST-CASES.md, write a real, runnable test.

### Unit test pattern

```python
class TestHashPassword:
    """UNIT-AUTH-001, UNIT-AUTH-002"""

    def test_hash_is_different_from_input(self) -> None:  # UNIT-AUTH-001
        from app.core.security import hash_password

        hashed = hash_password("mypassword123")
        assert hashed != "mypassword123"
        assert len(hashed) > 50
```

### Service test pattern

```python
class TestAuthServiceRegister:
    """SVC-AUTH-001 through SVC-AUTH-005"""

    @pytest.fixture
    def user_repo(self):
        repo = AsyncMock()
        repo.get_by_email.return_value = None
        return repo

    @pytest.fixture
    def svc(self, user_repo):
        return AuthService(user_repo=user_repo)

    @pytest.mark.asyncio
    async def test_register_creates_user(self, svc, user_repo):  # SVC-AUTH-001
        await svc.register(email="a@b.com", password="pass1234")
        user_repo.create.assert_called_once()
```

### API test pattern

```python
class TestAuthAPI:
    """API-AUTH-001 through API-AUTH-010"""

    @pytest.mark.asyncio
    async def test_register_201(self, client):  # API-AUTH-001
        r = await client.post("/api/v1/auth/register",
                              json={"email": "a@b.com", "password": "pass1234"})
        assert r.status_code == 201
```

For real examples from this project, see [examples/sample.md](examples/sample.md).

---

## Step 5 — Validate the output

After writing all files, run a syntax check:

```bash
python -m py_compile tests/unit/test_{feature}.py
python -m py_compile tests/unit/test_{feature}_service.py
python -m py_compile tests/integration/test_{feature}_api.py
```

If any file fails to compile, fix the syntax error immediately.

---

## Gotchas

- Import the function under test **inside the test method** (not at module top) for RED-phase TDD. This way the test fails with `ImportError` when the implementation doesn't exist yet, which is the expected RED behavior.
- Use `AsyncMock` (not `Mock`) for any async repository or service method.
- Check `conftest.py` for existing fixtures before creating new ones. Don't duplicate a `client` fixture that already exists.
- P0 tests go first in the file. Group by class, order by priority within each class.
- Add the test case ID as a trailing comment on the test method line (e.g., `# SVC-AUTH-001`).
- Use `@pytest.mark.asyncio` on every async test. Check if the project uses `asyncio_mode = "auto"` in pytest config — if so, the decorator isn't needed.
- Never write placeholder tests with `pass` or `pytest.skip`. Every test must have real assertions.

---

## Rules

- Read existing tests and conftest before writing — match the style exactly
- Do NOT write implementation code — only test files
- Do NOT modify TEST-CASES.md or SPEC.md
- Every test must be runnable immediately (no `TODO`, no `pass`, no `skip`)
- If appending to an existing file, preserve all existing tests
- Test the exact behavior described in the test case — don't add extra assertions or test more than stated
