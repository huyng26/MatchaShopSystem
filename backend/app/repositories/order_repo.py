from collections.abc import Iterable, Sequence
from datetime import datetime, timezone
from decimal import Decimal
from secrets import token_hex
from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import (
    Order,
    OrderItem,
    OrderPaymentStatus,
    OrderStatus,
    OrderType,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def order_code_exists(db: AsyncSession, order_code: str) -> bool:
    stmt = select(exists().where(Order.order_code == order_code))
    result = await db.execute(stmt)
    return bool(result.scalar())


async def reserve_unique_order_code(
    db: AsyncSession,
    *,
    prefix: str = "ORD",
    max_attempts: int = 20,
) -> str:
    for _ in range(max_attempts):
        timestamp = utc_now().strftime("%Y%m%d%H%M%S")
        order_code = f"{prefix}-{timestamp}-{token_hex(3).upper()}"
        if not await order_code_exists(db, order_code):
            return order_code

    raise RuntimeError("unable_to_reserve_unique_order_code")


async def list_orders(
    db: AsyncSession,
    *,
    status: OrderStatus | None = None,
    payment_status: OrderPaymentStatus | None = None,
    order_type: OrderType | None = None,
    customer_id: UUID | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    include_deleted: bool = False,
    load_items: bool = True,
) -> Sequence[Order]:
    stmt = select(Order).order_by(Order.created_at.desc())
    if not include_deleted:
        stmt = stmt.where(Order.deleted_at.is_(None))
    if status is not None:
        stmt = stmt.where(Order.status == status)
    if payment_status is not None:
        stmt = stmt.where(Order.payment_status == payment_status)
    if order_type is not None:
        stmt = stmt.where(Order.order_type == order_type)
    if customer_id is not None:
        stmt = stmt.where(Order.customer_id == customer_id)
    if created_from is not None:
        stmt = stmt.where(Order.created_at >= created_from)
    if created_to is not None:
        stmt = stmt.where(Order.created_at <= created_to)
    if load_items:
        stmt = stmt.options(selectinload(Order.items).selectinload(OrderItem.product))

    result = await db.execute(stmt)
    return result.scalars().all()


async def get_order(
    db: AsyncSession,
    order_id: UUID,
    *,
    include_deleted: bool = False,
) -> Order | None:
    stmt = select(Order).where(Order.id == order_id)
    if not include_deleted:
        stmt = stmt.where(Order.deleted_at.is_(None))

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_order_detail(
    db: AsyncSession,
    order_id: UUID,
    *,
    include_deleted: bool = False,
) -> Order | None:
    stmt = (
        select(Order)
        .where(Order.id == order_id)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.payments),
        )
    )
    if not include_deleted:
        stmt = stmt.where(Order.deleted_at.is_(None))

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_order_header(
    db: AsyncSession,
    *,
    order_code: str,
    order_type: OrderType,
    created_by: UUID,
    customer_id: UUID | None = None,
    status: OrderStatus = OrderStatus.PENDING,
    payment_status: OrderPaymentStatus = OrderPaymentStatus.UNPAID,
    subtotal: Decimal = Decimal("0"),
    discount_amount: Decimal = Decimal("0"),
    total_amount: Decimal = Decimal("0"),
    customer_name: str | None = None,
    customer_phone: str | None = None,
    delivery_address: str | None = None,
    delivery_latitude: Decimal | None = None,
    delivery_longitude: Decimal | None = None,
    note: str | None = None,
) -> Order:
    order = Order(
        order_code=order_code,
        customer_id=customer_id,
        order_type=order_type,
        status=status,
        payment_status=payment_status,
        subtotal=subtotal,
        discount_amount=discount_amount,
        total_amount=total_amount,
        customer_name=customer_name,
        customer_phone=customer_phone,
        delivery_address=delivery_address,
        delivery_latitude=delivery_latitude,
        delivery_longitude=delivery_longitude,
        note=note,
        created_by=created_by,
    )
    db.add(order)
    await db.flush()
    await db.refresh(order)
    return order


async def create_order_item_rows(
    db: AsyncSession,
    order_id: UUID,
    items: Iterable[dict[str, UUID | int | Decimal]],
) -> Sequence[OrderItem]:
    rows = [
        OrderItem(
            order_id=order_id,
            product_id=item["product_id"],
            quantity=item["quantity"],
            unit_price=item["unit_price"],
            line_total=item["line_total"],
        )
        for item in items
    ]
    db.add_all(rows)
    await db.flush()
    for row in rows:
        await db.refresh(row)
    return rows


async def update_order_status(
    db: AsyncSession,
    order: Order,
    *,
    status: OrderStatus | None = None,
    payment_status: OrderPaymentStatus | None = None,
) -> Order:
    if status is not None:
        order.status = status
    if payment_status is not None:
        order.payment_status = payment_status
    order.updated_at = utc_now()

    await db.flush()
    await db.refresh(order)
    return order


async def set_order_completed(
    db: AsyncSession,
    order: Order,
    *,
    completed_at: datetime | None = None,
) -> Order:
    now = completed_at or utc_now()
    order.status = OrderStatus.COMPLETED
    order.completed_at = now
    order.updated_at = now

    await db.flush()
    await db.refresh(order)
    return order


async def set_order_cancelled(
    db: AsyncSession,
    order: Order,
    *,
    cancelled_at: datetime | None = None,
) -> Order:
    now = cancelled_at or utc_now()
    order.status = OrderStatus.CANCELLED
    order.cancelled_at = now
    order.updated_at = now

    await db.flush()
    await db.refresh(order)
    return order


async def order_is_not_soft_deleted(db: AsyncSession, order_id: UUID) -> bool:
    stmt = select(
        exists().where(
            Order.id == order_id,
            Order.deleted_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    return bool(result.scalar())
