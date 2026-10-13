-- Sustituir demo-migration por un proyecto propio. Elegir región compatible.
CREATE SCHEMA IF NOT EXISTS `demo-migration.raw` OPTIONS(location='EU');
CREATE SCHEMA IF NOT EXISTS `demo-migration.analytics` OPTIONS(location='EU');
CREATE TABLE IF NOT EXISTS `demo-migration.raw.customers` (
 customer_id INT64, email STRING, updated_at TIMESTAMP
);
CREATE TABLE IF NOT EXISTS `demo-migration.raw.orders` (
 order_id INT64, customer_id INT64, order_date DATE, amount NUMERIC,
 discount_pct NUMERIC, status STRING, updated_at TIMESTAMP,
 metadata STRUCT<channel STRING>
) PARTITION BY order_date;
CREATE TABLE IF NOT EXISTS `demo-migration.analytics.daily_sales` (
 sales_date DATE, order_count INT64, net_revenue NUMERIC
) PARTITION BY sales_date;
