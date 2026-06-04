from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import UserRole, UserStatus
from app.core.database import get_db
from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.core.security import decode_token
from app.models.user import User
from app.repositories.user_repo import get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise AuthenticationError()

    try:
        user_id = UUID(payload["sub"])
    except (TypeError, ValueError) as exc:
        raise AuthenticationError() from exc

    user = await get_user_by_id(db, user_id)
    if user is None or user.status != UserStatus.ACTIVE:
        raise AuthenticationError()

    return user


def require_roles(*roles: UserRole) -> Callable:
    allowed_roles = {role.value for role in roles}

    async def dependency(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        current_role = getattr(current_user.role, "value", current_user.role)
        if current_role not in allowed_roles:
            raise PermissionDeniedError()
        return current_user

    return dependency
