// mongosh: ejecutar en una base aislada. Es JavaScript, no SQL.
db = db.getSiblingDB("migration_lab");
db.createCollection("customers");
db.createCollection("orders");
db.createCollection("daily_sales");
