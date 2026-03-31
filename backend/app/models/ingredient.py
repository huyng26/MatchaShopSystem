from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "kg", "g", "L", "ml", "pack"
    cost_per_unit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    current_stock: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)
    min_stock_threshold: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    purchases: Mapped[list["IngredientPurchase"]] = relationship(back_populates="ingredient")
    product_ingredients: Mapped[list["ProductIngredient"]] = relationship(back_populates="ingredient")  # noqa: F821


class IngredientPurchase(Base):
    __tablename__ = "ingredient_purchases"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredients.id"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    supplier: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(String(500))
    purchased_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    ingredient: Mapped["Ingredient"] = relationship(back_populates="purchases")
