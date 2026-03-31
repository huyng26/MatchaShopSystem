from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderItem, Payment, OrderStatus
from app.models.delivery import DeliveryOrder
from app.schemas.pos import OrderCreate, OrderStatusUpdate, PaymentCreate


async def get_orders(
    db: AsyncSession, skip: int = 0, limit: int = 100, status: OrderStatus | None = None
) -> list[Order]:
    query = select(Order).options(
        selectinload(Order.items),
        selectinload(Order.payment),
    )
    if status:
        query = query.where(Order.status == status)
    query = query.order_by(Order.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_order(db: AsyncSession, order_id: int) -> Order | None:
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items), selectinload(Order.payment))
        .where(Order.id == order_id)
    )
    return result.scalar_one_or_none()


async def create_order(db: AsyncSession, data: OrderCreate, product_prices: dict[int, Decimal]) -> Order:
    order = Order(
        order_type=data.order_type,
        customer_id=data.customer_id,
        notes=data.notes,
    )
    db.add(order)
    await db.flush()

    total = Decimal("0")
    for item_data in data.items:
        price = product_prices[item_data.product_id]
        subtotal = price * item_data.quantity
        total += subtotal
        item = OrderItem(
            order_id=order.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            unit_price=price,
            subtotal=subtotal,
        )
        db.add(item)

    order.total_amount = total

    if data.order_type.value == "delivery" and data.delivery_address:
        delivery = DeliveryOrder(
            order_id=order.id,
            delivery_address=data.delivery_address,
        )
        db.add(delivery)

    await db.commit()
    await db.refresh(order)
    return order


async def update_order_status(db: AsyncSession, order: Order, data: OrderStatusUpdate) -> Order:
    order.status = data.status
    await db.commit()
    await db.refresh(order)
    return order


async def create_payment(db: AsyncSession, order: Order, data: PaymentCreate) -> Payment:
    payment = Payment(
        order_id=order.id,
        method=data.method,
        amount=data.amount,
        reference=data.reference,
    )
    db.add(payment)
    order.status = OrderStatus.completed
    await db.commit()
    await db.refresh(payment)
    return payment
