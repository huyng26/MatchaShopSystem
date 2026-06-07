"""add delivery maps routing and tracking metadata

Revision ID: 20260607_delivery_maps_routing_tracking
Revises: 20260604_simplify_product_category_and_image_url
Create Date: 2026-06-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260607_delivery_maps_routing_tracking"
down_revision: str | None = "20260604_simplify_product_category_and_image_url"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("delivery_formatted_address", sa.Text()))
    op.add_column("orders", sa.Column("delivery_place_id", sa.String(length=255)))
    op.add_column("orders", sa.Column("geocoded_at", sa.DateTime(timezone=True)))
    op.add_column("orders", sa.Column("geocoding_status", sa.String(length=50)))
    op.add_column("orders", sa.Column("map_provider", sa.String(length=50)))

    op.add_column("delivery_trips", sa.Column("total_distance_km", sa.Numeric(10, 3)))
    op.add_column("delivery_trips", sa.Column("total_duration_minutes", sa.Integer()))
    op.add_column("delivery_trips", sa.Column("route_provider", sa.String(length=50)))

    op.add_column(
        "delivery_trip_orders",
        sa.Column("distance_from_previous_km", sa.Numeric(10, 3)),
    )
    op.add_column(
        "delivery_trip_orders",
        sa.Column("duration_from_previous_minutes", sa.Integer()),
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_delivery_location_logs_trip_recorded_at
        ON delivery_location_logs (trip_id, recorded_at DESC)
        """
    )


def downgrade() -> None:
    op.drop_index(
        "idx_delivery_location_logs_trip_recorded_at",
        table_name="delivery_location_logs",
    )
    op.drop_column("delivery_trip_orders", "duration_from_previous_minutes")
    op.drop_column("delivery_trip_orders", "distance_from_previous_km")
    op.drop_column("delivery_trips", "route_provider")
    op.drop_column("delivery_trips", "total_duration_minutes")
    op.drop_column("delivery_trips", "total_distance_km")
    op.drop_column("orders", "map_provider")
    op.drop_column("orders", "geocoding_status")
    op.drop_column("orders", "geocoded_at")
    op.drop_column("orders", "delivery_place_id")
    op.drop_column("orders", "delivery_formatted_address")
