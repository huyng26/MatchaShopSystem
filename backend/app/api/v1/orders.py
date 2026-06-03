from typing import Any

from fastapi import APIRouter, Body, HTTPException

from app.core.responses import success_response

router = APIRouter()

# Temporary mock data for early frontend integration.
# Replace this with order_service calls when implementing real APIs.
MOCK_ORDERS = [
    {
        "id": "order-1",
        "order_code": "ORD-0001",
        "customer_id": "customer-1",
        "order_type": "instore",
        "status": "completed",
        "payment_status": "paid",
        "subtotal": 55000,
        "discount_amount": 0,
        "total_amount": 55000,
        "created_at": "2026-06-01T09:00:00",
        "items": [
            {
                "product_id": "product-matcha-latte",
                "product_name": "Matcha Latte",
                "quantity": 1,
                "unit_price": 55000,
                "line_total": 55000,
            }
        ],
    },
    {
        "id": "order-2",
        "order_code": "ORD-0002",
        "customer_id": "customer-2",
        "order_type": "delivery",
        "status": "ready_for_delivery",
        "payment_status": "unpaid",
        "subtotal": 65000,
        "discount_amount": 0,
        "total_amount": 65000,
        "customer_name": "Tran Binh",
        "customer_phone": "0987654321",
        "delivery_address": "Quan 3, TP.HCM",
        "delivery_latitude": 10.7829,
        "delivery_longitude": 106.6934,
        "created_at": "2026-06-01T09:15:00",
        "items": [
            {
                "product_id": "product-matcha-frappe",
                "product_name": "Matcha Frappe",
                "quantity": 1,
                "unit_price": 65000,
                "line_total": 65000,
            }
        ],
    },
]


@router.get("")
async def list_orders() -> dict[str, Any]:
    return success_response(data=MOCK_ORDERS)


@router.post("")
async def create_order(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    return success_response(
        message="Mock order created successfully",
        data={
            "id": "order-mock-created",
            "order_code": "ORD-MOCK",
            "status": "pending",
            "payment_status": "unpaid",
            "payload": payload,
        },
    )


@router.get("/{order_id}")
async def get_order(order_id: str) -> dict[str, Any]:
    order = next((item for item in MOCK_ORDERS if item["id"] == order_id), None)
    if order is None:
        raise HTTPException(status_code=404, detail="order_not_found")
    return success_response(data=order)


@router.post("/{order_id}/complete")
async def complete_order(order_id: str) -> dict[str, Any]:
    return success_response(
        message="Mock order completed successfully",
        data={
            "id": order_id,
            "status": "completed",
            "inventory_deducted": True,
            "financial_records_created": True,
        },
    )
