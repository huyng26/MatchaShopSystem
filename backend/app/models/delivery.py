from datetime import datetime
import enum
from sqlalchemy import String, DateTime, ForeignKey, Enum, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class BatchStatus(str, enum.Enum):
    pending = "pending"       # not yet dispatched
    dispatched = "dispatched" # driver is on the way
    completed = "completed"   # all orders delivered
    cancelled = "cancelled"


class DeliveryStatus(str, enum.Enum):
    pending = "pending"
    in_transit = "in_transit"
    delivered = "delivered"
    failed = "failed"


class DeliveryBatch(Base):
    """Groups multiple delivery orders into one driver trip."""

    __tablename__ = "delivery_batches"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    batch_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    driver_name: Mapped[str | None] = mapped_column(String(255))
    driver_phone: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[BatchStatus] = mapped_column(Enum(BatchStatus), default=BatchStatus.pending)
    notes: Mapped[str | None] = mapped_column(Text)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    delivery_orders: Mapped[list["DeliveryOrder"]] = relationship(back_populates="batch")


class DeliveryOrder(Base):
    """Links a delivery Order to a batch with address and status."""

    __tablename__ = "delivery_orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True, nullable=False)
    batch_id: Mapped[int | None] = mapped_column(ForeignKey("delivery_batches.id"))
    delivery_address: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[DeliveryStatus] = mapped_column(Enum(DeliveryStatus), default=DeliveryStatus.pending)
    delivery_notes: Mapped[str | None] = mapped_column(Text)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    order: Mapped["Order"] = relationship(back_populates="delivery_order")  # noqa: F821
    batch: Mapped["DeliveryBatch | None"] = relationship(back_populates="delivery_orders")
