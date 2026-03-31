from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud import pos as crud
from app.models.order import OrderStatus
from app.models.product import Product
from app.schemas.pos import OrderCreate, OrderStatusUpdate, OrderResponse, PaymentCreate, PaymentResponse

router = APIRouter()


async def _fetch_product_prices(db: AsyncSession, product_ids: list[int]) -> dict[int, Decimal]:
    result = await db.execute(select(Product).where(Product.id.in_(product_ids)))
    products = result.scalars().all()
    missing = set(product_ids) - {p.id for p in products}
    if missing:
        raise HTTPException(status_code=404, detail=f"Products not found: {missing}")
    return {p.id: p.selling_price for p in products}


@router.get("/orders", response_model=list[OrderResponse])
async def list_orders(
    skip: int = 0,
    limit: int = 50,
    status: OrderStatus | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await crud.get_orders(db, skip=skip, limit=limit, status=status)


@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(data: OrderCreate, db: AsyncSession = Depends(get_db)):
    if not data.items:
        raise HTTPException(status_code=400, detail="Order must have at least one item")
    if data.order_type.value == "delivery" and not data.delivery_address:
        raise HTTPException(status_code=400, detail="delivery_address is required for delivery orders")

    product_ids = [item.product_id for item in data.items]
    prices = await _fetch_product_prices(db, product_ids)
    return await crud.create_order(db, data, prices)


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    order = await crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/orders/{order_id}/status", response_model=OrderResponse)
async def update_order_status(order_id: int, data: OrderStatusUpdate, db: AsyncSession = Depends(get_db)):
    order = await crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return await crud.update_order_status(db, order, data)


@router.post("/orders/{order_id}/payment", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def record_payment(order_id: int, data: PaymentCreate, db: AsyncSession = Depends(get_db)):
    order = await crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.payment:
        raise HTTPException(status_code=400, detail="Payment already recorded for this order")
    return await crud.create_payment(db, order, data)
