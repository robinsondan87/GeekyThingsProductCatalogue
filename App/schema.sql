CREATE TABLE IF NOT EXISTS products (
    id BIGSERIAL PRIMARY KEY,
    category TEXT NOT NULL,
    product_folder TEXT NOT NULL,
    sku TEXT NOT NULL DEFAULT '',
    ukca TEXT NOT NULL DEFAULT 'No',
    listings TEXT NOT NULL DEFAULT '',
    tags TEXT NOT NULL DEFAULT '',
    facebook_url TEXT NOT NULL DEFAULT '',
    tiktok_url TEXT NOT NULL DEFAULT '',
    ebay_url TEXT NOT NULL DEFAULT '',
    etsy_url TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'Live',
    completed TEXT NOT NULL DEFAULT '',
    colors TEXT NOT NULL DEFAULT '',
    sizes TEXT NOT NULL DEFAULT '',
    cost_to_make TEXT NOT NULL DEFAULT '',
    sale_price TEXT NOT NULL DEFAULT '',
    postage_price TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS products_category_folder_key
    ON products (category, product_folder);
CREATE INDEX IF NOT EXISTS products_sku_idx
    ON products (sku);

ALTER TABLE products
    ADD COLUMN IF NOT EXISTS completed TEXT NOT NULL DEFAULT '';

CREATE TABLE IF NOT EXISTS product_pricing (
    product_id BIGINT PRIMARY KEY REFERENCES products(id) ON DELETE CASCADE,
    pricing JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS ukca_documents (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    file_key TEXT NOT NULL,
    content TEXT NOT NULL DEFAULT '',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (product_id, file_key)
);

CREATE TABLE IF NOT EXISTS stock (
    id BIGSERIAL PRIMARY KEY,
    category TEXT NOT NULL,
    product_folder TEXT NOT NULL,
    sku TEXT NOT NULL DEFAULT '',
    color TEXT NOT NULL DEFAULT '',
    size TEXT NOT NULL DEFAULT '',
    quantity INTEGER NOT NULL DEFAULT 0
);

CREATE UNIQUE INDEX IF NOT EXISTS stock_unique_idx
    ON stock (category, product_folder, color, size);
CREATE INDEX IF NOT EXISTS stock_sku_idx
    ON stock (sku);

CREATE TABLE IF NOT EXISTS events (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    event_date DATE NOT NULL,
    location TEXT NOT NULL DEFAULT '',
    contact_name TEXT NOT NULL DEFAULT '',
    contact_email TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS events_date_idx
    ON events (event_date);

CREATE TABLE IF NOT EXISTS sales (
    id BIGSERIAL PRIMARY KEY,
    event_id BIGINT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    product_id BIGINT REFERENCES products(id) ON DELETE SET NULL,
    category TEXT NOT NULL DEFAULT '',
    product_folder TEXT NOT NULL DEFAULT '',
    sku TEXT NOT NULL DEFAULT '',
    color TEXT NOT NULL DEFAULT '',
    size TEXT NOT NULL DEFAULT '',
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price NUMERIC(10, 2) NOT NULL DEFAULT 0,
    override_price TEXT NOT NULL DEFAULT '',
    payment_method TEXT NOT NULL DEFAULT '',
    sold_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS sales_event_idx
    ON sales (event_id);

CREATE TABLE IF NOT EXISTS event_targets (
    id BIGSERIAL PRIMARY KEY,
    event_id BIGINT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    product_id BIGINT REFERENCES products(id) ON DELETE SET NULL,
    category TEXT NOT NULL DEFAULT '',
    product_folder TEXT NOT NULL DEFAULT '',
    sku TEXT NOT NULL DEFAULT '',
    color TEXT NOT NULL DEFAULT '',
    size TEXT NOT NULL DEFAULT '',
    target_qty INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS event_targets_unique_idx
    ON event_targets (event_id, category, product_folder, color, size);

CREATE TABLE IF NOT EXISTS production_queue (
    id BIGSERIAL PRIMARY KEY,
    category TEXT NOT NULL DEFAULT '',
    product_folder TEXT NOT NULL DEFAULT '',
    sku TEXT NOT NULL DEFAULT '',
    color TEXT NOT NULL DEFAULT '',
    size TEXT NOT NULL DEFAULT '',
    quantity INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'Queued',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS production_queue_unique_idx
    ON production_queue (category, product_folder, color, size, status);

CREATE INDEX IF NOT EXISTS production_queue_status_idx
    ON production_queue (status);

CREATE TABLE IF NOT EXISTS event_media (
    id BIGSERIAL PRIMARY KEY,
    event_id BIGINT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL DEFAULT '',
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS event_media_event_idx
    ON event_media (event_id);

CREATE TABLE IF NOT EXISTS supplies (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT '',
    unit TEXT NOT NULL DEFAULT '',
    quantity INTEGER NOT NULL DEFAULT 0,
    reorder_point INTEGER NOT NULL DEFAULT 0,
    vendor TEXT NOT NULL DEFAULT '',
    lead_time_days INTEGER NOT NULL DEFAULT 0,
    location TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS supplies_name_idx
    ON supplies (name);

CREATE TABLE IF NOT EXISTS expenses (
    id BIGSERIAL PRIMARY KEY,
    expense_date DATE NOT NULL,
    vendor TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT '',
    amount NUMERIC(10, 2) NOT NULL DEFAULT 0,
    payment_method TEXT NOT NULL DEFAULT '',
    reference TEXT NOT NULL DEFAULT '',
    receipt_path TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS expenses_date_idx
    ON expenses (expense_date);
