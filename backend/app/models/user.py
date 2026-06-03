from enum import Enum

from sqlalchemy import DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import Column

from app.models.base import Base


def enum_values(enum_cls: type[Enum]) -> list[str]:
    return [member.value for member in enum_cls]


class UserRole(str, Enum):
    ADMIN = "admin"
    INVENTORY_MANAGER = "inventory_manager"
    DELIVERY_MANAGER = "delivery_manager"
    CASHIER = "cashier"
    SHIPPER = "shipper"


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"


class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    email = Column(String(255), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(
        SQLEnum(
            UserRole,
            name="user_role",
            values_callable=enum_values,
            native_enum=True,
        ),
        nullable=False,
    )
    status = Column(
        SQLEnum(
            UserStatus,
            name="user_status",
            values_callable=enum_values,
            native_enum=True,
        ),
        nullable=False,
        server_default=text("'active'::user_status"),
    )
    last_login_at = Column(DateTime(timezone=True))
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    deleted_at = Column(DateTime(timezone=True))

    inventory_purchases = relationship("InventoryPurchase", back_populates="creator")
    inventory_movements = relationship("InventoryMovement", back_populates="creator")
    orders = relationship("Order", back_populates="creator")
    payments = relationship("Payment", back_populates="creator")
