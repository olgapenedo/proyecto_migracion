INSERT INTO raw.customers VALUES
 (1, ' ana@example.test ', '2025-01-01T09:00:00'),
 (1, 'ana@example.test', '2025-01-02T09:00:00'),
 (2, 'LUIS@example.test', '2025-01-01T09:00:00');
INSERT INTO raw.orders VALUES
 (101, 1, '2025-01-03', 100, 10, 'completed', '2025-01-03T10:00:00', '{"channel":"web"}'),
 (102, 2, '2025-01-03', 50, NULL, 'completed', '2025-01-03T11:00:00', '{"channel":"store"}'),
 (103, 1, '2025-01-03', 80, 0, 'cancelled', '2025-01-03T12:00:00', '{"channel":"web"}');
GO
