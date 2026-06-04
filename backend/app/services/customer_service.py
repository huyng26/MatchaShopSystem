from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.customer import Customer
from app.models.order import Order
from app.repositories import customer_repo, order_repo
from app.schemas.customer import CustomerCreate, CustomerUpdate


async def list_customers(
    db: AsyncSession,
    *,
    search: str | None = None,
) -> Sequence[Customer]:
    return await customer_repo.list_customers(db, search=search)


async def get_customer(db: AsyncSession, customer_id: UUID) -> Customer:
    customer = await customer_repo.get_customer_by_id(db, customer_id)
    if customer is None:
        raise NotFoundError("Customer not found")
    return customer


async def create_customer(
    db: AsyncSession,
    payload: CustomerCreate,
) -> Customer:
    customer = Customer(**payload.model_dump())
    customer_repo.add_customer(db, customer)

    try:
        await db.commit()
        await db.refresh(customer)
        return customer
    except Exception:
        await db.rollback()
        raise


async def update_customer(
    db: AsyncSession,
    customer_id: UUID,
    payload: CustomerUpdate,
) -> Customer:
    customer = await get_customer(db, customer_id)
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return customer

    try:
        customer = await customer_repo.update_customer(db, customer, **update_data)
        await db.commit()
        return customer
    except Exception:
        await db.rollback()
        raise


async def delete_customer(db: AsyncSession, customer_id: UUID) -> Customer:
    customer = await get_customer(db, customer_id)

    try:
        customer = await customer_repo.soft_delete_customer(db, customer)
        await db.commit()
        return customer
    except Exception:
        await db.rollback()
        raise


async def list_customer_orders(
    db: AsyncSession,
    customer_id: UUID,
) -> Sequence[Order]:
    await get_customer(db, customer_id)
    return await order_repo.list_orders(db, customer_id=customer_id)
