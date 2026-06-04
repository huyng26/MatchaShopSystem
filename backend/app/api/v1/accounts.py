from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import UserRole, UserStatus
from app.core.database import get_db
from app.core.permissions import require_roles
from app.core.responses import paginated_response, success_response
from app.models.user import User
from app.schemas.account import UserCreate, UserResponse, UserUpdate
from app.schemas.common import to_jsonable
from app.services import account_service

router = APIRouter()


@router.get("")
async def list_accounts(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    role: UserRole | None = None,
    status: UserStatus | None = None,
) -> dict:
    users, total = await account_service.list_accounts(
        db,
        page,
        page_size,
        role=role,
        status=status,
    )
    return paginated_response(
        items=to_jsonable([UserResponse.model_validate(user) for user in users]),
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{user_id}")
async def get_account(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> dict:
    user = await account_service.get_account(db, user_id)
    return success_response(data=to_jsonable(UserResponse.model_validate(user)))


@router.post("")
async def create_account(
    payload: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> dict:
    user = await account_service.create_account(db, payload, current_user.id)
    return success_response(
        message="Account created successfully",
        data=to_jsonable(UserResponse.model_validate(user)),
    )


@router.put("/{user_id}")
async def update_account(
    user_id: UUID,
    payload: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> dict:
    user = await account_service.update_account(
        db,
        user_id,
        payload,
        current_user.id,
    )
    return success_response(
        message="Account updated successfully",
        data=to_jsonable(UserResponse.model_validate(user)),
    )


@router.delete("/{user_id}")
async def delete_account(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> dict:
    user = await account_service.delete_account(db, user_id, current_user.id)
    return success_response(
        message="Account deleted successfully",
        data=to_jsonable(UserResponse.model_validate(user)),
    )
