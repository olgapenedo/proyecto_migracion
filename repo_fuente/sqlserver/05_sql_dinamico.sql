-- Caso de revisión manual: dependencia determinada en tiempo de ejecución.
CREATE OR ALTER PROCEDURE analytics.count_source_rows
 @schema_name SYSNAME, @table_name SYSNAME AS
BEGIN
 DECLARE @sql NVARCHAR(MAX);
 SET @sql = N'SELECT COUNT_BIG(*) AS row_count FROM '
  + QUOTENAME(@schema_name) + N'.' + QUOTENAME(@table_name);
 EXEC sys.sp_executesql @sql;
END;
GO
