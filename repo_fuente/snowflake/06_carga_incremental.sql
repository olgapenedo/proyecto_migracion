-- Ejecutar después de 01-03. Modelo de hechos a nivel de pedido.
-- Candidato dbt: materialized=incremental, unique_key=ORDER_ID, merge.
-- Conservar TODOS los estados: filtrar completed aquí dejaría pedidos cancelados
-- con su estado antiguo en el destino. El filtro pertenece al modelo consumidor.
CREATE TABLE IF NOT EXISTS ANALYTICS.FCT_ORDERS (
 ORDER_ID NUMBER(18,0), CUSTOMER_ID NUMBER(18,0), ORDER_DATE DATE,
 NET_AMOUNT NUMBER(12,2), STATUS VARCHAR, CHANNEL VARCHAR,
 UPDATED_AT TIMESTAMP_NTZ
);

CREATE OR REPLACE PROCEDURE ANALYTICS.LOAD_FCT_ORDERS()
RETURNS VARCHAR LANGUAGE SQL AS
$$
BEGIN
 MERGE INTO ANALYTICS.FCT_ORDERS t
 USING (
  SELECT ORDER_ID, CUSTOMER_ID, ORDER_DATE,
   ANALYTICS.NET_AMOUNT(AMOUNT, DISCOUNT_PCT) AS NET_AMOUNT,
   STATUS, METADATA:channel::VARCHAR AS CHANNEL, UPDATED_AT
  FROM RAW.ORDERS
  WHERE UPDATED_AT >= (
   SELECT DATEADD(day, -2, COALESCE(MAX(UPDATED_AT),
                                  '1900-01-01'::TIMESTAMP_NTZ))
   FROM ANALYTICS.FCT_ORDERS
  )
  QUALIFY ROW_NUMBER() OVER (
   PARTITION BY ORDER_ID ORDER BY UPDATED_AT DESC
  ) = 1
 ) s ON t.ORDER_ID = s.ORDER_ID
 WHEN MATCHED AND s.UPDATED_AT >= t.UPDATED_AT THEN UPDATE SET
  CUSTOMER_ID = s.CUSTOMER_ID, ORDER_DATE = s.ORDER_DATE,
  NET_AMOUNT = s.NET_AMOUNT, STATUS = s.STATUS,
  CHANNEL = s.CHANNEL, UPDATED_AT = s.UPDATED_AT
 WHEN NOT MATCHED THEN INSERT
  (ORDER_ID, CUSTOMER_ID, ORDER_DATE, NET_AMOUNT, STATUS, CHANNEL, UPDATED_AT)
 VALUES
  (s.ORDER_ID, s.CUSTOMER_ID, s.ORDER_DATE, s.NET_AMOUNT, s.STATUS, s.CHANNEL, s.UPDATED_AT);
 RETURN 'ok';
END;
$$;

-- Primera ejecución: carga 101, 102 y 103; siguientes: solo ventana de cambios.
-- CALL ANALYTICS.LOAD_FCT_ORDERS();
-- Contrato: UPDATED_AT no nulo, sin versiones distintas de un pedido con la
-- misma marca de tiempo. Retrasos máximos de dos días respecto al watermark.
-- Retrasos mayores o borrados físicos requieren reconciliación/full refresh.
-- En dbt aplicar este WHERE solo dentro de is_incremental(); full refresh
-- debe leer todo RAW.ORDERS. Evitar una materialización append que duplique IDs.
