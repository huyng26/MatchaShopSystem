-- Delivery trip order metadata added by the updated delivery plan.

ALTER TABLE IF EXISTS delivery_trip_orders
    ADD COLUMN IF NOT EXISTS failed_at timestamptz;

ALTER TABLE IF EXISTS delivery_trip_orders
    ADD COLUMN IF NOT EXISTS note text;
