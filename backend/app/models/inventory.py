from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import Column, UniqueConstraint

from app.models.base import Base
from app.models.user import enum_values


class InventoryMovementType(str, Enum):
    PURCHASE = "purchase"
    SALE_DEDUCTION = "sale_deduction"
    CANCELLATION_RESTORE = "cancellation_restore"
    MANUAL_ADJUSTMENT = "manual_adjustment"
    WASTE = "waste"


class ProductRecipe(Base):
    __tablename__ = "product_recipes"
    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "ingredient_id",
            name="product_recipes_product_ingredient_unique",
        ),
        CheckConstraint(
            "quantity_per_serving > 0", name="product_recipes_quantity_positive"
        ),
    )

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    ingredient_id = Column(
        UUID(as_uuid=True), ForeignKey("ingredients.id"), nullable=False
    )
    quantity_per_serving = Column(Numeric(12, 3), nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    product = relationship("Product", back_populates="recipe_rows")
    ingredient = relationship("Ingredient", back_populates="recipe_rows")


class InventoryPurchase(Base):
    __tablename__ = "inventory_purchases"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="inventory_purchases_quantity_positive"),
        CheckConstraint(
            "cost_per_unit >= 0",
            name="inventory_purchases_cost_per_unit_non_negative",
        ),
        CheckConstraint(
            "total_cost >= 0", name="inventory_purchases_total_cost_non_negative"
        ),
    )

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    ingredient_id = Column(
        UUID(as_uuid=True), ForeignKey("ingredients.id"), nullable=False
    )
    quantity = Column(Numeric(12, 3), nullable=False)
    cost_per_unit = Column(Numeric(12, 2), nullable=False)
    total_cost = Column(Numeric(12, 2), nullable=False)
    supplier_name = Column(String(255))
    notes = Column(Text)
    purchased_at = Column(DateTime(timezone=True), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    ingredient = relationship("Ingredient", back_populates="purchases")
    creator = relationship("User", back_populates="inventory_purchases")


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"
    __table_args__ = (
        CheckConstraint(
            "quantity_change <> 0",
            name="inventory_movements_quantity_change_not_zero",
        ),
        CheckConstraint(
            "stock_before >= 0", name="inventory_movements_stock_before_non_negative"
        ),
        CheckConstraint(
            "stock_after >= 0", name="inventory_movements_stock_after_non_negative"
        ),
        CheckConstraint(
            "unit_cost IS NULL OR unit_cost >= 0",
            name="inventory_movements_unit_cost_non_negative",
        ),
    )

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    ingredient_id = Column(
        UUID(as_uuid=True), ForeignKey("ingredients.id"), nullable=False
    )
    movement_type = Column(
        SQLEnum(
            InventoryMovementType,
            name="inventory_movement_type",
            values_callable=enum_values,
            native_enum=True,
        ),
        nullable=False,
    )
    quantity_change = Column(Numeric(12, 3), nullable=False)
    stock_before = Column(Numeric(12, 3), nullable=False)
    stock_after = Column(Numeric(12, 3), nullable=False)
    unit_cost = Column(Numeric(12, 2))
    reference_type = Column(String(100))
    reference_id = Column(UUID(as_uuid=True))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    ingredient = relationship("Ingredient", back_populates="movements")
    creator = relationship("User", back_populates="inventory_movements")
