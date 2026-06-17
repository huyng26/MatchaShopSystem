from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import (
    created,
    ok,
    raise_service_error,
    read_list,
    read_one,
)
from app.core.database import get_db
from app.core.config import get_settings
from app.models.payment import PaymentEventStatus, PaymentMethod
from app.schemas.payment import (
    PaymentCreate,
    PaymentRead,
    StripeCheckoutSessionCreate,
    StripeCheckoutSessionRead,
    StripeCheckoutSessionStatusRead,
)
from app.services import payment_service, stripe_gateway
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


@router.post("/stripe/checkout-session")
async def create_stripe_checkout_session(
    payload: StripeCheckoutSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    try:
        session = await payment_service.create_stripe_checkout_session(
            db,
            payload,
            created_by=current_user.id,
        )
        return created(
            StripeCheckoutSessionRead.model_validate(session),
            message="Stripe checkout session created successfully",
        )
    except ServiceError as error:
        raise_service_error(error)


@router.get("/stripe/checkout-session/{session_id}/status")
async def get_stripe_checkout_session_status(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    try:
        status = await payment_service.get_stripe_checkout_session_status(
            db,
            session_id,
        )
        return ok(StripeCheckoutSessionStatusRead.model_validate(status))
    except ServiceError as error:
        raise_service_error(error)


@router.post("/stripe/webhook")
async def handle_stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    if stripe_signature is None:
        raise HTTPException(status_code=400, detail="stripe_signature_required")

    settings = get_settings()
    if not settings.stripe_webhook_secret:
        raise_service_error(
            ServiceError("stripe_webhook_not_configured", status_code=503)
        )

    payload = await request.body()
    try:
        event = stripe_gateway.construct_webhook_event(
            payload=payload,
            signature=stripe_signature,
            webhook_secret=settings.stripe_webhook_secret,
        )
    except ServiceError as error:
        raise_service_error(error)
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail="invalid_stripe_webhook_signature",
        ) from error

    try:
        result = await payment_service.handle_stripe_webhook_event(db, event)
        return ok(result, message="Stripe webhook processed successfully")
    except ServiceError as error:
        raise_service_error(error)


@router.get("/methods")
async def list_payment_methods() -> dict[str, Any]:
    return ok([method.value for method in payment_service.list_payment_methods()])
