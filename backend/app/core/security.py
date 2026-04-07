"""
Botlixio — Security utilities: password hashing + JWT.

Functions:
  - hash_password / verify_password   — bcrypt via passlib
  - create_access_token               — 30-min JWT
  - create_refresh_token              — 7-day JWT
  - decode_token                      — verify + decode, raises 401 on failure
  - hash_refresh_token                — SHA-256 for DB storage of refresh tokens
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password ────────────────────────────────────────────────────────────────


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt (cost 12)."""
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the bcrypt hash, False otherwise."""
    return _pwd_context.verify(plain, hashed)


# ── JWT ─────────────────────────────────────────────────────────────────────


def create_access_token(user_id: str, role: str) -> str:
    """
    Create a short-lived access JWT.

    Payload: { sub, role, type='access', exp }
    Expiry:  ACCESS_TOKEN_EXPIRE_MINUTES (default 30)
    """
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "jti": str(uuid.uuid4()),
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """
    Create a long-lived refresh JWT.

    Payload: { sub, type='refresh', exp }
    Expiry:  REFRESH_TOKEN_EXPIRE_DAYS (default 7)
    """
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {
        "sub": user_id,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and verify a JWT.

    Raises:
        HTTPException(401) — expired, tampered, or malformed token
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── Refresh token hashing ────────────────────────────────────────────────────


def hash_refresh_token(token: str) -> str:
    """
    Produce a SHA-256 hex digest of the refresh token.

    This hash is stored in users.refresh_token_hash — never the raw token.
    SHA-256 is sufficient here because refresh tokens are long random JWTs
    (computationally hard to reverse), so slow bcrypt is unnecessary.
    """
    return hashlib.sha256(token.encode()).hexdigest()


# ── Token generation ────────────────────────────────────────────────────────


def generate_token() -> str:
    """Generate a cryptographically random 64-char hex token (32 bytes)."""
    return secrets.token_hex(32)
