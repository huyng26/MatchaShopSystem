from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.finance import FinancialRecordType


class ExpenseCreate(BaseModel):
    category: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    amount: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)
    expense_month: date
    invoice_photo_url: str | None = None


class ExpenseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category: str
    description: str
    amount: Decimal
    expense_month: date
    invoice_photo_url: str | None = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class FinancialRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    record_type: FinancialRecordType
    source_type: str
    source_id: UUID
    amount: Decimal
    record_date: date
    locked: bool
    created_at: datetime


class FinanceSummaryRead(BaseModel):
    revenue: Decimal
    material_cost: Decimal
    operating_expense: Decimal
    net_profit: Decimal
