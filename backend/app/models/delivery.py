from enum import Enum

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy import Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text
from sqlalchemy.sql.schema import Column

from app.models.base import Base
from app.models.user import enum_values


class DeliveryTripStatus(str, Enum):
    PENDING_DISPATCH = "pending_dispatch"
    ASSIGNED = "assigned"
    IN_TRANSIT = "in_transit"
    COMPLETED = "completed"
    RECONCILED = "reconciled"
    CANCELLED = "cancelled"


class DeliveryTripOrderStatus(str, Enum):
    ASSIGNED = "assigned"
    DELIVERED = "delivered"
    FAILED = "failed"


class CodReconciliationStatus(str, Enum):
    CONFIRMED = "confirmed"
    FLAGGED_FOR_REVIEW = "flagged_for_review"


class DeliveryTrip(Base):
    __tablename__ = "delivery_trips"
    __table_args__ = (
        CheckConstraint(
            "expected_cod_amount >= 0",
            name="delivery_trips_expected_cod_non_negative",
        ),
        CheckConstraint(
            "actual_cod_amount IS NULL OR actual_cod_amount >= 0",
            name="delivery_trips_actual_cod_non_negative",
        ),
    )

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    trip_code = Column(String(100), nullable=False, unique=True)
    shipper_id = Column(UUID(as_uuid=True), ForeignKey("staff_profiles.id"))
    status = Column(
        SQLEnum(
            DeliveryTripStatus,
            name="delivery_trip_status",
            values_callable=enum_values,
            native_enum=True,
        ),
        nullable=False,
        server_default=text("'pending_dispatch'::delivery_trip_status"),
    )
    expected_cod_amount = Column(
        Numeric(12, 2), nullable=False, server_default=text("0")
    )
    actual_cod_amount = Column(Numeric(12, 2))
    discrepancy_amount = Column(Numeric(12, 2))
    discrepancy_reason = Column(Text)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    reconciled_at = Column(DateTime(timezone=True))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    deleted_at = Column(DateTime(timezone=True))

    shipper = relationship("StaffProfile")
    creator = relationship("User")
    trip_orders = relationship(
        "DeliveryTripOrder",
        back_populates="trip",
        order_by="DeliveryTripOrder.stop_order",
    )
    location_logs = relationship("DeliveryLocationLog", back_populates="trip")
    reconciliation = relationship(
        "CodReconciliation",
        back_populates="trip",
        uselist=False,
    )


class DeliveryTripOrder(Base):
    __tablename__ = "delivery_trip_orders"
    __table_args__ = (
        CheckConstraint(
            "stop_order > 0",
            name="delivery_trip_orders_stop_order_positive",
        ),
        CheckConstraint(
            "cod_collected >= 0",
            name="delivery_trip_orders_cod_collected_non_negative",
        ),
    )

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    trip_id = Column(
        UUID(as_uuid=True),
        ForeignKey("delivery_trips.id"),
        nullable=False,
    )
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    stop_order = Column(Integer, nullable=False)
    status = Column(
        SQLEnum(
            DeliveryTripOrderStatus,
            name="delivery_trip_order_status",
            values_callable=enum_values,
            native_enum=True,
        ),
        nullable=False,
        server_default=text("'assigned'::delivery_trip_order_status"),
    )
    cod_collected = Column(Numeric(12, 2), nullable=False, server_default=text("0"))
    delivered_at = Column(DateTime(timezone=True))
    failed_at = Column(DateTime(timezone=True))
    failed_reason = Column(Text)
    note = Column(Text)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    trip = relationship("DeliveryTrip", back_populates="trip_orders")
    order = relationship("Order")


class DeliveryLocationLog(Base):
    __tablename__ = "delivery_location_logs"
    __table_args__ = (
        CheckConstraint(
            "latitude BETWEEN -90 AND 90",
            name="delivery_location_logs_latitude_valid",
        ),
        CheckConstraint(
            "longitude BETWEEN -180 AND 180",
            name="delivery_location_logs_longitude_valid",
        ),
    )

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    trip_id = Column(
        UUID(as_uuid=True),
        ForeignKey("delivery_trips.id"),
        nullable=False,
    )
    shipper_id = Column(
        UUID(as_uuid=True),
        ForeignKey("staff_profiles.id"),
        nullable=False,
    )
    latitude = Column(Numeric(10, 7), nullable=False)
    longitude = Column(Numeric(10, 7), nullable=False)
    recorded_at = Column(DateTime(timezone=True), nullable=False)

    trip = relationship("DeliveryTrip", back_populates="location_logs")
    shipper = relationship("StaffProfile")


class CodReconciliation(Base):
    __tablename__ = "cod_reconciliations"
    __table_args__ = (
        CheckConstraint(
            "expected_amount >= 0",
            name="cod_reconciliations_expected_amount_non_negative",
        ),
        CheckConstraint(
            "actual_amount >= 0",
            name="cod_reconciliations_actual_amount_non_negative",
        ),
    )

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    trip_id = Column(
        UUID(as_uuid=True),
        ForeignKey("delivery_trips.id"),
        nullable=False,
        unique=True,
    )
    shipper_id = Column(
        UUID(as_uuid=True),
        ForeignKey("staff_profiles.id"),
        nullable=False,
    )
    expected_amount = Column(Numeric(12, 2), nullable=False)
    actual_amount = Column(Numeric(12, 2), nullable=False)
    discrepancy_amount = Column(Numeric(12, 2), nullable=False)
    discrepancy_reason = Column(Text)
    status = Column(
        SQLEnum(
            CodReconciliationStatus,
            name="cod_reconciliation_status",
            values_callable=enum_values,
            native_enum=True,
        ),
        nullable=False,
        server_default=text("'confirmed'::cod_reconciliation_status"),
    )
    reconciled_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reconciled_at = Column(DateTime(timezone=True), nullable=False)

    trip = relationship("DeliveryTrip", back_populates="reconciliation")
    shipper = relationship("StaffProfile")
    reconciler = relationship("User")
