db = db.getSiblingDB("migration_lab");
db.customers.insertMany([
 {customer_id: 1, email: " ana@example.test ", updated_at: ISODate("2025-01-01T09:00:00Z")},
 {customer_id: 1, email: "ana@example.test", updated_at: ISODate("2025-01-02T09:00:00Z")},
 {customer_id: 2, email: "LUIS@example.test", updated_at: ISODate("2025-01-01T09:00:00Z")}
]);
db.orders.insertMany([
 {order_id: 101, customer_id: 1, order_date: "2025-01-03", amount: NumberDecimal("100"), discount_pct: NumberDecimal("10"), status: "completed", metadata: {channel: "web"}},
 {order_id: 102, customer_id: 2, order_date: "2025-01-03", amount: NumberDecimal("50"), discount_pct: null, status: "completed", metadata: {channel: "store"}},
 {order_id: 103, customer_id: 1, order_date: "2025-01-03", amount: NumberDecimal("80"), discount_pct: NumberDecimal("0"), status: "cancelled", metadata: {channel: "web"}}
]);
