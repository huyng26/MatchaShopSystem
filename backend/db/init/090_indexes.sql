-- Indexes for common filtering and joins.

CREATE INDEX IF NOT EXISTS idx_staff_profiles_email ON staff_profiles (email);
CREATE INDEX IF NOT EXISTS idx_staff_profiles_phone ON staff_profiles (phone);
CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers (phone);
CREATE INDEX IF NOT EXISTS idx_products_name ON products (name);
CREATE INDEX IF NOT EXISTS idx_products_category ON products (category);
CREATE INDEX IF NOT EXISTS idx_products_category_available
    ON products (category, is_available)
    WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders (customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders (status);
CREATE INDEX IF NOT EXISTS idx_orders_payment_status ON orders (payment_status);
CREATE INDEX IF NOT EXISTS idx_orders_order_type ON orders (order_type);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders (created_at);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items (order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items (product_id);
CREATE INDEX IF NOT EXISTS idx_payments_order_id ON payments (order_id);
CREATE INDEX IF NOT EXISTS idx_payments_method ON payments (method);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments (status);
CREATE INDEX IF NOT EXISTS idx_inventory_movements_ingredient_id
    ON inventory_movements (ingredient_id);
CREATE INDEX IF NOT EXISTS idx_inventory_movements_created_at
    ON inventory_movements (created_at);
CREATE INDEX IF NOT EXISTS idx_inventory_purchases_ingredient_id
    ON inventory_purchases (ingredient_id);
CREATE INDEX IF NOT EXISTS idx_expenses_expense_month ON expenses (expense_month);
CREATE INDEX IF NOT EXISTS idx_financial_records_record_type
    ON financial_records (record_type);
CREATE INDEX IF NOT EXISTS idx_financial_records_record_date
    ON financial_records (record_date);
CREATE INDEX IF NOT EXISTS idx_delivery_trips_shipper_id
    ON delivery_trips (shipper_id);
CREATE INDEX IF NOT EXISTS idx_delivery_trips_status ON delivery_trips (status);
CREATE INDEX IF NOT EXISTS idx_delivery_trip_orders_trip_id
    ON delivery_trip_orders (trip_id);
CREATE INDEX IF NOT EXISTS idx_delivery_trip_orders_order_id
    ON delivery_trip_orders (order_id);
CREATE INDEX IF NOT EXISTS idx_delivery_location_logs_trip_id
    ON delivery_location_logs (trip_id);
CREATE INDEX IF NOT EXISTS idx_delivery_location_logs_recorded_at
    ON delivery_location_logs (recorded_at);
