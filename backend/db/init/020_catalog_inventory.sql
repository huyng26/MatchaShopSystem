-- Product catalog, recipes, and inventory tables.

CREATE TABLE IF NOT EXISTS products (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name varchar(255) NOT NULL,
    description text,
    selling_price numeric(12, 2) NOT NULL,
    is_available boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    category varchar(100) NOT NULL,
    image_url text,
    CONSTRAINT chk_products_category_not_empty CHECK (
        length(trim(category)) > 0
    ),
    CONSTRAINT products_selling_price_positive CHECK (selling_price > 0)
);

CREATE TABLE IF NOT EXISTS ingredients (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name varchar(255) UNIQUE NOT NULL,
    unit varchar(50) NOT NULL,
    current_stock numeric(12, 3) NOT NULL DEFAULT 0,
    cost_per_unit numeric(12, 2) NOT NULL,
    minimum_threshold numeric(12, 3) NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    CONSTRAINT ingredients_current_stock_non_negative CHECK (current_stock >= 0),
    CONSTRAINT ingredients_cost_per_unit_non_negative CHECK (cost_per_unit >= 0),
    CONSTRAINT ingredients_minimum_threshold_non_negative CHECK (
        minimum_threshold >= 0
    )
);

CREATE TABLE IF NOT EXISTS product_recipes (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id uuid NOT NULL REFERENCES products (id),
    ingredient_id uuid NOT NULL REFERENCES ingredients (id),
    quantity_per_serving numeric(12, 3) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT product_recipes_product_ingredient_unique UNIQUE (
        product_id,
        ingredient_id
    ),
    CONSTRAINT product_recipes_quantity_positive CHECK (quantity_per_serving > 0)
);

CREATE TABLE IF NOT EXISTS inventory_purchases (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    ingredient_id uuid NOT NULL REFERENCES ingredients (id),
    quantity numeric(12, 3) NOT NULL,
    cost_per_unit numeric(12, 2) NOT NULL,
    total_cost numeric(12, 2) NOT NULL,
    supplier_name varchar(255),
    notes text,
    purchased_at timestamptz NOT NULL,
    created_by uuid NOT NULL REFERENCES users (id),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT inventory_purchases_quantity_positive CHECK (quantity > 0),
    CONSTRAINT inventory_purchases_cost_per_unit_non_negative CHECK (
        cost_per_unit >= 0
    ),
    CONSTRAINT inventory_purchases_total_cost_non_negative CHECK (total_cost >= 0)
);

CREATE TABLE IF NOT EXISTS inventory_movements (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    ingredient_id uuid NOT NULL REFERENCES ingredients (id),
    movement_type inventory_movement_type NOT NULL,
    quantity_change numeric(12, 3) NOT NULL,
    stock_before numeric(12, 3) NOT NULL,
    stock_after numeric(12, 3) NOT NULL,
    unit_cost numeric(12, 2),
    reference_type varchar(100),
    reference_id uuid,
    created_by uuid REFERENCES users (id),
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT inventory_movements_quantity_change_not_zero CHECK (
        quantity_change <> 0
    ),
    CONSTRAINT inventory_movements_stock_before_non_negative CHECK (
        stock_before >= 0
    ),
    CONSTRAINT inventory_movements_stock_after_non_negative CHECK (
        stock_after >= 0
    ),
    CONSTRAINT inventory_movements_unit_cost_non_negative CHECK (
        unit_cost IS NULL OR unit_cost >= 0
    )
);
