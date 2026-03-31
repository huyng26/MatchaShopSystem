from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, model_validator
from app.models.finance import CostCategory


class OperationalCostBase(BaseModel):
    category: CostCategory
    amount: Decimal
    period_month: int
    period_year: int
    description: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_period(self) -> "OperationalCostBase":
        if not 1 <= self.period_month <= 12:
            raise ValueError("period_month must be between 1 and 12")
        return self


class OperationalCostCreate(OperationalCostBase):
    pass


class OperationalCostUpdate(BaseModel):
    category: CostCategory | None = None
    amount: Decimal | None = None
    period_month: int | None = None
    period_year: int | None = None
    description: str | None = None
    notes: str | None = None


class OperationalCostResponse(OperationalCostBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recorded_at: datetime
    updated_at: datetime


class ProfitSummary(BaseModel):
    period_month: int
    period_year: int
    revenue: Decimal
    cogs: Decimal
    operational_costs: Decimal
    net_profit: Decimal
    order_count: int
