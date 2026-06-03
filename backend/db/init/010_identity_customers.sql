-- Account, staff, task, and customer tables.

CREATE TABLE IF NOT EXISTS users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email varchar(255) UNIQUE NOT NULL,
    hashed_password varchar(255) NOT NULL,
    role user_role NOT NULL,
    status user_status NOT NULL DEFAULT 'active',
    last_login_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz
);

CREATE TABLE IF NOT EXISTS staff_profiles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid UNIQUE REFERENCES users (id) ON DELETE SET NULL,
    full_name varchar(255) NOT NULL,
    phone varchar(50) UNIQUE NOT NULL,
    email varchar(255) UNIQUE NOT NULL,
    role user_role NOT NULL,
    salary numeric(12, 2),
    date_joined date NOT NULL,
    status staff_status NOT NULL DEFAULT 'active',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    CONSTRAINT staff_profiles_salary_non_negative CHECK (
        salary IS NULL OR salary >= 0
    )
);

CREATE TABLE IF NOT EXISTS staff_tasks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    staff_id uuid NOT NULL REFERENCES staff_profiles (id),
    title varchar(255) NOT NULL,
    description text,
    due_date date NOT NULL,
    priority task_priority NOT NULL,
    status task_status NOT NULL DEFAULT 'pending',
    created_by uuid NOT NULL REFERENCES users (id),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz
);

CREATE TABLE IF NOT EXISTS customers (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name varchar(255) NOT NULL,
    phone varchar(50),
    address text,
    note text,
    loyalty_points integer NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz,
    CONSTRAINT customers_loyalty_points_non_negative CHECK (loyalty_points >= 0)
);
