from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.finance import FinancialRecordType


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
