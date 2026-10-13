-- Fixture opcional: ejecutar UNA VEZ, después de la primera llamada a
-- ANALYTICS.LOAD_FCT_ORDERS(). Simula nuevas versiones en una fuente append-only.
INSERT INTO RAW.ORDERS
SELECT 101, 1, '2025-01-03'::DATE, 100, 20, 'completed',
 '2025-01-04 09:00:00'::TIMESTAMP_NTZ, PARSE_JSON('{"channel":"web"}')
UNION ALL
SELECT 102, 2, '2025-01-03'::DATE, 50, NULL, 'cancelled',
 '2025-01-04 09:05:00'::TIMESTAMP_NTZ, PARSE_JSON('{"channel":"store"}')
UNION ALL
SELECT 104, 2, '2025-01-04'::DATE, 200, 5, 'completed',
 '2025-01-04 10:00:00'::TIMESTAMP_NTZ, PARSE_JSON('{"channel":"app"}')
UNION ALL
-- Llegada tardía: fecha de negocio antigua, updated_at dentro de la ventana.
SELECT 105, 1, '2025-01-02'::DATE, 30, 0, 'completed',
 '2025-01-03 08:00:00'::TIMESTAMP_NTZ, PARSE_JSON('{"channel":"web"}');

-- CALL ANALYTICS.LOAD_FCT_ORDERS();
-- Esperado: 5 filas únicas; 101=80, 102=50/cancelled, 103=80/cancelled,
-- 104=190, 105=30. Repetir SOLO la llamada mantiene esas 5 filas.
-- Este fixture pertenece al caso FCT_ORDERS: las vistas originales no
-- deduplican pedidos y no deben usarse para validar este segundo lote.
