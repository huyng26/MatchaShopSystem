from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DashboardTodayRead(BaseModel):
    date: date
    revenue: Decimal
    order_count: int = Field(..., ge=0)
    completed_order_count: int = Field(..., ge=0)
    delivery_queue_count: int = Field(..., ge=0)
    low_stock_count: int = Field(..., ge=0)


class DashboardProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    selling_price: Decimal


class BestSellingProductRead(BaseModel):
    product: DashboardProductRead
    quantity_sold: int = Field(..., ge=0)
    revenue: Decimal = Field(..., ge=0)


class DeliveryPerformanceRead(BaseModel):
    total_trips: int = Field(..., ge=0)
    completed_trips: int = Field(..., ge=0)
    average_delivery_minutes: Decimal = Field(..., ge=0)
    cod_pending: Decimal = Field(..., ge=0)
