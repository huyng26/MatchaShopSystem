from typing import Any

from fastapi import APIRouter

from app.core.responses import success_response

router = APIRouter()

# Temporary mock data for early frontend integration.
# Replace this with payment_service calls when implementing real APIs.
MOCK_PAYMENTS = [
    {
        "id": "payment-1",
        "order_id": "order-1",
        "method": "cash",
        "status": "success",
        "amount": 55000,
        "paid_at": "2026-06-01T09:05:00",
    }
]


@router.get("")
async def list_payments() -> dict[str, Any]:
    return success_response(data=MOCK_PAYMENTS)


@router.get("/methods")
async def list_payment_methods() -> dict[str, Any]:
    return success_response(data=["cash", "card", "bank_transfer", "cod"])
