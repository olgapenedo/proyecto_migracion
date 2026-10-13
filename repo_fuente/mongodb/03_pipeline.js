db = db.getSiblingDB("migration_lab");
// No es un procedimiento almacenado: función local del cliente mongosh.
// $merge no elimina resultados antiguos si una fecha deja de tener ventas.
function refreshDailySales(pDate) {
 return db.orders.aggregate([
  {$match: {status: "completed", order_date: pDate}},
  {$set: {net_amount: {$round: [{$multiply: ["$amount", {$subtract: [NumberDecimal("1"), {$divide: [{$ifNull: ["$discount_pct", NumberDecimal("0")]}, NumberDecimal("100")]}]}]}, 2]}}},
  {$group: {_id: "$order_date", order_count: {$sum: 1}, net_revenue: {$sum: "$net_amount"}}},
  {$merge: {into: "daily_sales", on: "_id", whenMatched: "replace", whenNotMatched: "insert"}}
 ]).toArray();
}
// refreshDailySales("2025-01-03");
