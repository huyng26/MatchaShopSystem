from datetime import date
from uuid import uuid4

import pytest

from app.core.constants import StaffStatus, UserRole, UserStatus
from app.core.exceptions import BusinessRuleError
from app.core.security import verify_password
from app.models.staff import StaffProfile
from app.models.user import User
from app.schemas.staff import StaffProfileCreate
from app.services import staff_service


class FakeDb:
    def __init__(self) -> None:
        self.added = []
        self.commits = 0

    def add(self, item) -> None:
        self.added.append(item)

    async def flush(self) -> None:
        for item in self.added:
            if hasattr(item, "id") and item.id is None:
                item.id = uuid4()

    async def commit(self) -> None:
        self.commits += 1

    async def refresh(self, item) -> None:
        return None


async def no_existing(*args, **kwargs):
    return None


def patch_empty_staff_and_user_lookup(monkeypatch) -> None:
    monkeypatch.setattr(
        staff_service.staff_repo,
        "get_staff_profile_by_email",
        no_existing,
    )
    monkeypatch.setattr(
        staff_service.staff_repo,
        "get_staff_profile_by_phone",
        no_existing,
    )
    monkeypatch.setattr(
        staff_service.staff_repo,
        "get_staff_profile_by_user_id",
        no_existing,
    )
    monkeypatch.setattr(staff_service.user_repo, "get_user_by_email", no_existing)


@pytest.mark.asyncio
async def test_create_staff_profile_can_create_linked_account(monkeypatch) -> None:
    patch_empty_staff_and_user_lookup(monkeypatch)
    db = FakeDb()

    result = await staff_service.create_staff_profile(
        db,
        StaffProfileCreate(
            full_name="Nguyen Shipper",
            phone="0900000999",
            email="shipper@matcha.local",
            role=UserRole.SHIPPER,
            date_joined=date(2026, 6, 1),
            status=StaffStatus.ACTIVE,
            create_account=True,
            account_password="StrongPass123",
            account_status=UserStatus.ACTIVE,
        ),
        actor_user_id=uuid4(),
    )

    created_user = next(item for item in db.added if isinstance(item, User))
    created_staff = next(item for item in db.added if isinstance(item, StaffProfile))
    assert result is created_staff
    assert created_staff.user_id == created_user.id
    assert created_user.email == "shipper@matcha.local"
    assert created_user.role == UserRole.SHIPPER
    assert verify_password("StrongPass123", created_user.hashed_password)
    assert db.commits == 1


@pytest.mark.asyncio
async def test_create_shipper_requires_linked_or_created_account(monkeypatch) -> None:
    patch_empty_staff_and_user_lookup(monkeypatch)

    with pytest.raises(BusinessRuleError, match="Shipper staff must be linked"):
        await staff_service.create_staff_profile(
            FakeDb(),
            StaffProfileCreate(
                full_name="Missing Account",
                phone="0900000888",
                email="missing-shipper@matcha.local",
                role=UserRole.SHIPPER,
                date_joined=date(2026, 6, 1),
            ),
            actor_user_id=uuid4(),
        )
