from sqlalchemy import CheckConstraint, DateTime, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import Column

from app.models.base import Base


class Ingredient(Base):
    __tablename__ = "ingredients"
    __table_args__ = (
        CheckConstraint(
            "current_stock >= 0", name="ingredients_current_stock_non_negative"
        ),
        CheckConstraint(
            "cost_per_unit >= 0", name="ingredients_cost_per_unit_non_negative"
        ),
        CheckConstraint(
            "minimum_threshold >= 0",
            name="ingredients_minimum_threshold_non_negative",
        ),
    )

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    name = Column(String(255), nullable=False, unique=True)
    unit = Column(String(50), nullable=False)
    current_stock = Column(Numeric(12, 3), nullable=False, server_default=text("0"))
    cost_per_unit = Column(Numeric(12, 2), nullable=False)
    minimum_threshold = Column(Numeric(12, 3), nullable=False, server_default=text("0"))
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    deleted_at = Column(DateTime(timezone=True))

    recipe_rows = relationship("ProductRecipe", back_populates="ingredient")
    purchases = relationship("InventoryPurchase", back_populates="ingredient")
    movements = relationship("InventoryMovement", back_populates="ingredient")
