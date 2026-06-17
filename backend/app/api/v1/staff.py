from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import StaffStatus, UserRole
from app.core.database import get_db
from app.core.permissions import require_roles
from app.core.responses import paginated_response, success_response
from app.models.user import User
from app.schemas.common import to_jsonable
from app.schemas.staff import (
    StaffProfileCreate,
    StaffProfileResponse,
    StaffProfileUpdate,
)
from app.services import staff_service

router = APIRouter()


@router.get("")
async def list_staff(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.ADMIN, UserRole.DELIVERY_MANAGER)),
    ],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    role: UserRole | None = None,
    status: StaffStatus | None = None,
) -> dict:
    current_role = getattr(current_user.role, "value", current_user.role)
    if current_role == UserRole.DELIVERY_MANAGER.value:
        role = UserRole.SHIPPER
        status = StaffStatus.ACTIVE

    staff_profiles, total = await staff_service.list_staff_profiles(
        db,
        page,
        page_size,
        role=role,
        status=status,
    )
    return paginated_response(
        items=to_jsonable(
            [
                StaffProfileResponse.model_validate(staff_profile)
                for staff_profile in staff_profiles
            ]
        ),
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{staff_id}")
async def get_staff(
    staff_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> dict:
    staff_profile = await staff_service.get_staff_profile(db, staff_id)
    return success_response(
        data=to_jsonable(StaffProfileResponse.model_validate(staff_profile))
    )


@router.post("")
async def create_staff(
    payload: StaffProfileCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> dict:
    staff_profile = await staff_service.create_staff_profile(
        db,
        payload,
        current_user.id,
    )
    return success_response(
        message="Staff profile created successfully",
        data=to_jsonable(StaffProfileResponse.model_validate(staff_profile)),
    )


@router.put("/{staff_id}")
async def update_staff(
    staff_id: UUID,
    payload: StaffProfileUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> dict:
    staff_profile = await staff_service.update_staff_profile(
        db,
        staff_id,
        payload,
        current_user.id,
    )
    return success_response(
        message="Staff profile updated successfully",
        data=to_jsonable(StaffProfileResponse.model_validate(staff_profile)),
    )


@router.delete("/{staff_id}")
async def delete_staff(
    staff_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> dict:
    staff_profile = await staff_service.delete_staff_profile(
        db,
        staff_id,
        current_user.id,
    )
    return success_response(
        message="Staff profile deleted successfully",
        data=to_jsonable(StaffProfileResponse.model_validate(staff_profile)),
    )
