from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import StaffStatus
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.audit import AuditLog
from app.models.staff import StaffProfile, StaffTask
from app.repositories import staff_repo, user_repo
from app.schemas.staff import (
    StaffProfileCreate,
    StaffProfileUpdate,
    StaffTaskCreate,
    StaffTaskUpdate,
)


async def list_staff_profiles(
    db: AsyncSession,
    page: int,
    page_size: int,
    role=None,
    status=None,
) -> tuple[list[StaffProfile], int]:
    offset = (page - 1) * page_size
    staff = await staff_repo.list_staff_profiles(
        db,
        offset,
        page_size,
        role=role,
        status=status,
    )
    total = await staff_repo.count_staff_profiles(db, role=role, status=status)
    return staff, total


async def get_staff_profile(db: AsyncSession, staff_id: UUID) -> StaffProfile:
    staff_profile = await staff_repo.get_staff_profile_by_id(db, staff_id)
    if staff_profile is None:
        raise NotFoundError("Staff profile not found")
    return staff_profile


async def create_staff_profile(
    db: AsyncSession,
    payload: StaffProfileCreate,
    actor_user_id: UUID | None,
) -> StaffProfile:
    await _validate_staff_uniqueness(db, payload.email, payload.phone)
    await _validate_user_link(db, payload.user_id, payload.role)

    staff_profile = StaffProfile(**payload.model_dump())
    staff_repo.add_staff_profile(db, staff_profile)
    await db.flush()
    _add_audit_log(
        db,
        actor_user_id,
        "staff_profile.created",
        "staff_profiles",
        staff_profile.id,
        new_value=_staff_audit_value(staff_profile),
    )
    await db.commit()
    await db.refresh(staff_profile)
    return staff_profile


async def update_staff_profile(
    db: AsyncSession,
    staff_id: UUID,
    payload: StaffProfileUpdate,
    actor_user_id: UUID | None,
) -> StaffProfile:
    staff_profile = await get_staff_profile(db, staff_id)
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return staff_profile

    next_email = update_data.get("email", staff_profile.email)
    next_phone = update_data.get("phone", staff_profile.phone)
    await _validate_staff_uniqueness(
        db,
        next_email,
        next_phone,
        current_staff_id=staff_profile.id,
    )

    next_role = update_data.get("role", staff_profile.role)
    if "user_id" in update_data:
        await _validate_user_link(
            db,
            update_data["user_id"],
            next_role,
            current_staff_id=staff_profile.id,
        )
    elif staff_profile.user_id is not None and "role" in update_data:
        await _validate_user_link(
            db,
            staff_profile.user_id,
            next_role,
            current_staff_id=staff_profile.id,
        )

    old_value = _staff_audit_value(staff_profile)
    for field, value in update_data.items():
        setattr(staff_profile, field, value)

    _add_audit_log(
        db,
        actor_user_id,
        "staff_profile.updated",
        "staff_profiles",
        staff_profile.id,
        old_value=old_value,
        new_value=_staff_audit_value(staff_profile),
    )
    await db.commit()
    await db.refresh(staff_profile)
    return staff_profile


async def delete_staff_profile(
    db: AsyncSession,
    staff_id: UUID,
    actor_user_id: UUID | None,
) -> StaffProfile:
    staff_profile = await get_staff_profile(db, staff_id)
    old_value = _staff_audit_value(staff_profile)
    staff_profile.status = StaffStatus.INACTIVE
    staff_profile.deleted_at = datetime.now(timezone.utc)
    _add_audit_log(
        db,
        actor_user_id,
        "staff_profile.deleted",
        "staff_profiles",
        staff_profile.id,
        old_value=old_value,
        new_value=_staff_audit_value(staff_profile),
    )
    await db.commit()
    await db.refresh(staff_profile)
    return staff_profile


async def list_staff_tasks(
    db: AsyncSession,
    page: int,
    page_size: int,
    staff_id: UUID | None = None,
    status=None,
) -> tuple[list[StaffTask], int]:
    offset = (page - 1) * page_size
    tasks = await staff_repo.list_staff_tasks(
        db,
        offset,
        page_size,
        staff_id=staff_id,
        status=status,
    )
    total = await staff_repo.count_staff_tasks(db, staff_id=staff_id, status=status)
    return tasks, total


async def get_staff_task(db: AsyncSession, task_id: UUID) -> StaffTask:
    task = await staff_repo.get_staff_task_by_id(db, task_id)
    if task is None:
        raise NotFoundError("Staff task not found")
    return task


