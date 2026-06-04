from collections.abc import Sequence
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderPaymentStatus, OrderType
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
    _validate_payment_method_for_order(order, payload.method)

    status = PaymentEventStatus.SUCCESS
    paid_at = utc_now()
    change_amount: Decimal | None = None
    amount = payload.amount.quantize(MONEY_QUANT)
    order_total = order.total_amount.quantize(MONEY_QUANT)

    if payload.method != PaymentMethod.COD and amount < order_total:
        raise ServiceError("payment_amount_less_than_order_total")

    if payload.method == PaymentMethod.CASH:
        if payload.amount_received is None:
            raise ServiceError("cash_amount_received_required")
        if payload.amount_received < order_total:
            raise ServiceError("cash_amount_received_too_low")
        change_amount = (payload.amount_received - order_total).quantize(
            MONEY_QUANT
        )
    elif payload.method == PaymentMethod.COD:
        if amount != order_total:
            raise ServiceError("cod_amount_must_equal_order_total", status_code=409)
        status = PaymentEventStatus.PENDING
        paid_at = None

    try:
        if payload.method == PaymentMethod.COD:
            payment = await _ensure_pending_cod_payment(
                db,
                order_id=payload.order_id,
                amount=order_total,
                created_by=created_by,
            )
        else:
            payment = await payment_repo.create_payment_event(
                db,
                order_id=payload.order_id,
                method=payload.method,
                status=status,
                amount=amount,
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


def _validate_payment_method_for_order(order: Order, method: PaymentMethod) -> None:
    if order.order_type == OrderType.DELIVERY and method == PaymentMethod.CASH:
        raise ServiceError("cash_not_allowed_for_delivery_order", status_code=409)
    if order.order_type == OrderType.INSTORE and method == PaymentMethod.COD:
        raise ServiceError("cod_not_allowed_for_instore_order", status_code=409)


async def _ensure_pending_cod_payment(
    db: AsyncSession,
    *,
    order_id: UUID,
    amount: Decimal,
    created_by: UUID,
) -> Payment:
    pending_cod = await payment_repo.get_pending_cod_payment_for_order(db, order_id)
    if pending_cod is not None:
        return await payment_repo.update_pending_cod_amount(
            db,
            pending_cod,
            amount=amount,
        )
    return await payment_repo.create_payment_event(
        db,
        order_id=order_id,
        method=PaymentMethod.COD,
        status=PaymentEventStatus.PENDING,
        amount=amount,
        created_by=created_by,
    )
