from decimal import Decimal
from typing import Any

from app.models.order import Order
from app.services.errors import ServiceError


def require_stripe() -> Any:
    try:
        import stripe
    except ImportError as error:
        raise ServiceError(
            "stripe_dependency_not_installed",
            status_code=503,
        ) from error
    return stripe


def create_checkout_session(
    *,
    order: Order,
    amount_minor: int,
    currency: str,
    success_url: str,
    cancel_url: str,
    secret_key: str,
) -> Any:
    stripe = require_stripe()
    return stripe.checkout.Session.create(
        api_key=secret_key,
        mode="payment",
        payment_method_types=["card"],
        client_reference_id=str(order.id),
        metadata={
            "order_id": str(order.id),
            "order_code": order.order_code,
        },
        line_items=[
            {
                "quantity": 1,
                "price_data": {
                    "currency": currency,
                    "unit_amount": amount_minor,
                    "product_data": {
                        "name": f"Matcha order {order.order_code}",
                    },
                },
            }
        ],
        success_url=success_url,
        cancel_url=cancel_url,
    )


def retrieve_checkout_session(
    *,
    session_id: str,
    secret_key: str,
) -> Any:
    stripe = require_stripe()
    return stripe.checkout.Session.retrieve(
        session_id,
        api_key=secret_key,
    )


def construct_webhook_event(
    *,
    payload: bytes,
    signature: str,
    webhook_secret: str,
) -> Any:
    stripe = require_stripe()
    return stripe.Webhook.construct_event(
        payload=payload,
        sig_header=signature,
        secret=webhook_secret,
    )


def amount_to_zero_decimal_minor_units(amount: Decimal) -> int:
    if amount != amount.to_integral_value():
        raise ServiceError("stripe_vnd_amount_must_be_whole_number")
    return int(amount)
