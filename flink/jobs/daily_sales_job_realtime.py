from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.functions import ProcessWindowFunction
from pyflink.datastream.window import TimeWindow, TumblingEventTimeWindows
from pyflink.common import Row, WatermarkStrategy, Duration
from pyflink.datastream.connectors import FlinkKafkaConsumer
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common import Time
import json
from dateutil import parser
import clickhouse_connect

# Initialize ClickHouse client
client = clickhouse_connect.get_client(
    host='clickhouse-server',
    port=8123,
    username='admin',
    password='admin'
)

class SalesAggregationWindow(ProcessWindowFunction):
    def process(self, key, context: Window.Context, elements, out: list):
        total_orders = len(set(e['order_id'] for e in elements))
        total_items_sold = sum(e['quantity'] for e in elements)
        total_revenue = sum(e['price'] * e['quantity'] for e in elements)
        total_cost = sum(e['cost_price'] * e['quantity'] for e in elements)
        total_profit = total_revenue - total_cost
        average_order_value = total_revenue / total_orders if total_orders else 0

        out.append({
            'date': datetime.now().date().isoformat(),
            'total_orders': total_orders,
            'total_items_sold': total_items_sold,
            'total_revenue': total_revenue,
            'total_cost': total_cost,
            'total_profit': total_profit,
            'average_order_value': average_order_value
        })

class BulkWriteToClickHouse(ProcessWindowFunction):
    def __init__(self, table_name):
        self.table_name = table_name

    def open(self, ctx: RuntimeContext):
        pass  # Already initialized above

    def process(self, ctx, in_elem, out):
        values = [list(row.values()) for row in in_elem]
        cols = list(in_elem[0].keys())

        col_str = ", ".join(cols)
        placeholder_str = ", ".join(["%s"] * len(cols))

        query = f"INSERT INTO demo_tables.daily_sales_stats ({col_str}) VALUES ({placeholder_str})"
        client.command(query, values)

def run_sales_aggregation():
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1)

    env.add_jars("file:///opt/flink/lib/flink-connector-kafka_2.12-1.16.0.jar")

    source = FlinkKafkaConsumer(
        topics='dbserver1.demo.order_items',
        deserialization_schema=SimpleStringSchema(),
        properties={'bootstrap.servers': 'kafka:9092', 'group.id': 'flink_sales_group'}
    ).set_start_from_latest()

    watermark_strategy = (
        WatermarkStrategy.for_bounded_out_of_orderness(Time.seconds(10))
        .with_timestamp_assigner(lambda event, _: extract_event_time(event))
    )

    env.add_source(source) \
        .assign_timestamps_and_watermarks(watermark_strategy) \
        .key_by(lambda x: json.loads(x)['order_id']) \
        .window(TumblingEventTimeWindows.of(Time.hours(1))) \
        .process(SalesAggregationWindow()) \
        .map(BulkWriteToClickHouse('daily_sales_stats')) \
        .name("Real-Time Sales Aggregation") \
        .disable_chaining()

    env.execute("Real-Time Sales Aggregation")