"""add product image columns

Revision ID: 20260604_add_product_image_columns
Revises:
Create Date: 2026-06-04
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260604_add_product_image_columns"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("products", sa.Column("image", sa.LargeBinary(), nullable=True))
    op.add_column(
        "products",
        sa.Column("image_content_type", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "products", sa.Column("image_size_bytes", sa.Integer(), nullable=True)
    )
    op.add_column(
        "products",
        sa.Column("image_updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_check_constraint(
        "products_image_size_non_negative",
        "products",
        "image_size_bytes IS NULL OR image_size_bytes >= 0",
    )


def downgrade() -> None:
    op.drop_constraint("products_image_size_non_negative", "products", type_="check")
    op.drop_column("products", "image_updated_at")
    op.drop_column("products", "image_size_bytes")
    op.drop_column("products", "image_content_type")
    op.drop_column("products", "image")
