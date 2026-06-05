from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.finance import FinancialRecordType
from app.schemas.finance import ExpenseCreate
from app.services import finance_service
from app.services.errors import ServiceError


class FakeDb:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1


def make_expense(**overrides):
    now = datetime.now(timezone.utc)
    values = {
        "id": uuid4(),
        "category": "utilities",
        "description": "Electricity bill",
        "amount": Decimal("1200000.00"),
        "expense_month": date(2026, 6, 1),
        "invoice_photo_url": None,
        "created_by": uuid4(),
        "created_at": now,
        "updated_at": now,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


@pytest.mark.asyncio
async def test_create_expense_commits_and_records_operating_expense(monkeypatch):
    db = FakeDb()
    created_by = uuid4()
    expense = make_expense(created_by=created_by)
    captured = {}

    async def create_expense(db, **kwargs):
        captured["expense"] = kwargs
        return expense

    async def create_financial_record(db, **kwargs):
        captured["financial_record"] = kwargs
        return SimpleNamespace(id=uuid4(), **kwargs)

    monkeypatch.setattr(
        finance_service.finance_repo,
        "create_expense",
        create_expense,
    )
    monkeypatch.setattr(
        finance_service.finance_repo,
        "create_financial_record",
        create_financial_record,
    )

    payload = ExpenseCreate(
        category="utilities",
        description="Electricity bill",
        amount=Decimal("1200000.00"),
        expense_month=date(2026, 6, 1),
        invoice_photo_url=None,
    )

    result = await finance_service.create_expense(
        db,
        payload,
        created_by=created_by,
    )

    assert result is expense
    assert db.commits == 1
    assert db.rollbacks == 0
    assert captured["expense"]["created_by"] == created_by
    assert captured["financial_record"]["record_type"] == (
        FinancialRecordType.OPERATING_EXPENSE
    )
    assert captured["financial_record"]["source_type"] == "expense"
    assert captured["financial_record"]["source_id"] == expense.id
    assert captured["financial_record"]["amount"] == expense.amount
    assert captured["financial_record"]["record_date"] == expense.expense_month
    assert captured["financial_record"]["locked"] is False


@pytest.mark.asyncio
async def test_create_expense_rolls_back_when_financial_record_fails(monkeypatch):
    db = FakeDb()
    expense = make_expense()

    async def create_expense(db, **kwargs):
        return expense

    async def create_financial_record(db, **kwargs):
        raise RuntimeError("ledger failed")

    monkeypatch.setattr(
        finance_service.finance_repo,
        "create_expense",
        create_expense,
    )
    monkeypatch.setattr(
        finance_service.finance_repo,
        "create_financial_record",
        create_financial_record,
    )

    payload = ExpenseCreate(
        category="utilities",
        description="Electricity bill",
        amount=Decimal("1200000.00"),
        expense_month=date(2026, 6, 1),
    )

    with pytest.raises(RuntimeError):
        await finance_service.create_expense(db, payload, created_by=uuid4())

    assert db.commits == 0
    assert db.rollbacks == 1


@pytest.mark.asyncio
async def test_create_expense_rejects_non_positive_amount():
    db = FakeDb()
    payload = ExpenseCreate.model_construct(
        category="utilities",
        description="Electricity bill",
        amount=Decimal("0"),
        expense_month=date(2026, 6, 1),
        invoice_photo_url=None,
    )

    with pytest.raises(ServiceError) as error:
        await finance_service.create_expense(db, payload, created_by=uuid4())

    assert error.value.code == "expense_amount_must_be_positive"
    assert db.commits == 0
    assert db.rollbacks == 0


@pytest.mark.asyncio
async def test_create_staff_wage_expense_records_operating_expense(monkeypatch):
    db = FakeDb()
    created_by = uuid4()
    expense = make_expense(
        category=finance_service.STAFF_WAGE_CATEGORY,
        description="Staff wages for 2026-06",
        amount=Decimal("25000000.00"),
        expense_month=date(2026, 6, 1),
        created_by=created_by,
    )
    captured = {}

    async def get_expense_by_category_and_month(db, **kwargs):
        captured["duplicate_check"] = kwargs
        return None

    async def sum_active_staff_salaries(db):
        return Decimal("25000000.00"), 3

    async def create_expense(db, **kwargs):
        captured["expense"] = kwargs
        return expense

    async def create_financial_record(db, **kwargs):
        captured["financial_record"] = kwargs
        return SimpleNamespace(id=uuid4(), **kwargs)

    monkeypatch.setattr(
        finance_service.finance_repo,
        "get_expense_by_category_and_month",
        get_expense_by_category_and_month,
    )
    monkeypatch.setattr(
        finance_service.staff_repo,
        "sum_active_staff_salaries",
        sum_active_staff_salaries,
    )
    monkeypatch.setattr(
        finance_service.finance_repo,
        "create_expense",
        create_expense,
    )
    monkeypatch.setattr(
        finance_service.finance_repo,
        "create_financial_record",
        create_financial_record,
    )

    result = await finance_service.create_staff_wage_expense(
        db,
        month="2026-06",
        created_by=created_by,
    )

    assert db.commits == 1
    assert db.rollbacks == 0
    assert result.staff_count == 3
    assert result.total_salary == Decimal("25000000.00")
    assert result.expense.id == expense.id
    assert captured["duplicate_check"] == {
        "category": finance_service.STAFF_WAGE_CATEGORY,
        "expense_month": date(2026, 6, 1),
    }
    assert captured["expense"]["category"] == finance_service.STAFF_WAGE_CATEGORY
    assert captured["expense"]["description"] == "Staff wages for 2026-06"
    assert captured["expense"]["amount"] == Decimal("25000000.00")
    assert captured["expense"]["expense_month"] == date(2026, 6, 1)
    assert captured["expense"]["created_by"] == created_by
    assert captured["financial_record"]["record_type"] == (
        FinancialRecordType.OPERATING_EXPENSE
    )
    assert captured["financial_record"]["source_type"] == "expense"
    assert captured["financial_record"]["source_id"] == expense.id
    assert captured["financial_record"]["amount"] == expense.amount
    assert captured["financial_record"]["record_date"] == expense.expense_month
    assert captured["financial_record"]["locked"] is False


@pytest.mark.asyncio
async def test_create_staff_wage_expense_rejects_duplicate(monkeypatch):
    db = FakeDb()

    async def get_expense_by_category_and_month(db, **kwargs):
        return make_expense(category=finance_service.STAFF_WAGE_CATEGORY)

    monkeypatch.setattr(
        finance_service.finance_repo,
        "get_expense_by_category_and_month",
        get_expense_by_category_and_month,
    )

    with pytest.raises(ServiceError) as error:
        await finance_service.create_staff_wage_expense(
            db,
            month="2026-06",
            created_by=uuid4(),
        )

    assert error.value.code == "staff_wage_expense_already_exists"
    assert error.value.status_code == 409
    assert db.commits == 0
    assert db.rollbacks == 0


@pytest.mark.asyncio
async def test_create_staff_wage_expense_rejects_zero_total(monkeypatch):
    db = FakeDb()

    async def get_expense_by_category_and_month(db, **kwargs):
        return None

    async def sum_active_staff_salaries(db):
        return Decimal("0.00"), 0

    monkeypatch.setattr(
        finance_service.finance_repo,
        "get_expense_by_category_and_month",
        get_expense_by_category_and_month,
    )
    monkeypatch.setattr(
        finance_service.staff_repo,
        "sum_active_staff_salaries",
        sum_active_staff_salaries,
    )

    with pytest.raises(ServiceError) as error:
        await finance_service.create_staff_wage_expense(
            db,
            month="2026-06",
            created_by=uuid4(),
        )

    assert error.value.code == "staff_wage_total_is_zero"
    assert db.commits == 0
    assert db.rollbacks == 0


@pytest.mark.asyncio
async def test_create_staff_wage_expense_rejects_invalid_month():
    db = FakeDb()

    with pytest.raises(ServiceError) as error:
        await finance_service.create_staff_wage_expense(
            db,
            month="2026-6",
            created_by=uuid4(),
        )

    assert error.value.code == "month_must_use_yyyy_mm_format"
    assert db.commits == 0
    assert db.rollbacks == 0


@pytest.mark.asyncio
async def test_create_staff_wage_expense_rolls_back_when_ledger_fails(monkeypatch):
    db = FakeDb()
    expense = make_expense(
        category=finance_service.STAFF_WAGE_CATEGORY,
        amount=Decimal("25000000.00"),
        expense_month=date(2026, 6, 1),
    )

    async def get_expense_by_category_and_month(db, **kwargs):
        return None

    async def sum_active_staff_salaries(db):
        return Decimal("25000000.00"), 3

    async def create_expense(db, **kwargs):
        return expense

    async def create_financial_record(db, **kwargs):
        raise RuntimeError("ledger failed")

    monkeypatch.setattr(
        finance_service.finance_repo,
        "get_expense_by_category_and_month",
        get_expense_by_category_and_month,
    )
    monkeypatch.setattr(
        finance_service.staff_repo,
        "sum_active_staff_salaries",
        sum_active_staff_salaries,
    )
    monkeypatch.setattr(
        finance_service.finance_repo,
        "create_expense",
        create_expense,
    )
    monkeypatch.setattr(
        finance_service.finance_repo,
        "create_financial_record",
        create_financial_record,
    )

    with pytest.raises(RuntimeError):
        await finance_service.create_staff_wage_expense(
            db,
            month="2026-06",
            created_by=uuid4(),
        )

    assert db.commits == 0
    assert db.rollbacks == 1


@pytest.mark.asyncio
async def test_get_finance_summary_calculates_monthly_profit(monkeypatch):
    db = FakeDb()
    captured = {}

    async def get_monthly_totals(db, *, month_start, next_month_start):
        captured["month_start"] = month_start
        captured["next_month_start"] = next_month_start
        return {
            FinancialRecordType.REVENUE: Decimal("550000.00"),
            FinancialRecordType.MATERIAL_COST: Decimal("180000.00"),
            FinancialRecordType.OPERATING_EXPENSE: Decimal("120000.00"),
        }

    monkeypatch.setattr(
        finance_service.finance_repo,
        "get_monthly_totals",
        get_monthly_totals,
    )

    summary = await finance_service.get_finance_summary(db, month="2026-06")

    assert captured["month_start"] == date(2026, 6, 1)
    assert captured["next_month_start"] == date(2026, 7, 1)
    assert summary.revenue == Decimal("550000.00")
    assert summary.material_cost == Decimal("180000.00")
    assert summary.operating_expense == Decimal("120000.00")
    assert summary.net_profit == Decimal("250000.00")


def test_parse_month_rejects_invalid_format():
    with pytest.raises(ServiceError) as error:
        finance_service.parse_month("2026-6")

    assert error.value.code == "month_must_use_yyyy_mm_format"
