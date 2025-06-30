CREATE DATABASE IF NOT EXISTS demo_tables;

CREATE TABLE demo_tables.products (
    id UInt64,
    name String,
    description String,
    price Decimal(15, 2),
    cost_price Decimal(15, 2),
    created_at DateTime,
    updated_at DateTime,
    kafka_timestamp DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY id;

CREATE TABLE demo_tables.orders (
    id UInt64,
    customer_name String,
    status String,
    total_amount Decimal(15, 2),
    created_at DateTime,
    updated_at DateTime,
    kafka_timestamp DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY id;

CREATE TABLE demo_tables.order_items (
    id UInt64,
    order_id UInt64,
    product_id UInt64,
    quantity UInt32,
    price Decimal(15, 2),
    cost_price Decimal(15, 2),
    created_at DateTime,
    updated_at DateTime,
    kafka_timestamp DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY id;