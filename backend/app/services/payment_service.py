import base64
import io
from collections.abc import Sequence
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.order import Order, OrderPaymentStatus, OrderStatus, OrderType
from app.models.payment import Payment, PaymentEventStatus, PaymentMethod
from app.repositories import order_repo, payment_repo
from app.schemas.order import OrderReadyForDelivery
from app.schemas.payment import PaymentCreate, StripeCheckoutSessionCreate
from app.services.errors import ServiceError
from app.services import order_service, stripe_gateway

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


async def create_stripe_checkout_session(
    db: AsyncSession,
    payload: StripeCheckoutSessionCreate,
    *,
    created_by: UUID,
) -> dict[str, Any]:
    settings = get_settings()
    _validate_stripe_checkout_settings(settings)

    order = await order_repo.get_order_detail(db, payload.order_id)
    if order is None:
        raise ServiceError("order_not_found", status_code=404)
    _validate_order_for_stripe_checkout(order)

    amount = order.total_amount.quantize(MONEY_QUANT)
    amount_minor = _stripe_amount_minor_units(amount, settings.stripe_currency)
    pending = await payment_repo.get_latest_pending_stripe_checkout_payment_for_order(
        db,
        order.id,
    )
    if pending is not None and _pending_stripe_payment_is_reusable(
        pending,
        ready_for_delivery=payload.ready_for_delivery,
    ):
        return _stripe_checkout_response(pending)

    session = stripe_gateway.create_checkout_session(
        order=order,
        amount_minor=amount_minor,
        currency=settings.stripe_currency.lower(),
        success_url=settings.stripe_success_url or "",
        cancel_url=settings.stripe_cancel_url or "",
        secret_key=settings.stripe_secret_key or "",
    )
    session_id = _stripe_field(session, "id")
    checkout_url = _stripe_field(session, "url")
    if not session_id or not checkout_url:
        raise ServiceError("stripe_checkout_session_invalid", status_code=502)

    expires_at = _stripe_timestamp_to_datetime(_stripe_field(session, "expires_at"))
    metadata = {
        "checkout_url": checkout_url,
        "expires_at": expires_at.isoformat() if expires_at is not None else None,
        "ready_for_delivery": payload.ready_for_delivery,
        "stripe_status": _stripe_field(session, "status"),
        "stripe_payment_status": _stripe_field(session, "payment_status"),
        "stripe_currency": settings.stripe_currency.lower(),
        "stripe_amount_total": amount_minor,
        "order_id": str(order.id),
    }

    try:
        payment = await payment_repo.create_payment_event(
            db,
            order_id=order.id,
            method=PaymentMethod.BANK_TRANSFER,
            status=PaymentEventStatus.PENDING,
            amount=amount,
            gateway_transaction_id=session_id,
            metadata=metadata,
            created_by=created_by,
        )
        await db.commit()
        return _stripe_checkout_response(payment)
    except Exception:
        await db.rollback()
        raise


async def get_stripe_checkout_session_status(
    db: AsyncSession,
    session_id: str,
) -> dict[str, Any]:
    payment = await payment_repo.get_payment_by_gateway_transaction_id(
        db,
        session_id,
        load_order=True,
    )
    if payment is None or not _is_stripe_checkout_payment(payment):
        raise ServiceError("stripe_checkout_session_not_found", status_code=404)
    if payment.order is None:
        raise ServiceError("order_not_found", status_code=404)

    await _sync_stripe_checkout_status_from_gateway(db, payment)
    payment = await payment_repo.get_payment_by_gateway_transaction_id(
        db,
        session_id,
        load_order=True,
    )
    if payment is None or payment.order is None:
        raise ServiceError("stripe_checkout_session_not_found", status_code=404)
    return _stripe_checkout_status_response(payment)


async def handle_stripe_webhook_event(
    db: AsyncSession,
    event: Any,
) -> dict[str, Any]:
    event_type = _stripe_field(event, "type")
    try:
        if event_type == "checkout.session.completed":
            result = await _handle_stripe_checkout_completed(db, _event_object(event))
        elif event_type == "checkout.session.expired":
            result = await _handle_stripe_checkout_terminal_status(
                db,
                _event_object(event),
                status=PaymentEventStatus.CANCELLED,
            )
        elif event_type in {
            "checkout.session.async_payment_failed",
            "payment_intent.payment_failed",
        }:
            result = await _handle_stripe_checkout_terminal_status(
                db,
                _event_object(event),
                status=PaymentEventStatus.FAILED,
            )
        else:
            result = {"processed": False, "event_type": event_type}

        await db.commit()
        return result
    except Exception:
        await db.rollback()
        raise


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


