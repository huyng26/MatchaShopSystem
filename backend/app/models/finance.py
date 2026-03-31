from datetime import datetime
from decimal import Decimal
import enum
from sqlalchemy import String, Numeric, DateTime, Enum, Text, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CostCategory(str, enum.Enum):
    electricity = "electricity"
    water = "water"
    staff = "staff"
    rent = "rent"
    other = "other"


class OperationalCost(Base):
    """Manually recorded operational expenses per period."""

    __tablename__ = "operational_costs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    category: Mapped[CostCategory] = mapped_column(Enum(CostCategory), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    period_month: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-12
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
