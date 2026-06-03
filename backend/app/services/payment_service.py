from collections.abc import Sequence
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import OrderPaymentStatus
from app.models.payment import Payment, PaymentEventStatus, PaymentMethod
from app.repositories import order_repo, payment_repo
from app.schemas.payment import PaymentCreate
from app.services.errors import ServiceError

MONEY_QUANT = Decimal("0.01")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def list_payments(
    db: AsyncSession,
    *,
    order_id: UUID | None = None,
    method: PaymentMethod | None = None,
    status: PaymentEventStatus | None = None,
) -> Sequence[Payment]:
    return await payment_repo.list_payments(
        db,
        order_id=order_id,
        method=method,
        status=status,
    )


async def create_payment(
    db: AsyncSession,
    payload: PaymentCreate,
    *,
    created_by: UUID,
) -> Payment:
    if payload.amount <= Decimal("0"):
        raise ServiceError("payment_amount_must_be_positive")

    order = await order_repo.get_order(db, payload.order_id)
    if order is None:
        raise ServiceError("order_not_found", status_code=404)

    status = PaymentEventStatus.SUCCESS
    paid_at = utc_now()
    change_amount: Decimal | None = None

    if payload.method != PaymentMethod.COD and payload.amount < order.total_amount:
        raise ServiceError("payment_amount_less_than_order_total")

    if payload.method == PaymentMethod.CASH:
        if payload.amount_received is None:
            raise ServiceError("cash_amount_received_required")
        if payload.amount_received < order.total_amount:
            raise ServiceError("cash_amount_received_too_low")
        change_amount = (payload.amount_received - order.total_amount).quantize(
            MONEY_QUANT
        )
    elif payload.method == PaymentMethod.COD:
        status = PaymentEventStatus.PENDING
        paid_at = None

    try:
        payment = await payment_repo.create_payment_event(
            db,
            order_id=payload.order_id,
            method=payload.method,
            status=status,
            amount=payload.amount,
            amount_received=payload.amount_received,
            change_amount=change_amount,
            gateway_transaction_id=payload.gateway_transaction_id,
            bank_reference_number=payload.bank_reference_number,
            paid_at=paid_at,
            created_by=created_by,
        )

        if status == PaymentEventStatus.SUCCESS:
            await order_repo.update_order_status(
                db,
                order,
                payment_status=OrderPaymentStatus.PAID,
            )

        await db.commit()
        return payment
    except Exception:
        await db.rollback()
        raise


def list_payment_methods() -> list[PaymentMethod]:
    return list(PaymentMethod)
