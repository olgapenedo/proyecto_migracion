-- Ejecutar con SSMS o sqlcmd: GO es un separador del cliente.
IF SCHEMA_ID('raw') IS NULL EXEC('CREATE SCHEMA raw');
GO
IF SCHEMA_ID('analytics') IS NULL EXEC('CREATE SCHEMA analytics');
GO
CREATE TABLE raw.customers (
 customer_id BIGINT, email NVARCHAR(255), updated_at DATETIME2
);
CREATE TABLE raw.orders (
 order_id BIGINT PRIMARY KEY, customer_id BIGINT, order_date DATE,
 amount DECIMAL(12,2), discount_pct DECIMAL(5,2), status NVARCHAR(30),
 updated_at DATETIME2, metadata NVARCHAR(MAX)
);
CREATE TABLE analytics.daily_sales (
 sales_date DATE PRIMARY KEY, order_count BIGINT, net_revenue DECIMAL(18,2)
);
GO
