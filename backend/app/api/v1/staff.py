from typing import Any

from fastapi import APIRouter

from app.core.responses import success_response

router = APIRouter()

# Temporary mock data for early frontend integration.
# Replace this with staff_service calls when implementing real APIs.
MOCK_STAFF = [
    {
        "id": "staff-admin",
        "user_id": "user-admin",
        "full_name": "Admin User",
        "phone": "0900000001",
        "email": "admin@matcha.local",
        "role": "admin",
        "status": "active",
    },
    {
        "id": "staff-shipper",
        "user_id": None,
        "full_name": "Demo Shipper",
        "phone": "0900000002",
        "email": "shipper@matcha.local",
        "role": "shipper",
        "status": "active",
    },
]

MOCK_STAFF_TASKS = [
    {
        "id": "task-1",
        "staff_id": "staff-admin",
        "title": "Review low stock ingredients",
        "due_date": "2026-06-01",
        "priority": "medium",
        "status": "pending",
    }
]


@router.get("")
async def list_staff() -> dict[str, Any]:
    return success_response(data=MOCK_STAFF)


@router.get("/tasks")
async def list_staff_tasks() -> dict[str, Any]:
    return success_response(data=MOCK_STAFF_TASKS)
