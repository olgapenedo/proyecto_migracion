-- PostgreSQL 11+. La llamada completa es atómica en su transacción.
CREATE OR REPLACE PROCEDURE analytics.refresh_daily_sales(p_date DATE)
LANGUAGE plpgsql AS $$
BEGIN
 INSERT INTO analytics.daily_sales
 SELECT order_date, COUNT(*), SUM(net_amount)
 FROM analytics.v_orders WHERE order_date = p_date GROUP BY order_date
 ON CONFLICT (sales_date) DO UPDATE
 SET order_count = EXCLUDED.order_count, net_revenue = EXCLUDED.net_revenue;
 DELETE FROM analytics.daily_sales
 WHERE sales_date = p_date
 AND NOT EXISTS (SELECT 1 FROM analytics.v_orders WHERE order_date = p_date);
 -- Efecto lateral: no convertir automáticamente en un modelo SELECT.
 INSERT INTO analytics.refresh_audit VALUES (CURRENT_TIMESTAMP, p_date);
END;
$$;
-- CALL analytics.refresh_daily_sales(DATE '2025-01-03');
