from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import UserRole, UserStatus
from app.models.user import User


async def get_user_by_id(
    db: AsyncSession,
    user_id: UUID,
    include_deleted: bool = False,
) -> User | None:
    stmt = select(User).where(User.id == user_id)
    if not include_deleted:
        stmt = stmt.where(User.deleted_at.is_(None))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_email(
    db: AsyncSession,
    email: str,
    include_deleted: bool = False,
) -> User | None:
    stmt = select(User).where(User.email == email)
    if not include_deleted:
        stmt = stmt.where(User.deleted_at.is_(None))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_users(
    db: AsyncSession,
    offset: int,
    limit: int,
    role: UserRole | None = None,
    status: UserStatus | None = None,
    include_deleted: bool = False,
) -> list[User]:
    stmt = select(User)
    stmt = _apply_user_filters(stmt, role, status, include_deleted)
    stmt = stmt.order_by(User.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def count_users(
    db: AsyncSession,
    role: UserRole | None = None,
    status: UserStatus | None = None,
    include_deleted: bool = False,
) -> int:
    stmt = select(func.count()).select_from(User)
    stmt = _apply_user_filters(stmt, role, status, include_deleted)
    result = await db.execute(stmt)
    return int(result.scalar_one())


def add_user(db: AsyncSession, user: User) -> User:
    db.add(user)
    return user


def _apply_user_filters(
    stmt,
    role: UserRole | None,
    status: UserStatus | None,
    include_deleted: bool,
):
    if role is not None:
        stmt = stmt.where(User.role == role)
    if status is not None:
        stmt = stmt.where(User.status == status)
    if not include_deleted:
        stmt = stmt.where(User.deleted_at.is_(None))
    return stmt
