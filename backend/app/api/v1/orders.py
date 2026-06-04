from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import (
    created,
    ok,
    raise_service_error,
    read_list,
    read_one,
)
from app.core.database import get_db
from app.core.permissions import get_current_user
from app.models.user import User
from app.models.order import OrderPaymentStatus, OrderStatus, OrderType
from app.schemas.order import (
    OrderCreate,
    OrderDetailRead,
    OrderListFilters,
    OrderRead,
)
from app.services import order_service
from app.services.errors import ServiceError

router = APIRouter()


@router.get("")
async def list_orders(
    status: OrderStatus | None = Query(default=None),
    payment_status: OrderPaymentStatus | None = Query(default=None),
    order_type: OrderType | None = Query(default=None),
    customer_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    filters = OrderListFilters(
        status=status,
        payment_status=payment_status,
        order_type=order_type,
        customer_id=customer_id,
    )
    orders = await order_service.list_orders(db, filters)
    return ok(read_list(OrderRead, orders))


@router.post("")
async def create_order(
    payload: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    try:
        order = await order_service.create_order(
            db,
            payload,
            created_by=current_user.id,
        )
        return created(read_one(OrderDetailRead, order))
    except ServiceError as error:
        raise_service_error(error)


@router.get("/{order_id}")
async def get_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        order = await order_service.get_order_detail(db, order_id)
        return ok(read_one(OrderDetailRead, order))
    except ServiceError as error:
        raise_service_error(error)


@router.post("/{order_id}/complete")
async def complete_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        result = await order_service.complete_order(db, order_id)
        return ok(result, message="Order completed successfully")
    except ServiceError as error:
        raise_service_error(error)


@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        result = await order_service.cancel_order(db, order_id)
        return ok(result, message="Order cancelled successfully")
    except ServiceError as error:
        raise_service_error(error)
