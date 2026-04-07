"""
Unit tests for auth-extended token generation utility.

UNIT-EXT-001, UNIT-EXT-002
"""

import pytest


class TestGenerateToken:
    """UNIT-EXT-001, UNIT-EXT-002"""

    def test_returns_64_char_hex_string(self) -> None:  # UNIT-EXT-001
        from app.core.security import generate_token

        token = generate_token()
        assert len(token) == 64
        assert all(c in "0123456789abcdef" for c in token)

    def test_produces_unique_values(self) -> None:  # UNIT-EXT-002
        from app.core.security import generate_token

        token_a = generate_token()
        token_b = generate_token()
        assert token_a != token_b
