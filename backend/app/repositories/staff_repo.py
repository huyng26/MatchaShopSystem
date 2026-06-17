from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import StaffStatus, UserRole
from app.models.staff import StaffProfile


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


def add_staff_profile(db: AsyncSession, staff_profile: StaffProfile) -> StaffProfile:
    db.add(staff_profile)
    return staff_profile


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
