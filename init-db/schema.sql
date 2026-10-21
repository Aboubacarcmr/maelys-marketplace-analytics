-- Maelys Marketplace - modèle dimensionnel en étoile (type Kimball)
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS dwh;
CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS staging.orders (
    order_id TEXT NOT NULL,
    line_id INTEGER NOT NULL,
    dt DATE NOT NULL,
    seller_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),
    total NUMERIC(14,2) NOT NULL CHECK (total >= 0),
    status TEXT NOT NULL CHECK (status IN ('paid','cancelled')),
    PRIMARY KEY (order_id, line_id)
);
CREATE INDEX IF NOT EXISTS idx_staging_dt ON staging.orders(dt);

CREATE TABLE IF NOT EXISTS dwh.dim_seller (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT NOT NULL,
    joined_date DATE NOT NULL
);
CREATE TABLE IF NOT EXISTS dwh.dim_product (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    seller_id INTEGER NOT NULL,
    price NUMERIC(12,2) NOT NULL
);
CREATE TABLE IF NOT EXISTS dwh.dim_date (
    dt DATE PRIMARY KEY,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS dwh.fact_orders (
    order_id TEXT NOT NULL,
    line_id INTEGER NOT NULL,
    dt DATE NOT NULL REFERENCES dwh.dim_date(dt),
    seller_id INTEGER NOT NULL REFERENCES dwh.dim_seller(id),
    product_id INTEGER NOT NULL REFERENCES dwh.dim_product(id),
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12,2) NOT NULL,
    total NUMERIC(14,2) NOT NULL,
    commission NUMERIC(14,2) NOT NULL,
    status TEXT NOT NULL,
    PRIMARY KEY (order_id, line_id)
);
CREATE INDEX IF NOT EXISTS idx_fact_dt ON dwh.fact_orders(dt);
CREATE INDEX IF NOT EXISTS idx_fact_seller_dt ON dwh.fact_orders(seller_id, dt);
CREATE INDEX IF NOT EXISTS idx_fact_product_dt ON dwh.fact_orders(product_id, dt);

CREATE TABLE IF NOT EXISTS analytics.daily_summary (
    dt DATE PRIMARY KEY,
    total_orders INTEGER NOT NULL,
    total_revenue NUMERIC(18,2) NOT NULL,
    total_commission NUMERIC(18,2) NOT NULL,
    average_basket NUMERIC(18,2) NOT NULL
);
CREATE TABLE IF NOT EXISTS analytics.seller_daily (
    dt DATE NOT NULL,
    seller_id INTEGER NOT NULL REFERENCES dwh.dim_seller(id),
    revenue NUMERIC(18,2) NOT NULL,
    orders_count INTEGER NOT NULL,
    PRIMARY KEY(dt, seller_id)
);
CREATE TABLE IF NOT EXISTS analytics.category_daily (
    dt DATE NOT NULL,
    category TEXT NOT NULL,
    revenue NUMERIC(18,2) NOT NULL,
    PRIMARY KEY(dt, category)
);
CREATE TABLE IF NOT EXISTS analytics.anomaly_alerts (
    dt DATE PRIMARY KEY,
    revenue NUMERIC(18,2) NOT NULL,
    mean_7d NUMERIC(18,2) NOT NULL,
    ratio NUMERIC(8,4) NOT NULL,
    severity TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
