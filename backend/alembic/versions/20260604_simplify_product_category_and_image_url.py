"""simplify product category and image url

Revision ID: 20260604_simplify_product_category_and_image_url
Revises: 20260604_add_product_image_columns
Create Date: 2026-06-04
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260604_simplify_product_category_and_image_url"
down_revision: str | None = "20260604_add_product_image_columns"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("products", sa.Column("category", sa.String(length=100)))
    op.add_column("products", sa.Column("image_url", sa.Text()))

    op.execute(
        """
        UPDATE products
        SET category = product_categories.name
        FROM product_categories
        WHERE products.category_id = product_categories.id
        """
    )
    op.alter_column("products", "category", nullable=False)
    op.create_check_constraint(
        "chk_products_category_not_empty",
        "products",
        "length(trim(category)) > 0",
    )

    op.drop_index("idx_products_category_id", table_name="products")
    op.create_index("idx_products_category", "products", ["category"])
    op.create_index(
        "idx_products_category_available",
        "products",
        ["category", "is_available"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.drop_constraint("products_category_id_fkey", "products", type_="foreignkey")
    op.drop_column("products", "category_id")

    op.drop_constraint("products_image_size_non_negative", "products", type_="check")
    op.drop_column("products", "image_updated_at")
    op.drop_column("products", "image_size_bytes")
    op.drop_column("products", "image_content_type")
    op.drop_column("products", "image")

    op.drop_table("product_categories")


def downgrade() -> None:
    op.create_table(
        "product_categories",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("description", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )

    op.execute(
        """
        INSERT INTO product_categories (name)
        SELECT DISTINCT category
        FROM products
        """
    )

    op.add_column("products", sa.Column("category_id", sa.UUID()))
    op.execute(
        """
        UPDATE products
        SET category_id = product_categories.id
        FROM product_categories
        WHERE products.category = product_categories.name
        """
    )
    op.alter_column("products", "category_id", nullable=False)
    op.create_foreign_key(
        "products_category_id_fkey",
        "products",
        "product_categories",
        ["category_id"],
        ["id"],
    )
    op.drop_index("idx_products_category_available", table_name="products")
    op.drop_index("idx_products_category", table_name="products")
    op.create_index("idx_products_category_id", "products", ["category_id"])
    op.drop_constraint("chk_products_category_not_empty", "products", type_="check")
    op.drop_column("products", "category")

    op.add_column("products", sa.Column("image", sa.LargeBinary()))
    op.add_column("products", sa.Column("image_content_type", sa.String(length=100)))
    op.add_column("products", sa.Column("image_size_bytes", sa.Integer()))
    op.add_column("products", sa.Column("image_updated_at", sa.DateTime(timezone=True)))
    op.create_check_constraint(
        "products_image_size_non_negative",
        "products",
        "image_size_bytes IS NULL OR image_size_bytes >= 0",
    )
    op.drop_column("products", "image_url")
