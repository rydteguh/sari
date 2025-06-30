from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import clickhouse_connect
import logging

default_args = {
    'owner': 'sari',
    'depends_on_past': False,
    'start_date': datetime(2025, 6, 1),  # Changed to a past date so we can see the DAG
    'retries': 3,  # Increased retries
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'daily_sales_metrics',
    default_args=default_args,
    description='Calculate daily sales metrics every 6 hours',
    schedule_interval='0 */6 * * *',  # Every 6 hours
    catchup=False,
)

def calculate_daily_sales(**kwargs):
    logger = logging.getLogger(__name__)
    logger.info("Starting daily sales calculation")
    
    try:
        logger.info("Attempting to connect to ClickHouse")
        client = clickhouse_connect.get_client(
            host='clickhouse',
            port=8123,
            username='default',
            password='clickhouse',
            database='demo_tables'
        )
        logger.info("Successfully connected to ClickHouse")

        query = """
        SELECT
            toDate(orders.created_at) AS date,
            COUNT(DISTINCT orders.id) AS total_orders,
            SUM(order_items.quantity) AS total_items_sold,
            SUM(order_items.price * order_items.quantity) AS total_revenue,
            SUM(order_items.cost_price * order_items.quantity) AS total_cost,
            SUM((order_items.price - order_items.cost_price) * order_items.quantity) AS total_profit,
            divide(SUM(order_items.price * order_items.quantity), COUNT(DISTINCT orders.id)) AS average_order_value
        FROM orders
        JOIN order_items ON orders.id = order_items.order_id
        WHERE orders.status = 'completed'
          AND orders.created_at >= today() - 1
        GROUP BY date
        """

        logger.info("Executing query to fetch daily sales metrics")
        result = client.query(query)
        rows = result.result_rows

        if not rows:
            logger.info("No data found for today's metrics.")
            return

        logger.info(f"Found {len(rows)} rows of data")

        insert_sql = """
        INSERT INTO demo_tables.daily_sales_stats (
            date,
            total_orders,
            total_items_sold,
            total_revenue,
            total_cost,
            total_profit,
            average_order_value
        ) VALUES
        """

        values = [
            f"('{row[0]}', {row[1]}, {row[2]}, {row[3]}, {row[4]}, {row[5]}, {row[6]})"
            for row in rows
        ]

        insert_sql += ', '.join(values)

        logger.info("Deleting existing records for today")
        client.command("ALTER TABLE demo_tables.daily_sales_stats DELETE WHERE date = today()")
        
        logger.info("Inserting new records")
        client.command(insert_sql)
        
        logger.info("Daily sales calculation completed successfully")

    except Exception as e:
        logger.error(f"Error in daily sales calculation: {str(e)}")
        raise  # Re-raise the exception so Airflow knows the task failed


calculate_task = PythonOperator(
    task_id='calculate_daily_sales',
    python_callable=calculate_daily_sales,
    provide_context=True,
    dag=dag,
)

calculate_task