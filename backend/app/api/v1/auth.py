from typing import Any

from fastapi import APIRouter, Body

from app.core.responses import success_response

router = APIRouter()

# Temporary mock data for early frontend integration.
# Replace this with auth_service calls when implementing real authentication.
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


@router.post("/login")
async def login(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    email = payload.get("email", "admin@matcha.local")
    user = next((item for item in MOCK_USERS if item["email"] == email), MOCK_USERS[0])
    return success_response(
        message="Mock login successfully",
        data={
            "access_token": "mock-access-token",
            "refresh_token": "mock-refresh-token",
            "token_type": "bearer",
            "user": user,
        },
    )


@router.get("/me")
async def me() -> dict[str, Any]:
    return success_response(data=MOCK_USERS[0])
