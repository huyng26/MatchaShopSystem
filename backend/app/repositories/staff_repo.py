from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import StaffStatus, TaskStatus, UserRole
from app.models.staff import StaffProfile, StaffTask


async def get_staff_profile_by_id(
    db: AsyncSession,
    staff_id: UUID,
    include_deleted: bool = False,
) -> StaffProfile | None:
    stmt = select(StaffProfile).where(StaffProfile.id == staff_id)
    if not include_deleted:
        stmt = stmt.where(StaffProfile.deleted_at.is_(None))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_staff_profile_by_email(
    db: AsyncSession,
    email: str,
    include_deleted: bool = False,
) -> StaffProfile | None:
    stmt = select(StaffProfile).where(StaffProfile.email == email)
    if not include_deleted:
        stmt = stmt.where(StaffProfile.deleted_at.is_(None))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_staff_profile_by_phone(
    db: AsyncSession,
    phone: str,
    include_deleted: bool = False,
) -> StaffProfile | None:
    stmt = select(StaffProfile).where(StaffProfile.phone == phone)
    if not include_deleted:
        stmt = stmt.where(StaffProfile.deleted_at.is_(None))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_staff_profile_by_user_id(
    db: AsyncSession,
    user_id: UUID,
    include_deleted: bool = False,
) -> StaffProfile | None:
    stmt = select(StaffProfile).where(StaffProfile.user_id == user_id)
    if not include_deleted:
        stmt = stmt.where(StaffProfile.deleted_at.is_(None))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_staff_profiles(
    db: AsyncSession,
    offset: int,
    limit: int,
    role: UserRole | None = None,
    status: StaffStatus | None = None,
    include_deleted: bool = False,
) -> list[StaffProfile]:
    stmt = select(StaffProfile)
    stmt = _apply_staff_filters(stmt, role, status, include_deleted)
    stmt = stmt.order_by(StaffProfile.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def count_staff_profiles(
    db: AsyncSession,
    role: UserRole | None = None,
    status: StaffStatus | None = None,
    include_deleted: bool = False,
) -> int:
    stmt = select(func.count()).select_from(StaffProfile)
    stmt = _apply_staff_filters(stmt, role, status, include_deleted)
    result = await db.execute(stmt)
    return int(result.scalar_one())


async def sum_active_staff_salaries(db: AsyncSession) -> tuple[Decimal, int]:
    stmt = select(
        func.coalesce(func.sum(StaffProfile.salary), Decimal("0")),
        func.count(StaffProfile.id),
    ).where(
        StaffProfile.status == StaffStatus.ACTIVE,
        StaffProfile.deleted_at.is_(None),
        StaffProfile.salary.is_not(None),
    )
    result = await db.execute(stmt)
    total_salary, staff_count = result.one()
    return Decimal(total_salary), int(staff_count)


def add_staff_profile(db: AsyncSession, staff_profile: StaffProfile) -> StaffProfile:
    db.add(staff_profile)
    return staff_profile


async def get_staff_task_by_id(
    db: AsyncSession,
    task_id: UUID,
    include_deleted: bool = False,
) -> StaffTask | None:
    stmt = select(StaffTask).where(StaffTask.id == task_id)
    if not include_deleted:
        stmt = stmt.where(StaffTask.deleted_at.is_(None))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_staff_tasks(
    db: AsyncSession,
    offset: int,
    limit: int,
    staff_id: UUID | None = None,
    status: TaskStatus | None = None,
    include_deleted: bool = False,
) -> list[StaffTask]:
    stmt = select(StaffTask)
    stmt = _apply_task_filters(stmt, staff_id, status, include_deleted)
    stmt = stmt.order_by(StaffTask.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def count_staff_tasks(
    db: AsyncSession,
    staff_id: UUID | None = None,
    status: TaskStatus | None = None,
    include_deleted: bool = False,
) -> int:
    stmt = select(func.count()).select_from(StaffTask)
    stmt = _apply_task_filters(stmt, staff_id, status, include_deleted)
    result = await db.execute(stmt)
    return int(result.scalar_one())


def add_staff_task(db: AsyncSession, staff_task: StaffTask) -> StaffTask:
    db.add(staff_task)
    return staff_task


def _apply_staff_filters(
    stmt,
    role: UserRole | None,
    status: StaffStatus | None,
    include_deleted: bool,
):
    if role is not None:
        stmt = stmt.where(StaffProfile.role == role)
    if status is not None:
        stmt = stmt.where(StaffProfile.status == status)
    if not include_deleted:
        stmt = stmt.where(StaffProfile.deleted_at.is_(None))
    return stmt


def _apply_task_filters(
    stmt,
    staff_id: UUID | None,
    status: TaskStatus | None,
    include_deleted: bool,
):
    if staff_id is not None:
        stmt = stmt.where(StaffTask.staff_id == staff_id)
    if status is not None:
        stmt = stmt.where(StaffTask.status == status)
    if not include_deleted:
        stmt = stmt.where(StaffTask.deleted_at.is_(None))
    return stmt
