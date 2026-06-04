import asyncio
import os
from datetime import UTC, date, datetime

from sqlalchemy import select

from app.core.constants import StaffStatus, UserRole, UserStatus
from app.core.database import AsyncSessionLocal, close_database
from app.core.security import hash_password
from app.models.customer import Customer
from app.models.staff import StaffProfile
from app.models.user import User
from app.repositories.staff_repo import get_staff_profile_by_email
from app.repositories.user_repo import get_user_by_email

DEMO_CUSTOMERS = [
    {
        "name": "Nguyen An",
        "phone": "0912345678",
        "address": "Quan 1, TP.HCM",
        "loyalty_points": 120,
    },
    {
        "name": "Tran Binh",
        "phone": "0987654321",
        "address": "Quan 3, TP.HCM",
        "loyalty_points": 45,
    },
    {
        "name": "Le Chi",
        "phone": "0901122334",
        "address": "Quan Binh Thanh, TP.HCM",
        "loyalty_points": 0,
    },
]


async def seed_admin() -> None:
    admin_email = os.getenv("SEED_ADMIN_EMAIL", "admin@matcha.local").lower()
    admin_password = os.getenv("SEED_ADMIN_PASSWORD", "Admin12345")

    async with AsyncSessionLocal() as db:
        admin = await get_user_by_email(db, admin_email, include_deleted=True)
        if admin is None:
            admin = User(
                email=admin_email,
                hashed_password=hash_password(admin_password),
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
            )
            db.add(admin)
            await db.flush()

        staff_profile = await get_staff_profile_by_email(
            db,
            admin_email,
            include_deleted=True,
        )
        if staff_profile is None:
            db.add(
                StaffProfile(
                    user_id=admin.id,
                    full_name="System Admin",
                    phone=os.getenv("SEED_ADMIN_PHONE", "0900000001"),
                    email=admin_email,
                    role=UserRole.ADMIN,
                    date_joined=date.today(),
                    status=StaffStatus.ACTIVE,
                )
            )

        admin.deleted_at = None
        admin.status = UserStatus.ACTIVE
        admin.updated_at = datetime.now(UTC)
        await db.commit()


async def seed_customers() -> None:
    async with AsyncSessionLocal() as db:
        for customer_data in DEMO_CUSTOMERS:
            result = await db.execute(
                select(Customer).where(Customer.phone == customer_data["phone"])
            )
            customer = result.scalar_one_or_none()
            if customer is None:
                db.add(Customer(**customer_data))
                continue

            for field, value in customer_data.items():
                setattr(customer, field, value)
            customer.deleted_at = None

        await db.commit()


async def main() -> None:
    try:
        await seed_admin()
        await seed_customers()
    finally:
        await close_database()


if __name__ == "__main__":
    asyncio.run(main())
