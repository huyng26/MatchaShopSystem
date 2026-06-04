from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import get_current_user
from app.core.responses import success_response
from app.models.user import User
from app.schemas.auth import AuthUser, LoginRequest, RefreshTokenRequest
from app.schemas.common import to_jsonable
from app.services import auth_service

router = APIRouter()


@router.post("/token")
async def token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    token_response = await auth_service.login(
        db,
        LoginRequest(email=form_data.username, password=form_data.password),
    )
    return token_response.model_dump(mode="json")


@router.post("/login")
async def login(
    payload: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    token_response = await auth_service.login(db, payload)
    return success_response(
        message="Login successfully",
        data=to_jsonable(token_response),
    )


@router.post("/refresh")
async def refresh_token(
    payload: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    token_response = await auth_service.refresh_access_token(db, payload)
    return success_response(
        message="Token refreshed successfully",
        data=to_jsonable(token_response),
    )


@router.get("/me")
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> dict:
    return success_response(data=to_jsonable(AuthUser.model_validate(current_user)))
