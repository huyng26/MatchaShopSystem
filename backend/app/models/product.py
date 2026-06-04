from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import Column

from app.models.base import Base


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("selling_price > 0", name="products_selling_price_positive"),
        CheckConstraint(
            "length(trim(category)) > 0",
            name="chk_products_category_not_empty",
        ),
    )

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    name = Column(String(255), nullable=False)
    description = Column(Text)
    selling_price = Column(Numeric(12, 2), nullable=False)
    is_available = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    deleted_at = Column(DateTime(timezone=True))
    category = Column(String(100), nullable=False)
    image_url = Column(Text)

    recipe_rows = relationship("ProductRecipe", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")
