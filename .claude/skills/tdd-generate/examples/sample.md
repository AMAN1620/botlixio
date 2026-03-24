# Example — Real test code from this project

Extracted from `backend/tests/unit/test_security.py`. Shows the expected style.

---

## Unit test (pure function)

```python
"""
Unit tests for app.core.security — password hashing + JWT.

TDD RED phase: security.py does NOT exist yet. All tests will fail.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from fastapi import HTTPException


class TestPasswordHashing:
    """UNIT-SEC-001, UNIT-SEC-002, UNIT-SEC-003"""

    def test_hash_is_different_from_input(self) -> None:  # UNIT-SEC-001
        from app.core.security import hash_password

        hashed = hash_password("mypassword123")
        assert hashed != "mypassword123"
        assert len(hashed) > 50  # bcrypt hashes are 60 chars

    def test_verify_correct_password_returns_true(self) -> None:  # UNIT-SEC-002
        from app.core.security import hash_password, verify_password

        hashed = hash_password("mypassword123")
        assert verify_password("mypassword123", hashed) is True

    def test_verify_wrong_password_returns_false(self) -> None:  # UNIT-SEC-003
        from app.core.security import hash_password, verify_password

        hashed = hash_password("mypassword123")
        assert verify_password("wrongpassword", hashed) is False

    def test_two_hashes_of_same_password_are_different(self) -> None:
        """bcrypt uses random salt — same input must not produce same hash."""
        from app.core.security import hash_password

        h1 = hash_password("mypassword123")
        h2 = hash_password("mypassword123")
        assert h1 != h2
```

## Key patterns to follow

- Imports inside test methods (RED-phase pattern)
- `class Test{Feature}:` grouping with docstring listing test case IDs
- Test case ID as trailing comment: `# UNIT-SEC-001`
- Type hints on test methods: `-> None`
- Concrete assertions (not just "no error")
- No fixtures needed for pure functions
