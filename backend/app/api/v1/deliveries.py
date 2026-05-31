from typing import Any

from fastapi import APIRouter

from app.core.responses import success_response

router = APIRouter()

# Temporary mock data for early frontend integration.
# Replace this with delivery_service calls when implementing real APIs.
MOCK_DELIVERY_QUEUE = [
    {
        "order_id": "order-2",
        "order_code": "ORD-0002",
        "customer_name": "Tran Binh",
        "customer_phone": "0987654321",
        "delivery_address": "Quan 3, TP.HCM",
        "delivery_latitude": 10.7829,
        "delivery_longitude": 106.6934,
        "total_amount": 65000,
        "payment_status": "unpaid",
        "cod_amount": 65000,
        "waiting_time": "12 minutes",
        "created_at": "2026-06-01T09:15:00",
    }
]

MOCK_DELIVERY_TRIPS = [
    {
        "id": "trip-1",
        "trip_code": "TRIP-0001",
        "shipper_id": "staff-shipper",
        "status": "pending_dispatch",
        "expected_cod_amount": 65000,
        "orders": MOCK_DELIVERY_QUEUE,
    }
]


@router.get("/queue")
async def get_delivery_queue() -> dict[str, Any]:
    return success_response(data=MOCK_DELIVERY_QUEUE)


@router.get("/trips")
async def list_delivery_trips() -> dict[str, Any]:
    return success_response(data=MOCK_DELIVERY_TRIPS)
