from typing import Any

from fastapi import APIRouter, Body

from app.core.responses import success_response

router = APIRouter()

# Temporary mock data for early frontend integration.
# Replace this with finance_service calls when implementing real APIs.
MOCK_EXPENSES = [
    {
        "id": "expense-1",
        "category": "utilities",
        "description": "Electricity bill",
        "amount": 1200000,
        "expense_month": "2026-06-01",
    }
]

MOCK_FINANCIAL_RECORDS = [
    {
        "id": "finance-1",
        "record_type": "revenue",
        "source_type": "order",
        "source_id": "order-1",
        "amount": 55000,
        "record_date": "2026-06-01",
    }
]


@router.get("/summary")
async def get_finance_summary() -> dict[str, Any]:
    return success_response(
        data={
            "revenue": 55000,
            "material_cost": 18000,
            "operating_expense": 1200000,
            "net_profit": -1163000,
        }
    )


@router.get("/expenses")
async def list_expenses() -> dict[str, Any]:
    return success_response(data=MOCK_EXPENSES)


@router.post("/expenses")
async def create_expense(
    payload: dict[str, Any] = Body(default_factory=dict),
) -> dict[str, Any]:
    return success_response(
        message="Mock expense created successfully",
        data={"id": "expense-mock-created", **payload},
    )


@router.get("/records")
async def list_financial_records() -> dict[str, Any]:
    return success_response(data=MOCK_FINANCIAL_RECORDS)