def _validate_stripe_checkout_settings(settings: Any) -> None:
    if (
        not settings.stripe_secret_key
        or not settings.stripe_success_url
        or not settings.stripe_cancel_url
    ):
        raise ServiceError("stripe_checkout_not_configured", status_code=503)


def _validate_order_for_stripe_checkout(order: Order) -> None:
    if order.status in (OrderStatus.COMPLETED, OrderStatus.CANCELLED):
        raise ServiceError("order_not_payable_by_stripe", status_code=409)
    if order.payment_status == OrderPaymentStatus.PAID:
        raise ServiceError("order_already_paid", status_code=409)
    if order.total_amount <= Decimal("0"):
        raise ServiceError("stripe_checkout_amount_must_be_positive")


def _stripe_amount_minor_units(amount: Decimal, currency: str) -> int:
    if currency.lower() != "vnd":
        raise ServiceError("stripe_currency_must_be_vnd", status_code=503)
    return stripe_gateway.amount_to_zero_decimal_minor_units(amount)


def _pending_stripe_payment_is_reusable(
    payment: Payment,
    *,
    ready_for_delivery: bool,
) -> bool:
    metadata = payment.metadata_ or {}
    if metadata.get("ready_for_delivery") is not ready_for_delivery:
        return False
    expires_at = _parse_datetime(metadata.get("expires_at"))
    return expires_at is None or expires_at > utc_now()


def _stripe_checkout_response(payment: Payment) -> dict[str, Any]:
    metadata = payment.metadata_ or {}
    checkout_url = metadata.get("checkout_url")
    if not isinstance(checkout_url, str) or not checkout_url:
        raise ServiceError("stripe_checkout_url_missing", status_code=500)
    return {
        "payment_id": payment.id,
        "order_id": payment.order_id,
        "stripe_checkout_session_id": payment.gateway_transaction_id,
        "checkout_url": checkout_url,
        "qr_code_data_url": _build_qr_code_data_url(checkout_url),
        "expires_at": _parse_datetime(metadata.get("expires_at")),
        "status": payment.status,
    }


def _stripe_checkout_status_response(payment: Payment) -> dict[str, Any]:
    order = payment.order
    return {
        "payment_id": payment.id,
        "order_id": payment.order_id,
        "stripe_checkout_session_id": payment.gateway_transaction_id,
        "payment_status": payment.status,
        "order_status": order.status,
        "order_payment_status": order.payment_status,
        "paid_at": payment.paid_at,
        "completed_at": order.completed_at,
    }


async def _sync_stripe_checkout_status_from_gateway(
    db: AsyncSession,
    payment: Payment,
) -> None:
    if payment.status != PaymentEventStatus.PENDING:
        return

    settings = get_settings()
    if not settings.stripe_secret_key or not payment.gateway_transaction_id:
        return

    session = stripe_gateway.retrieve_checkout_session(
        session_id=payment.gateway_transaction_id,
        secret_key=settings.stripe_secret_key,
    )
    stripe_status = _stripe_field(session, "status")
    stripe_payment_status = _stripe_field(session, "payment_status")

    try:
        if stripe_status == "complete" and stripe_payment_status in {
            "paid",
            "no_payment_required",
        }:
            await _handle_stripe_checkout_completed(db, session)
            await db.commit()
        elif stripe_status == "expired":
            await _handle_stripe_checkout_terminal_status(
                db,
                session,
                status=PaymentEventStatus.CANCELLED,
            )
            await db.commit()
    except Exception:
        await db.rollback()
        raise


def _build_qr_code_data_url(value: str) -> str:
    try:
        import qrcode
    except ImportError as error:
        raise ServiceError(
            "qrcode_dependency_not_installed",
            status_code=503,
        ) from error

    image = qrcode.make(value)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


