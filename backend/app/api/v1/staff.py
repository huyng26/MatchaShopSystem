from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import StaffStatus, TaskStatus, UserRole
from app.core.database import get_db
from app.core.permissions import require_roles
from app.core.responses import paginated_response, success_response
from app.models.user import User
from app.schemas.common import to_jsonable
from app.schemas.staff import (
    StaffProfileCreate,
    StaffProfileResponse,
    StaffProfileUpdate,
    StaffTaskCreate,
    StaffTaskResponse,
    StaffTaskUpdate,
)
from app.services import staff_service

router = APIRouter()


@router.get("")
async def list_staff(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    role: UserRole | None = None,
    status: StaffStatus | None = None,
) -> dict:
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


@router.get("/tasks")
async def list_staff_tasks(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    staff_id: UUID | None = None,
    status: TaskStatus | None = None,
) -> dict:
    tasks, total = await staff_service.list_staff_tasks(
        db,
        page,
        page_size,
        staff_id=staff_id,
        status=status,
    )
    return paginated_response(
        items=to_jsonable([StaffTaskResponse.model_validate(task) for task in tasks]),
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/tasks")
async def create_staff_task(
    payload: StaffTaskCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> dict:
    task = await staff_service.create_staff_task(db, payload, current_user.id)
    return success_response(
        message="Staff task created successfully",
        data=to_jsonable(StaffTaskResponse.model_validate(task)),
    )


@router.get("/tasks/{task_id}")
async def get_staff_task(
    task_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> dict:
    task = await staff_service.get_staff_task(db, task_id)
    return success_response(data=to_jsonable(StaffTaskResponse.model_validate(task)))


@router.put("/tasks/{task_id}")
async def update_staff_task(
    task_id: UUID,
    payload: StaffTaskUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> dict:
    task = await staff_service.update_staff_task(
        db,
        task_id,
        payload,
        current_user.id,
    )
    return success_response(
        message="Staff task updated successfully",
        data=to_jsonable(StaffTaskResponse.model_validate(task)),
    )


@router.delete("/tasks/{task_id}")
async def delete_staff_task(
    task_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN))],
) -> dict:
    task = await staff_service.delete_staff_task(db, task_id, current_user.id)
    return success_response(
        message="Staff task deleted successfully",
        data=to_jsonable(StaffTaskResponse.model_validate(task)),
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
