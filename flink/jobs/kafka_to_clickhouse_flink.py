from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.functions import RuntimeContext, MapFunction
from pyflink.datastream.connectors import FlinkKafkaConsumer
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common import WatermarkStrategy, Duration
from pyflink.common.typeinfo import Types
from pyflink.common import Configuration
from pyflink.datastream.checkpointing_mode import CheckpointingMode
import json
from datetime import datetime, timedelta
from dateutil import parser
import clickhouse_connect


# Global ClickHouse client
client = None

class DeduplicateByKey(MapFunction):
    def __init__(self):
        self.seen_ids = set()

    def map(self, value):
        record = json.loads(value)
        if record['id'] not in self.seen_ids:
            self.seen_ids.add(record['id'])
            return record
        return None


class WriteToClickHouse(MapFunction):
    def __init__(self, table_name):
        self.table_name = table_name

    def open(self, runtime_context: RuntimeContext):
        global client
        client = clickhouse_connect.get_client(
            host='clickhouse-server',
            port=8123,
            username='admin',
            password='admin'
        )

    def map(self, value):
        if not value:
            return

        try:
            columns = ', '.join(value.keys())
            placeholders = ', '.join(['%s'] * len(value))
            query = f"INSERT INTO demo_tables.order_items ({columns}) VALUES ({placeholders})"
            client.command(query, list(value.values()))
        except Exception as e:
            print(f"[ERROR] Failed to write to ClickHouse: {e}")


def extract_event_time(record):
    ts = json.loads(record).get('created_at')
    return int(parser.parse(ts).timestamp() * 1000)  # Convert to milliseconds


def run_kafka_to_clickhouse_job():
    config = Configuration()
    config.set_string("pipeline.jars", "file:///opt/flink/lib/flink-connector-kafka_2.12-1.16.0.jar")
    env = StreamExecutionEnvironment.get_execution_environment(config)
    env.set_parallelism(1)

    watermark_strategy = (
        WatermarkStrategy.for_bounded_out_of_orderness(Duration.of_seconds(10))
        .with_timestamp_assigner(lambda event, _: extract_event_time(event))
    )

    kafka_source = FlinkKafkaConsumer(
        topics='dbserver1.demo.order_items',
        deserialization_schema=SimpleStringSchema(),
        properties={'bootstrap.servers': 'kafka:9092', 'group.id': 'flink_group'}
    ).set_start_from_latest()

    env.add_source(kafka_source) \
        .assign_timestamps_and_watermarks(watermark_strategy) \
        .map(DeduplicateByKey()) \
        .filter(lambda x: x is not None) \
        .map(WriteToClickHouse('order_items')) \
        .name("Flink → ClickHouse") \
        .disable_chaining()

    env.execute("Real-Time Order Items Ingestion via Flink")


if __name__ == '__main__':
    run_kafka_to_clickhouse_job()