async def _handle_stripe_checkout_completed(
    db: AsyncSession,
    session: Any,
) -> dict[str, Any]:
    session_id = _stripe_field(session, "id")
    if not session_id:
        raise ServiceError("stripe_checkout_session_id_missing", status_code=400)

    payment = await payment_repo.get_payment_by_gateway_transaction_id(
        db,
        session_id,
        for_update=True,
        load_order=True,
    )
    if payment is None or not _is_stripe_checkout_payment(payment):
        return {"processed": False, "reason": "payment_not_found"}
    if payment.status == PaymentEventStatus.SUCCESS:
        return {"processed": True, "payment_id": payment.id, "idempotent": True}

    _validate_stripe_session_matches_payment(session, payment)
    metadata = {
        **(payment.metadata_ or {}),
        "stripe_status": _stripe_field(session, "status"),
        "stripe_payment_status": _stripe_field(session, "payment_status"),
        "stripe_completed_at": utc_now().isoformat(),
    }
    payment_intent = _stripe_field(session, "payment_intent")

    await payment_repo.mark_payment_success(
        db,
        payment,
        amount_received=payment.amount.quantize(MONEY_QUANT),
        paid_at=utc_now(),
        bank_reference_number=str(payment_intent) if payment_intent else None,
        metadata=metadata,
    )
    order = await order_repo.update_order_status(
        db,
        payment.order,
        payment_status=OrderPaymentStatus.PAID,
    )

    if order.order_type == OrderType.INSTORE:
        await order_service.complete_order_without_commit(db, order.id)
    elif metadata.get("ready_for_delivery") is True:
        await order_service.mark_ready_for_delivery_without_commit(
            db,
            order.id,
            OrderReadyForDelivery(payment_method=None),
            actor_user_id=payment.created_by,
        )

    return {"processed": True, "payment_id": payment.id}


async def _handle_stripe_checkout_terminal_status(
    db: AsyncSession,
    session: Any,
    *,
    status: PaymentEventStatus,
) -> dict[str, Any]:
    session_id = _stripe_field(session, "id")
    if not session_id:
        return {"processed": False, "reason": "session_id_missing"}
    payment = await payment_repo.get_payment_by_gateway_transaction_id(
        db,
        session_id,
        for_update=True,
    )
    if payment is None or not _is_stripe_checkout_payment(payment):
        return {"processed": False, "reason": "payment_not_found"}
    if payment.status != PaymentEventStatus.PENDING:
        return {"processed": True, "payment_id": payment.id, "idempotent": True}

    metadata = {
        **(payment.metadata_ or {}),
        "stripe_status": _stripe_field(session, "status"),
        "stripe_payment_status": _stripe_field(session, "payment_status"),
        "stripe_terminal_at": utc_now().isoformat(),
    }
    await payment_repo.update_payment_status(
        db,
        payment,
        status=status,
        metadata=metadata,
    )
    return {"processed": True, "payment_id": payment.id}


def _validate_stripe_session_matches_payment(session: Any, payment: Payment) -> None:
    metadata = _stripe_field(session, "metadata") or {}
    order_id = _stripe_mapping_value(metadata, "order_id")
    if order_id and order_id != str(payment.order_id):
        raise ServiceError("stripe_session_order_mismatch", status_code=409)

    amount_total = _stripe_field(session, "amount_total")
    expected_amount = _stripe_amount_minor_units(
        payment.amount.quantize(MONEY_QUANT),
        (payment.metadata_ or {}).get("stripe_currency", "vnd"),
    )
    if amount_total is not None and int(amount_total) != expected_amount:
        raise ServiceError("stripe_session_amount_mismatch", status_code=409)

    currency = _stripe_field(session, "currency")
    if currency and currency.lower() != (payment.metadata_ or {}).get(
        "stripe_currency",
        "vnd",
    ):
        raise ServiceError("stripe_session_currency_mismatch", status_code=409)


def _is_stripe_checkout_payment(payment: Payment) -> bool:
    return (
        payment.method == PaymentMethod.BANK_TRANSFER
        and payment.gateway_transaction_id is not None
        and bool((payment.metadata_ or {}).get("checkout_url"))
    )


def _event_object(event: Any) -> Any:
    data = _stripe_field(event, "data") or {}
    return _stripe_field(data, "object")


def _stripe_field(obj: Any, key: str) -> Any:
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


def _stripe_mapping_value(obj: Any, key: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(key)
    if hasattr(obj, "get"):
        return obj.get(key)
    return getattr(obj, key, None)


def _stripe_timestamp_to_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    return datetime.fromtimestamp(int(value), tz=timezone.utc)


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed
