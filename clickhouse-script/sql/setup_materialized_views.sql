
CREATE MATERIALIZED VIEW kafka_tables.mv_products
TO demo_tables.products
AS
SELECT
    JSONExtractUInt(payload, 'id') AS id,
    JSONExtractString(payload, 'name') AS name,
    JSONExtractString(payload, 'description') AS description,
    toDecimal128(JSONExtract(payload, 'price', 'Float64'), 2) AS price,
    toDecimal128(JSONExtract(payload, 'cost_price', 'Float64'), 2) AS cost_price,
    parseDateTimeBestEffort(JSONExtractString(payload, 'created_at')) AS created_at,
    parseDateTimeBestEffort(JSONExtractString(payload, 'updated_at')) AS updated_at
FROM kafka_tables.kafka_products;

CREATE MATERIALIZED VIEW kafka_tables.mv_orders
TO demo_tables.orders
AS
SELECT
    JSONExtractUInt(payload, 'id') AS id,
    JSONExtractString(payload, 'customer_name') AS customer_name,
    JSONExtractString(payload, 'status') AS status,
    toDecimal128(JSONExtract(payload, 'total_amount', 'Float64'), 2) AS total_amount,
    parseDateTimeBestEffort(JSONExtractString(payload, 'created_at')) AS created_at,
    parseDateTimeBestEffort(JSONExtractString(payload, 'updated_at')) AS updated_at
FROM kafka_tables.kafka_orders;

CREATE MATERIALIZED VIEW kafka_tables.mv_order_items
TO demo_tables.order_items
AS
SELECT
    JSONExtractUInt(payload, 'id') AS id,
    JSONExtractUInt(payload, 'order_id') AS order_id,
    JSONExtractUInt(payload, 'product_id') AS product_id,
    JSONExtractUInt(payload, 'quantity') AS quantity,
    toDecimal128(JSONExtract(payload, 'price', 'Float64'), 2) AS price,
    toDecimal128(JSONExtract(payload, 'cost_price', 'Float64'), 2) AS cost_price,
    parseDateTimeBestEffort(JSONExtractString(payload, 'created_at')) AS created_at,
    parseDateTimeBestEffort(JSONExtractString(payload, 'updated_at')) AS updated_at
FROM kafka_tables.kafka_order_items;