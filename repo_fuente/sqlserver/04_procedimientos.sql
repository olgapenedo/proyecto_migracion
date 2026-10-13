CREATE OR ALTER PROCEDURE analytics.refresh_daily_sales @p_date DATE AS
BEGIN
 SET NOCOUNT ON;
 SET XACT_ABORT ON;
 BEGIN TRY
  BEGIN TRANSACTION;
  DELETE FROM analytics.daily_sales WHERE sales_date = @p_date;
  INSERT INTO analytics.daily_sales
  SELECT order_date, COUNT_BIG(*), SUM(net_amount)
  FROM analytics.v_orders WHERE order_date = @p_date GROUP BY order_date;
  COMMIT TRANSACTION;
 END TRY
 BEGIN CATCH
  IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
  THROW;
 END CATCH;
END;
GO
-- EXEC analytics.refresh_daily_sales @p_date = '2025-01-03';
