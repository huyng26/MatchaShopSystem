from datetime import datetime
from decimal import Decimal
import enum
import uuid

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class InventoryMovementType(str, enum.Enum):
    purchase = "purchase"
    sale_deduction = "sale_deduction"
    cancellation_restore = "cancellation_restore"
    manual_adjustment = "manual_adjustment"
    waste = "waste"


class Ingredient(Base):
    __tablename__ = "ingredients"
    __table_args__ = (
        CheckConstraint("current_stock >= 0", name="ck_ingredients_current_stock_non_negative"),
        CheckConstraint("cost_per_unit >= 0", name="ck_ingredients_cost_per_unit_non_negative"),
        CheckConstraint("minimum_threshold >= 0", name="ck_ingredients_minimum_threshold_non_negative"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    current_stock: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False, default=Decimal("0"))
    cost_per_unit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    minimum_threshold: Mapped[Decimal] = mapped_column(
        Numeric(12, 3), nullable=False, default=Decimal("0")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    purchases: Mapped[list["InventoryPurchase"]] = relationship(back_populates="ingredient")
    movements: Mapped[list["InventoryMovement"]] = relationship(back_populates="ingredient")
    recipes: Mapped[list["ProductRecipe"]] = relationship(back_populates="ingredient")  # noqa: F821


class InventoryPurchase(Base):
    __tablename__ = "inventory_purchases"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_inventory_purchases_quantity_positive"),
        CheckConstraint("cost_per_unit >= 0", name="ck_inventory_purchases_cost_non_negative"),
        CheckConstraint("total_cost >= 0", name="ck_inventory_purchases_total_non_negative"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    ingredient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ingredients.id"), nullable=False, index=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    cost_per_unit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    supplier_name: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)
    purchased_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    ingredient: Mapped["Ingredient"] = relationship(back_populates="purchases")


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"
    __table_args__ = (
        CheckConstraint("quantity_change <> 0", name="ck_inventory_movements_quantity_non_zero"),
        CheckConstraint("stock_before >= 0", name="ck_inventory_movements_stock_before_non_negative"),
        CheckConstraint("stock_after >= 0", name="ck_inventory_movements_stock_after_non_negative"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    ingredient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ingredients.id"), nullable=False, index=True
    )
    movement_type: Mapped[InventoryMovementType] = mapped_column(
        Enum(InventoryMovementType), nullable=False
    )
    quantity_change: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    stock_before: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    stock_after: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    reference_type: Mapped[str | None] = mapped_column(String(100))
    reference_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    ingredient: Mapped["Ingredient"] = relationship(back_populates="movements")
