CREATE OR REPLACE PROCEDURE `demo-migration.analytics.refresh_daily_sales`(p_date DATE)
BEGIN
 BEGIN TRANSACTION;
 DELETE FROM `demo-migration.analytics.daily_sales` WHERE sales_date = p_date;
 INSERT INTO `demo-migration.analytics.daily_sales`
 SELECT order_date, COUNT(*), SUM(net_amount)
 FROM `demo-migration.analytics.v_orders` WHERE order_date = p_date GROUP BY order_date;
 COMMIT TRANSACTION;
EXCEPTION WHEN ERROR THEN
 ROLLBACK TRANSACTION;
 RAISE;
END;
-- CALL `demo-migration.analytics.refresh_daily_sales`(DATE '2025-01-03');
