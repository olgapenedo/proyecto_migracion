CREATE OR REPLACE FUNCTION analytics.net_amount(amount NUMERIC, discount_pct NUMERIC)
RETURNS NUMERIC LANGUAGE SQL IMMUTABLE AS
$$ SELECT ROUND(amount * (1 - COALESCE(discount_pct, 0) / 100.0), 2) $$;
CREATE OR REPLACE VIEW analytics.v_customers AS
SELECT customer_id, LOWER(TRIM(email)) AS email, updated_at
FROM (
 SELECT *, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY updated_at DESC) AS rn
 FROM raw.customers
) ranked WHERE rn = 1;
CREATE OR REPLACE VIEW analytics.v_orders AS
SELECT o.order_id, o.customer_id, o.order_date,
 analytics.net_amount(o.amount, o.discount_pct) AS net_amount,
 o.metadata ->> 'channel' AS channel, c.email, o.updated_at
FROM raw.orders o JOIN analytics.v_customers c ON o.customer_id = c.customer_id
WHERE o.status = 'completed';
