from typing import Any

from fastapi import APIRouter, HTTPException

from app.core.responses import success_response

router = APIRouter()

# Temporary mock data for early frontend integration.
# Replace this with customer_service calls when implementing real APIs.
MOCK_CUSTOMERS = [
    {
        "id": "customer-1",
        "name": "Nguyen An",
        "phone": "0912345678",
        "address": "Quan 1, TP.HCM",
        "loyalty_points": 120,
    },
    {
        "id": "customer-2",
        "name": "Tran Binh",
        "phone": "0987654321",
        "address": "Quan 3, TP.HCM",
        "loyalty_points": 45,
    },
]

MOCK_ORDERS = [
    {
        "id": "order-1",
        "order_code": "ORD-0001",
        "customer_id": "customer-1",
        "status": "completed",
        "payment_status": "paid",
        "total_amount": 55000,
    },
    {
        "id": "order-2",
        "order_code": "ORD-0002",
        "customer_id": "customer-2",
        "status": "ready_for_delivery",
        "payment_status": "unpaid",
        "total_amount": 65000,
    },
]


@router.get("")
async def list_customers() -> dict[str, Any]:
    return success_response(data=MOCK_CUSTOMERS)


@router.get("/{customer_id}")
async def get_customer(customer_id: str) -> dict[str, Any]:
    customer = next((item for item in MOCK_CUSTOMERS if item["id"] == customer_id), None)
    if customer is None:
        raise HTTPException(status_code=404, detail="customer_not_found")
    return success_response(data=customer)


@router.get("/{customer_id}/orders")
async def get_customer_orders(customer_id: str) -> dict[str, Any]:
    orders = [item for item in MOCK_ORDERS if item.get("customer_id") == customer_id]
    return success_response(data=orders)
