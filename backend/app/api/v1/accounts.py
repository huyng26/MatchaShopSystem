from typing import Any

from fastapi import APIRouter

from app.core.responses import success_response

router = APIRouter()

# Temporary mock data for early frontend integration.
# Replace this with account_service calls when implementing real APIs.
MOCK_USERS = [
    {
        "id": "user-admin",
        "email": "admin@matcha.local",
        "role": "admin",
        "status": "active",
    },
    {
        "id": "user-cashier",
        "email": "cashier@matcha.local",
        "role": "cashier",
        "status": "active",
    },
]


@router.get("")
async def list_accounts() -> dict[str, Any]:
    return success_response(data=MOCK_USERS)
