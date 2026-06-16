-- Finance, delivery, COD reconciliation, and audit tables.

CREATE TABLE IF NOT EXISTS expenses (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    category varchar(100) NOT NULL,
    description text NOT NULL,
    amount numeric(12, 2) NOT NULL,
    expense_month date NOT NULL,
    invoice_photo_url text,
    created_by uuid NOT NULL REFERENCES users (id),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    CONSTRAINT expenses_amount_positive CHECK (amount > 0)
);

CREATE TABLE IF NOT EXISTS financial_records (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    record_type financial_record_type NOT NULL,
    source_type varchar(100) NOT NULL,
    source_id uuid NOT NULL,
    amount numeric(12, 2) NOT NULL,
    record_date date NOT NULL,
    locked boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT financial_records_amount_non_negative CHECK (amount >= 0)
);

CREATE TABLE IF NOT EXISTS delivery_trips (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_code varchar(100) UNIQUE NOT NULL,
    shipper_id uuid REFERENCES staff_profiles (id),
    status delivery_trip_status NOT NULL DEFAULT 'pending_dispatch',
    expected_cod_amount numeric(12, 2) NOT NULL DEFAULT 0,
    actual_cod_amount numeric(12, 2),
    discrepancy_amount numeric(12, 2),
    discrepancy_reason text,
    total_distance_km numeric(10, 3),
    total_duration_minutes integer,
    route_provider varchar(50),
    started_at timestamptz,
    completed_at timestamptz,
    reconciled_at timestamptz,
    created_by uuid NOT NULL REFERENCES users (id),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    CONSTRAINT delivery_trips_expected_cod_non_negative CHECK (
        expected_cod_amount >= 0
    ),
    CONSTRAINT delivery_trips_actual_cod_non_negative CHECK (
        actual_cod_amount IS NULL OR actual_cod_amount >= 0
    )
);

CREATE TABLE IF NOT EXISTS delivery_trip_orders (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_id uuid NOT NULL REFERENCES delivery_trips (id),
    order_id uuid NOT NULL REFERENCES orders (id),
    stop_order integer NOT NULL,
    status delivery_trip_order_status NOT NULL DEFAULT 'assigned',
    cod_collected numeric(12, 2) NOT NULL DEFAULT 0,
    distance_from_previous_km numeric(10, 3),
    duration_from_previous_minutes integer,
    delivered_at timestamptz,
    failed_at timestamptz,
    failed_reason text,
    note text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT delivery_trip_orders_trip_order_unique UNIQUE (trip_id, order_id),
    CONSTRAINT delivery_trip_orders_trip_stop_unique UNIQUE (trip_id, stop_order),
    CONSTRAINT delivery_trip_orders_stop_order_positive CHECK (stop_order > 0),
    CONSTRAINT delivery_trip_orders_cod_collected_non_negative CHECK (
        cod_collected >= 0
    )
);

CREATE TABLE IF NOT EXISTS delivery_location_logs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_id uuid NOT NULL REFERENCES delivery_trips (id),
    shipper_id uuid NOT NULL REFERENCES staff_profiles (id),
    latitude numeric(10, 7) NOT NULL,
    longitude numeric(10, 7) NOT NULL,
    recorded_at timestamptz NOT NULL,
    CONSTRAINT delivery_location_logs_latitude_valid CHECK (
        latitude BETWEEN -90 AND 90
    ),
    CONSTRAINT delivery_location_logs_longitude_valid CHECK (
        longitude BETWEEN -180 AND 180
    )
);

CREATE TABLE IF NOT EXISTS cod_reconciliations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_id uuid UNIQUE NOT NULL REFERENCES delivery_trips (id),
    shipper_id uuid NOT NULL REFERENCES staff_profiles (id),
    expected_amount numeric(12, 2) NOT NULL,
    actual_amount numeric(12, 2) NOT NULL,
    discrepancy_amount numeric(12, 2) NOT NULL,
    discrepancy_reason text,
    status cod_reconciliation_status NOT NULL DEFAULT 'confirmed',
    reconciled_by uuid NOT NULL REFERENCES users (id),
    reconciled_at timestamptz NOT NULL,
    CONSTRAINT cod_reconciliations_expected_amount_non_negative CHECK (
        expected_amount >= 0
    ),
    CONSTRAINT cod_reconciliations_actual_amount_non_negative CHECK (
        actual_amount >= 0
    )
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_user_id uuid REFERENCES users (id),
    action varchar(100) NOT NULL,
    entity_type varchar(100) NOT NULL,
    entity_id uuid,
    old_value jsonb,
    new_value jsonb,
    ip_address varchar(100),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS notifications (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users (id),
    type varchar(100) NOT NULL,
    severity varchar(20) NOT NULL DEFAULT 'info',
    title varchar(255) NOT NULL,
    message text NOT NULL,
    entity_type varchar(100),
    entity_id uuid,
    action_url text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    dedupe_key varchar(255),
    read_at timestamptz,
    dismissed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz,
    CONSTRAINT notifications_severity_valid CHECK (
        severity IN ('info', 'warning', 'critical')
    )
);
