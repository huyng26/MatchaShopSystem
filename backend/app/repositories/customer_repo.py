from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def list_customers(
    db: AsyncSession,
    *,
    search: str | None = None,
    include_deleted: bool = False,
) -> list[Customer]:
    stmt = select(Customer)
    if not include_deleted:
        stmt = stmt.where(Customer.deleted_at.is_(None))
    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Customer.name.ilike(pattern),
                Customer.phone.ilike(pattern),
            )
        )

    stmt = stmt.order_by(Customer.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_customer_by_id(
    db: AsyncSession,
    customer_id: UUID,
    *,
    include_deleted: bool = False,
) -> Customer | None:
    stmt = select(Customer).where(Customer.id == customer_id)
    if not include_deleted:
        stmt = stmt.where(Customer.deleted_at.is_(None))

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_customer_by_phone(
    db: AsyncSession,
    phone: str,
    *,
    include_deleted: bool = False,
) -> Customer | None:
    stmt = select(Customer).where(Customer.phone == phone)
    if not include_deleted:
        stmt = stmt.where(Customer.deleted_at.is_(None))

    stmt = stmt.order_by(Customer.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().first()


def add_customer(db: AsyncSession, customer: Customer) -> Customer:
    db.add(customer)
    return customer


async def update_customer(
    db: AsyncSession,
    customer: Customer,
    **values: object,
) -> Customer:
    for field, value in values.items():
        setattr(customer, field, value)
    customer.updated_at = utc_now()

    await db.flush()
    await db.refresh(customer)
    return customer


async def soft_delete_customer(
    db: AsyncSession,
    customer: Customer,
) -> Customer:
    now = utc_now()
    customer.deleted_at = now
    customer.updated_at = now

    await db.flush()
    await db.refresh(customer)
    return customer


async def customer_exists(db: AsyncSession, customer_id: UUID) -> bool:
    stmt = select(
        exists().where(
            Customer.id == customer_id,
            Customer.deleted_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    return bool(result.scalar())


async def add_loyalty_points(
    db: AsyncSession,
    customer_id: UUID,
    points: int,
) -> Customer | None:
    stmt = (
        select(Customer)
        .where(Customer.id == customer_id, Customer.deleted_at.is_(None))
        .with_for_update()
    )
    result = await db.execute(stmt)
    customer = result.scalar_one_or_none()
    if customer is None:
        return None

    customer.loyalty_points += points
    customer.updated_at = utc_now()
    await db.flush()
    await db.refresh(customer)
    return customer
