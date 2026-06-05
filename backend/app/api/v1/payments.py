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
    require_actor_user_id,
)
from app.core.database import get_db
from app.models.payment import PaymentEventStatus, PaymentMethod
from app.schemas.payment import PaymentCreate, PaymentRead
from app.services import payment_service
from app.services.errors import ServiceError
from app.models.user import User
from app.core.permissions import get_current_user

router = APIRouter()


@router.get("")
async def list_payments(
    order_id: UUID | None = Query(default=None),
    method: PaymentMethod | None = Query(default=None),
    status: PaymentEventStatus | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    payments = await payment_service.list_payments(
        db,
        order_id=order_id,
        method=method,
        status=status,
    )
    return ok(read_list(PaymentRead, payments))


@router.post("")
async def create_payment(
    payload: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User= Depends(get_current_user),
) -> dict[str, Any]:
    try:
        payment = await payment_service.create_payment(
            db,
            payload,
            created_by=current_user.id,
        )
        return created(read_one(PaymentRead, payment))
    except ServiceError as error:
        raise_service_error(error)


@router.get("/methods")
async def list_payment_methods() -> dict[str, Any]:
    return ok([method.value for method in payment_service.list_payment_methods()])
