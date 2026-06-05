from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.finance import ExpenseCreate, ExpenseRead, StaffWageExpenseRead


def test_expense_create_rejects_non_positive_amount() -> None:
    with pytest.raises(ValidationError):
        ExpenseCreate(
            category="utilities",
            description="Electricity bill",
            amount=Decimal("0"),
            expense_month=date(2026, 6, 1),
        )


def test_expense_read_serializes_orm_like_object() -> None:
    now = datetime.now(timezone.utc)
    expense_id = uuid4()
    created_by = uuid4()
    expense = SimpleNamespace(
        id=expense_id,
        category="utilities",
        description="Electricity bill",
        amount=Decimal("1200000.00"),
        expense_month=date(2026, 6, 1),
        invoice_photo_url=None,
        created_by=created_by,
        created_at=now,
        updated_at=now,
    )

    result = ExpenseRead.model_validate(expense)

    assert result.id == expense_id
    assert result.amount == Decimal("1200000.00")
    assert result.created_by == created_by


def test_staff_wage_expense_read_serializes_nested_expense() -> None:
    now = datetime.now(timezone.utc)
    expense_id = uuid4()
    created_by = uuid4()
    expense = SimpleNamespace(
        id=expense_id,
        category="staff_wage",
        description="Staff wages for 2026-06",
        amount=Decimal("25000000.00"),
        expense_month=date(2026, 6, 1),
        invoice_photo_url=None,
        created_by=created_by,
        created_at=now,
        updated_at=now,
    )

    result = StaffWageExpenseRead(
        expense=ExpenseRead.model_validate(expense),
        staff_count=3,
        total_salary=Decimal("25000000.00"),
    )

    assert result.expense.id == expense_id
    assert result.expense.category == "staff_wage"
    assert result.staff_count == 3
    assert result.total_salary == Decimal("25000000.00")
