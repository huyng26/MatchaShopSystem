-- Order and payment tables.

CREATE TABLE IF NOT EXISTS orders (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    order_code varchar(100) UNIQUE NOT NULL,
    customer_id uuid REFERENCES customers (id),
    order_type order_type NOT NULL,
    status order_status NOT NULL DEFAULT 'pending',
    payment_status order_payment_status NOT NULL DEFAULT 'unpaid',
    subtotal numeric(12, 2) NOT NULL DEFAULT 0,
    discount_amount numeric(12, 2) NOT NULL DEFAULT 0,
    total_amount numeric(12, 2) NOT NULL DEFAULT 0,
    customer_name varchar(255),
    customer_phone varchar(50),
    delivery_address text,
    delivery_latitude numeric(10, 7),
    delivery_longitude numeric(10, 7),
    note text,
    created_by uuid NOT NULL REFERENCES users (id),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    cancelled_at timestamptz,
    deleted_at timestamptz,
    CONSTRAINT orders_subtotal_non_negative CHECK (subtotal >= 0),
    CONSTRAINT orders_discount_non_negative CHECK (discount_amount >= 0),
    CONSTRAINT orders_total_non_negative CHECK (total_amount >= 0),
    CONSTRAINT orders_delivery_latitude_valid CHECK (
        delivery_latitude IS NULL
        OR delivery_latitude BETWEEN -90 AND 90
    ),
    CONSTRAINT orders_delivery_longitude_valid CHECK (
        delivery_longitude IS NULL
        OR delivery_longitude BETWEEN -180 AND 180
    )
);

CREATE TABLE IF NOT EXISTS order_items (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id uuid NOT NULL REFERENCES orders (id),
    product_id uuid NOT NULL REFERENCES products (id),
    quantity integer NOT NULL,
    unit_price numeric(12, 2) NOT NULL,
    line_total numeric(12, 2) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT order_items_quantity_positive CHECK (quantity > 0),
    CONSTRAINT order_items_unit_price_non_negative CHECK (unit_price >= 0),
    CONSTRAINT order_items_line_total_non_negative CHECK (line_total >= 0)
);

CREATE TABLE IF NOT EXISTS payments (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id uuid NOT NULL REFERENCES orders (id),
    method payment_method NOT NULL,
    status payment_event_status NOT NULL DEFAULT 'pending',
    amount numeric(12, 2) NOT NULL,
    amount_received numeric(12, 2),
    change_amount numeric(12, 2),
    gateway_transaction_id varchar(255),
    bank_reference_number varchar(255),
    paid_at timestamptz,
    created_by uuid NOT NULL REFERENCES users (id),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT payments_amount_positive CHECK (amount > 0),
    CONSTRAINT payments_amount_received_non_negative CHECK (
        amount_received IS NULL OR amount_received >= 0
    ),
    CONSTRAINT payments_change_amount_non_negative CHECK (
        change_amount IS NULL OR change_amount >= 0
    )
);
