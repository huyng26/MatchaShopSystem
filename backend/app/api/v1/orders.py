import uuid

from fastapi import APIRouter, Depends, status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.integration_contracts import Actor, require_roles
from app.models.order import OrderStatus
from app.schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate
from app.services import order_service

router = APIRouter()
order_read = require_roles("admin", "cashier", "delivery_manager")
order_write = require_roles("admin", "cashier")


@router.get("/orders", response_model=list[OrderResponse])
async def list_orders(
    skip: int = 0,
    limit: int = 100,
    status: OrderStatus | None = None,
    _: Actor = Depends(order_read),
    db: AsyncSession = Depends(get_db),
):
    return await order_service.list_orders(db, skip, limit, status)


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: uuid.UUID,
    _: Actor = Depends(order_read),
    db: AsyncSession = Depends(get_db),
):
    return await order_service.get_order(db, order_id)


@router.post("/orders", response_model=OrderResponse, status_code=http_status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreate,
    actor: Actor = Depends(order_write),
    db: AsyncSession = Depends(get_db),
):
    return await order_service.create_order(db, data, actor.user_id)


@router.patch("/orders/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: uuid.UUID,
    data: OrderStatusUpdate,
    _: Actor = Depends(order_write),
    db: AsyncSession = Depends(get_db),
):
    return await order_service.update_status(db, order_id, data.status)


@router.post("/orders/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: uuid.UUID,
    actor: Actor = Depends(order_write),
    db: AsyncSession = Depends(get_db),
):
    return await order_service.cancel_order(db, order_id, actor.user_id)


@router.post("/orders/{order_id}/complete", response_model=OrderResponse)
async def complete_order(
    order_id: uuid.UUID,
    actor: Actor = Depends(order_write),
    db: AsyncSession = Depends(get_db),
):
    return await order_service.complete_order(db, order_id, actor.user_id)
