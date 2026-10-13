CREATE OR ALTER FUNCTION analytics.net_amount(@amount DECIMAL(12,2), @discount_pct DECIMAL(5,2))
RETURNS DECIMAL(12,2) AS
BEGIN
 RETURN ROUND(@amount * (1 - COALESCE(@discount_pct, 0) / 100.0), 2);
END;
GO
CREATE OR ALTER VIEW analytics.v_customers AS
SELECT customer_id, LOWER(LTRIM(RTRIM(email))) AS email, updated_at
FROM (
 SELECT *, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY updated_at DESC) AS rn
 FROM raw.customers
) ranked WHERE rn = 1;
GO
CREATE OR ALTER VIEW analytics.v_orders AS
SELECT o.order_id, o.customer_id, o.order_date,
 analytics.net_amount(o.amount, o.discount_pct) AS net_amount,
 JSON_VALUE(o.metadata, '$.channel') AS channel, c.email, o.updated_at
FROM raw.orders o JOIN analytics.v_customers c ON o.customer_id = c.customer_id
WHERE o.status = 'completed';
GO