async def create_staff_task(
    db: AsyncSession,
    payload: StaffTaskCreate,
    actor_user_id: UUID,
) -> StaffTask:
    await _require_staff_profile(db, payload.staff_id)

    task = StaffTask(**payload.model_dump(), created_by=actor_user_id)
    staff_repo.add_staff_task(db, task)
    await db.flush()
    _add_audit_log(
        db,
        actor_user_id,
        "staff_task.created",
        "staff_tasks",
        task.id,
        new_value=_task_audit_value(task),
    )
    await db.commit()
    await db.refresh(task)
    return task


async def update_staff_task(
    db: AsyncSession,
    task_id: UUID,
    payload: StaffTaskUpdate,
    actor_user_id: UUID,
) -> StaffTask:
    task = await get_staff_task(db, task_id)
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return task

    if "staff_id" in update_data:
        await _require_staff_profile(db, update_data["staff_id"])

    old_value = _task_audit_value(task)
    for field, value in update_data.items():
        setattr(task, field, value)

    _add_audit_log(
        db,
        actor_user_id,
        "staff_task.updated",
        "staff_tasks",
        task.id,
        old_value=old_value,
        new_value=_task_audit_value(task),
    )
    await db.commit()
    await db.refresh(task)
    return task


async def delete_staff_task(
    db: AsyncSession,
    task_id: UUID,
    actor_user_id: UUID,
) -> StaffTask:
    task = await get_staff_task(db, task_id)
    old_value = _task_audit_value(task)
    task.deleted_at = datetime.now(timezone.utc)
    _add_audit_log(
        db,
        actor_user_id,
        "staff_task.deleted",
        "staff_tasks",
        task.id,
        old_value=old_value,
        new_value=_task_audit_value(task),
    )
    await db.commit()
    await db.refresh(task)
    return task


async def _validate_staff_uniqueness(
    db: AsyncSession,
    email: str,
    phone: str,
    current_staff_id: UUID | None = None,
) -> None:
    existing_email = await staff_repo.get_staff_profile_by_email(
        db,
        email,
        include_deleted=True,
    )
    if existing_email is not None and existing_email.id != current_staff_id:
        raise ConflictError(
            "Staff email already exists",
            [{"field": "email", "message": "Staff email already exists"}],
        )

    existing_phone = await staff_repo.get_staff_profile_by_phone(
        db,
        phone,
        include_deleted=True,
    )
    if existing_phone is not None and existing_phone.id != current_staff_id:
        raise ConflictError(
            "Staff phone already exists",
            [{"field": "phone", "message": "Staff phone already exists"}],
        )


async def _validate_user_link(
    db: AsyncSession,
    user_id: UUID | None,
    role,
    current_staff_id: UUID | None = None,
) -> None:
    if user_id is None:
        return

    user = await user_repo.get_user_by_id(db, user_id)
    if user is None:
        raise NotFoundError("Linked user account not found")
    user_role = getattr(user.role, "value", user.role)
    role_value = getattr(role, "value", role)
    if user_role != role_value:
        raise BusinessRuleError("Linked user role must match staff role")

    existing = await staff_repo.get_staff_profile_by_user_id(
        db,
        user_id,
        include_deleted=True,
    )
    if existing is not None and existing.id != current_staff_id:
        raise ConflictError(
            "User account is already linked to another staff profile",
            [{"field": "user_id", "message": "User is already linked"}],
        )


async def _require_staff_profile(
    db: AsyncSession,
    staff_id: UUID,
) -> StaffProfile:
    staff_profile = await staff_repo.get_staff_profile_by_id(db, staff_id)
    if staff_profile is None:
        raise NotFoundError("Staff profile not found")
    return staff_profile


def _add_audit_log(
    db: AsyncSession,
    actor_user_id: UUID | None,
    action: str,
    entity_type: str,
    entity_id: UUID,
    old_value: dict | None = None,
    new_value: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
        )
    )


def _staff_audit_value(staff_profile: StaffProfile) -> dict:
    return {
        "id": str(staff_profile.id),
        "user_id": str(staff_profile.user_id) if staff_profile.user_id else None,
        "full_name": staff_profile.full_name,
        "phone": staff_profile.phone,
        "email": staff_profile.email,
        "role": getattr(staff_profile.role, "value", staff_profile.role),
        "status": getattr(staff_profile.status, "value", staff_profile.status),
        "deleted_at": (
            staff_profile.deleted_at.isoformat() if staff_profile.deleted_at else None
        ),
    }


def _task_audit_value(task: StaffTask) -> dict:
    return {
        "id": str(task.id),
        "staff_id": str(task.staff_id),
        "title": task.title,
        "due_date": task.due_date.isoformat(),
        "priority": getattr(task.priority, "value", task.priority),
        "status": getattr(task.status, "value", task.status),
        "deleted_at": task.deleted_at.isoformat() if task.deleted_at else None,
    }
