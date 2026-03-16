"""
Botlixio — FastAPI dependency: get_current_user.

Extracts the Bearer token from the Authorization header,
resolves it to a User via AuthService, and injects the User
into any route that depends on it.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService

_bearer = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
):
    """
    FastAPI dependency — decode Bearer JWT and return the authenticated User.

    Raises:
        HTTPException(401) — missing, invalid, or expired token
        HTTPException(403) — account blocked
    """
    token = credentials.credentials
    repo = UserRepository(db)
    service = AuthService(user_repo=repo)
    return await service.get_current_user(token=token)
