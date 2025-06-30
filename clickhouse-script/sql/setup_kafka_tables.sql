CREATE DATABASE IF NOT EXISTS kafka_tables;

CREATE TABLE kafka_tables.kafka_products (
    payload String
) ENGINE = Kafka()
SETTINGS
    kafka_broker_list = 'kafka:9092',
    kafka_topic_list = 'dbserver1.demo.products',
    kafka_group_name = 'clickhouse_kafka_group',
    kafka_format = 'AvroConfluent';

CREATE TABLE kafka_tables.kafka_orders (
    payload String
) ENGINE = Kafka()
SETTINGS
    kafka_broker_list = 'kafka:9092',
    kafka_topic_list = 'dbserver1.demo.orders',
    kafka_group_name = 'clickhouse_kafka_group',
    kafka_format = 'AvroConfluent';

CREATE TABLE kafka_tables.kafka_order_items (
    payload String
) ENGINE = Kafka()
SETTINGS
    kafka_broker_list = 'kafka:9092',
    kafka_topic_list = 'dbserver1.demo.order_items',
    kafka_group_name = 'clickhouse_kafka_group',
    kafka_format = 'AvroConfluent';