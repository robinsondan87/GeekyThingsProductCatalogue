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

CREATE TABLE IF NOT EXISTS product_pricing (
    product_id BIGINT PRIMARY KEY REFERENCES products(id) ON DELETE CASCADE,
    pricing JSONB NOT NULL DEFAULT '{}'::jsonb
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
