from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import Column

from app.models.base import Base
from app.models.user import enum_values


class OrderType(str, Enum):
    INSTORE = "instore"
    DELIVERY = "delivery"


class OrderStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    READY_FOR_DELIVERY = "ready_for_delivery"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OrderPaymentStatus(str, Enum):
    UNPAID = "unpaid"
    PAID = "paid"
    REFUNDED = "refunded"


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("subtotal >= 0", name="orders_subtotal_non_negative"),
        CheckConstraint("discount_amount >= 0", name="orders_discount_non_negative"),
        CheckConstraint("total_amount >= 0", name="orders_total_non_negative"),
        CheckConstraint(
            "delivery_latitude IS NULL OR delivery_latitude BETWEEN -90 AND 90",
            name="orders_delivery_latitude_valid",
        ),
        CheckConstraint(
            "delivery_longitude IS NULL OR delivery_longitude BETWEEN -180 AND 180",
            name="orders_delivery_longitude_valid",
        ),
    )

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    order_code = Column(String(100), nullable=False, unique=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"))
    order_type = Column(
        SQLEnum(
            OrderType,
            name="order_type",
            values_callable=enum_values,
            native_enum=True,
        ),
        nullable=False,
    )
    status = Column(
        SQLEnum(
            OrderStatus,
            name="order_status",
            values_callable=enum_values,
            native_enum=True,
        ),
        nullable=False,
        server_default=text("'pending'::order_status"),
    )
    payment_status = Column(
        SQLEnum(
            OrderPaymentStatus,
            name="order_payment_status",
            values_callable=enum_values,
            native_enum=True,
        ),
        nullable=False,
        server_default=text("'unpaid'::order_payment_status"),
    )
    subtotal = Column(Numeric(12, 2), nullable=False, server_default=text("0"))
    discount_amount = Column(Numeric(12, 2), nullable=False, server_default=text("0"))
    total_amount = Column(Numeric(12, 2), nullable=False, server_default=text("0"))
    customer_name = Column(String(255))
    customer_phone = Column(String(50))
    delivery_address = Column(Text)
    delivery_latitude = Column(Numeric(10, 7))
    delivery_longitude = Column(Numeric(10, 7))
    delivery_formatted_address = Column(Text)
    delivery_place_id = Column(String(255))
    geocoded_at = Column(DateTime(timezone=True))
    geocoding_status = Column(String(50))
    map_provider = Column(String(50))
    note = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    completed_at = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))
    deleted_at = Column(DateTime(timezone=True))

    customer = relationship("Customer", back_populates="orders")
    creator = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
    payments = relationship("Payment", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="order_items_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="order_items_unit_price_non_negative"),
        CheckConstraint("line_total >= 0", name="order_items_line_total_non_negative"),
    )

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    line_total = Column(Numeric(12, 2), nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
