INSERT INTO `demo-migration.raw.customers` VALUES
 (1, ' ana@example.test ', TIMESTAMP '2025-01-01 09:00:00+00'),
 (1, 'ana@example.test', TIMESTAMP '2025-01-02 09:00:00+00'),
 (2, 'LUIS@example.test', TIMESTAMP '2025-01-01 09:00:00+00');
INSERT INTO `demo-migration.raw.orders` VALUES
 (101, 1, DATE '2025-01-03', 100, 10, 'completed', TIMESTAMP '2025-01-03 10:00:00+00', STRUCT('web' AS channel)),
 (102, 2, DATE '2025-01-03', 50, NULL, 'completed', TIMESTAMP '2025-01-03 11:00:00+00', STRUCT('store' AS channel)),
 (103, 1, DATE '2025-01-03', 80, 0, 'cancelled', TIMESTAMP '2025-01-03 12:00:00+00', STRUCT('web' AS channel));
