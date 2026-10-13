CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE TABLE IF NOT EXISTS raw.customers (
 customer_id BIGINT, email TEXT, updated_at TIMESTAMP
);
CREATE TABLE IF NOT EXISTS raw.orders (
 order_id BIGINT PRIMARY KEY, customer_id BIGINT, order_date DATE,
 amount NUMERIC(12,2), discount_pct NUMERIC(5,2), status TEXT,
 updated_at TIMESTAMP, metadata JSONB
);
CREATE TABLE IF NOT EXISTS analytics.daily_sales (
 sales_date DATE PRIMARY KEY, order_count BIGINT, net_revenue NUMERIC(18,2)
);
CREATE TABLE IF NOT EXISTS analytics.refresh_audit (
 refreshed_at TIMESTAMP, sales_date DATE
);
