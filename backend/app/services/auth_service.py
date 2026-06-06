from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import UserStatus
from app.core.exceptions import AuthenticationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repo import get_user_by_email, get_user_by_id
from app.schemas.auth import AuthUser, LoginRequest, RefreshTokenRequest, TokenResponse


async def login(db: AsyncSession, payload: LoginRequest) -> TokenResponse:
    user = await get_user_by_email(db, payload.email)
    if (
        user is None
        or user.status != UserStatus.ACTIVE
        or not verify_password(payload.password, user.hashed_password)
    ):
        raise AuthenticationError("Invalid email or password")

    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)

    return _build_token_response(user)


async def refresh_access_token(
    db: AsyncSession,
    payload: RefreshTokenRequest,
) -> TokenResponse:
    token_payload = decode_token(payload.refresh_token)
    if token_payload.get("type") != "refresh":
        raise AuthenticationError()

    try:
        user_id = UUID(token_payload["sub"])
    except (TypeError, ValueError) as exc:
        raise AuthenticationError() from exc

    user = await get_user_by_id(db, user_id)
    if user is None or user.status != UserStatus.ACTIVE:
        raise AuthenticationError()

    return _build_token_response(user)


def _build_token_response(user: User) -> TokenResponse:
    role = getattr(user.role, "value", user.role)
    return TokenResponse(
        access_token=create_access_token(user.id, role),
        refresh_token=create_refresh_token(user.id),
        user=AuthUser.model_validate(user),
    )
