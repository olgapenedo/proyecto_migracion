CREATE OR REPLACE FUNCTION `demo-migration.analytics.net_amount`(amount NUMERIC, discount_pct NUMERIC)
RETURNS NUMERIC AS (ROUND(amount * (1 - COALESCE(discount_pct, 0) / 100), 2));
CREATE OR REPLACE VIEW `demo-migration.analytics.v_customers` AS
SELECT customer_id, LOWER(TRIM(email)) AS email, updated_at
FROM `demo-migration.raw.customers`
QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY updated_at DESC) = 1;
CREATE OR REPLACE VIEW `demo-migration.analytics.v_orders` AS
SELECT o.order_id, o.customer_id, o.order_date,
 `demo-migration.analytics.net_amount`(o.amount, o.discount_pct) AS net_amount,
 o.metadata.channel AS channel, c.email, o.updated_at
FROM `demo-migration.raw.orders` o
JOIN `demo-migration.analytics.v_customers` c ON o.customer_id = c.customer_id
WHERE o.status = 'completed';
