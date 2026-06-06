from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import UserStatus
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.core.security import hash_password
from app.models.audit import AuditLog
from app.models.user import User
from app.repositories import user_repo
from app.schemas.account import UserCreate, UserUpdate


async def list_accounts(
    db: AsyncSession,
    page: int,
    page_size: int,
    role=None,
    status=None,
) -> tuple[list[User], int]:
    offset = (page - 1) * page_size
    users = await user_repo.list_users(db, offset, page_size, role=role, status=status)
    total = await user_repo.count_users(db, role=role, status=status)
    return users, total


async def get_account(db: AsyncSession, user_id: UUID) -> User:
    user = await user_repo.get_user_by_id(db, user_id)
    if user is None:
        raise NotFoundError("Account not found")
    return user


async def create_account(
    db: AsyncSession,
    payload: UserCreate,
    actor_user_id: UUID | None,
) -> User:
    existing = await user_repo.get_user_by_email(
        db,
        payload.email,
        include_deleted=True,
    )
    if existing is not None:
        raise ConflictError(
            "Email already exists",
            [{"field": "email", "message": "Email already exists"}],
        )

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        status=payload.status,
    )
    user_repo.add_user(db, user)
    await db.flush()
    _add_audit_log(
        db,
        actor_user_id,
        "account.created",
        "users",
        user.id,
        new_value=_user_audit_value(user),
    )
    await db.commit()
    await db.refresh(user)
    return user


async def update_account(
    db: AsyncSession,
    user_id: UUID,
    payload: UserUpdate,
    actor_user_id: UUID | None,
) -> User:
    user = await get_account(db, user_id)
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return user

    if "email" in update_data:
        existing = await user_repo.get_user_by_email(
            db,
            update_data["email"],
            include_deleted=True,
        )
        if existing is not None and existing.id != user.id:
            raise ConflictError(
                "Email already exists",
                [{"field": "email", "message": "Email already exists"}],
            )

    old_value = _user_audit_value(user)
    if "email" in update_data:
        user.email = update_data["email"]
    if "password" in update_data:
        user.hashed_password = hash_password(update_data["password"])
    if "role" in update_data:
        user.role = update_data["role"]
    if "status" in update_data:
        user.status = update_data["status"]

    _add_audit_log(
        db,
        actor_user_id,
        "account.updated",
        "users",
        user.id,
        old_value=old_value,
        new_value=_user_audit_value(user),
    )
    await db.commit()
    await db.refresh(user)
    return user


async def delete_account(
    db: AsyncSession,
    user_id: UUID,
    actor_user_id: UUID | None,
) -> User:
    if actor_user_id == user_id:
        raise BusinessRuleError("Current user cannot delete their own account")

    user = await get_account(db, user_id)
    old_value = _user_audit_value(user)
    user.status = UserStatus.INACTIVE
    user.deleted_at = datetime.now(timezone.utc)
    _add_audit_log(
        db,
        actor_user_id,
        "account.deleted",
        "users",
        user.id,
        old_value=old_value,
        new_value=_user_audit_value(user),
    )
    await db.commit()
    await db.refresh(user)
    return user


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


def _user_audit_value(user: User) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "role": getattr(user.role, "value", user.role),
        "status": getattr(user.status, "value", user.status),
        "deleted_at": user.deleted_at.isoformat() if user.deleted_at else None,
    }
