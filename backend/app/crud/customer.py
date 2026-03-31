from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate


async def get_customers(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Customer]:
    result = await db.execute(select(Customer).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_customer(db: AsyncSession, customer_id: int) -> Customer | None:
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    return result.scalar_one_or_none()


async def create_customer(db: AsyncSession, data: CustomerCreate) -> Customer:
    customer = Customer(**data.model_dump())
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


async def update_customer(db: AsyncSession, customer: Customer, data: CustomerUpdate) -> Customer:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(customer, field, value)
    await db.commit()
    await db.refresh(customer)
    return customer


async def delete_customer(db: AsyncSession, customer: Customer) -> None:
    await db.delete(customer)
    await db.commit()
