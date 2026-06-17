from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import StaffStatus, UserRole, UserStatus
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.core.security import hash_password
from app.models.audit import AuditLog
from app.models.staff import StaffProfile
from app.models.user import User
from app.repositories import staff_repo, user_repo
from app.schemas.staff import (
    StaffProfileCreate,
    StaffProfileUpdate,
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
    user_id = await _resolve_staff_user_link(
        db,
        email=payload.email,
        role=payload.role,
        user_id=payload.user_id,
        create_account=payload.create_account,
        account_password=payload.account_password,
        account_status=payload.account_status,
        actor_user_id=actor_user_id,
    )

    staff_data = payload.model_dump(
        exclude={"create_account", "account_password", "account_status"}
    )
    staff_data["user_id"] = user_id
    staff_profile = StaffProfile(**staff_data)
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
    create_account = bool(update_data.pop("create_account", False))
    account_password = update_data.pop("account_password", None)
    account_status = update_data.pop("account_status", UserStatus.ACTIVE)
    if not update_data:
        if create_account:
            update_data["user_id"] = await _create_account_for_staff(
                db,
                email=staff_profile.email,
                role=staff_profile.role,
                account_password=account_password,
                account_status=account_status,
                actor_user_id=actor_user_id,
                current_staff_id=staff_profile.id,
                current_user_id=staff_profile.user_id,
            )
        else:
            _validate_account_options(
                create_account=create_account,
                account_password=account_password,
            )
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
    if create_account:
        _validate_account_options(
            create_account=True,
            account_password=account_password,
            requested_user_id=update_data.get("user_id"),
        )
        update_data["user_id"] = await _create_account_for_staff(
            db,
            email=next_email,
            role=next_role,
            account_password=account_password,
            account_status=account_status,
            actor_user_id=actor_user_id,
            current_staff_id=staff_profile.id,
            current_user_id=staff_profile.user_id,
        )
    else:
        _validate_account_options(
            create_account=create_account,
            account_password=account_password,
        )
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
    _validate_shipper_account_requirement(
        next_role,
        update_data.get("user_id", staff_profile.user_id),
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


async def _resolve_staff_user_link(
    db: AsyncSession,
    *,
    email: str,
    role,
    user_id: UUID | None,
    create_account: bool,
    account_password: str | None,
    account_status: UserStatus,
    actor_user_id: UUID | None,
) -> UUID | None:
    _validate_account_options(
        create_account=create_account,
        account_password=account_password,
        requested_user_id=user_id,
    )
    if create_account:
        user_id = await _create_account_for_staff(
            db,
            email=email,
            role=role,
            account_password=account_password,
            account_status=account_status,
            actor_user_id=actor_user_id,
        )
    else:
        await _validate_user_link(db, user_id, role)

    _validate_shipper_account_requirement(role, user_id)
    return user_id


async def _create_account_for_staff(
    db: AsyncSession,
    *,
    email: str,
    role,
    account_password: str | None,
    account_status: UserStatus,
    actor_user_id: UUID | None,
    current_staff_id: UUID | None = None,
    current_user_id: UUID | None = None,
) -> UUID:
    _validate_account_options(
        create_account=True,
        account_password=account_password,
        current_user_id=current_user_id,
    )

    existing = await user_repo.get_user_by_email(
        db,
        email,
        include_deleted=True,
    )
    if existing is not None:
        raise ConflictError(
            "Account email already exists",
            [{"field": "email", "message": "Account email already exists"}],
        )

    user = User(
        email=email,
        hashed_password=hash_password(account_password),
        role=role,
        status=account_status,
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

    existing_link = await staff_repo.get_staff_profile_by_user_id(
        db,
        user.id,
        include_deleted=True,
    )
    if existing_link is not None and existing_link.id != current_staff_id:
        raise ConflictError(
            "User account is already linked to another staff profile",
            [{"field": "user_id", "message": "User is already linked"}],
        )

    return user.id


def _validate_account_options(
    *,
    create_account: bool,
    account_password: str | None,
    requested_user_id: UUID | None = None,
    current_user_id: UUID | None = None,
) -> None:
    if account_password is not None and not create_account:
        raise BusinessRuleError(
            "create_account must be true when account_password is provided"
        )
    if not create_account:
        return
    if requested_user_id is not None:
        raise BusinessRuleError("Choose either linked user or create account")
    if current_user_id is not None:
        raise BusinessRuleError("Staff profile already has a linked account")
    if account_password is None:
        raise BusinessRuleError("Account password is required")


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


def _validate_shipper_account_requirement(role, user_id: UUID | None) -> None:
    if _enum_value(role) == UserRole.SHIPPER.value and user_id is None:
        raise BusinessRuleError("Shipper staff must be linked to an account")


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


def _user_audit_value(user: User) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "role": _enum_value(user.role),
        "status": _enum_value(user.status),
        "deleted_at": user.deleted_at.isoformat() if user.deleted_at else None,
    }


def _enum_value(value):
    return getattr(value, "value", value)
