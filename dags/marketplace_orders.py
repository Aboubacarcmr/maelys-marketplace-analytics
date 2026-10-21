"""DAG principal : API → MinIO → staging → qualité → DWH → agrégations."""
from __future__ import annotations

from datetime import datetime, timezone
import json

from airflow.sdk import dag, task
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.postgres.hooks.postgres import PostgresHook

from marketplace_hook import MarketplaceAPIHook
from marketplace_data import flatten_orders
from data_quality_operator import DataQualityOperator
from etl_utils import execute_sql_file, upsert_dimensions

BUCKET = "data-lake"


@dag(
    dag_id="marketplace_orders_ingest_daily",
    schedule="@daily",
    start_date=datetime(2026, 4, 1, tzinfo=timezone.utc),
    catchup=False,
    max_active_runs=1,
    tags=["maelys", "elt", "mvp"],
)
def marketplace_orders_ingest_daily():
    @task(retries=2)
    def extract_to_raw(day: str):
        payload = MarketplaceAPIHook().get_orders(day)
        key = f"raw/orders/dt={day}/data.json"
        S3Hook(aws_conn_id="minio_s3").load_string(
            json.dumps(payload, ensure_ascii=False), key=key, bucket_name=BUCKET, replace=True
        )
        return {"key": key, "day": day, "orders": len(payload)}

    @task
    def stage_orders(raw: dict):
        body = S3Hook(aws_conn_id="minio_s3").read_key(raw["key"], bucket_name=BUCKET)
        rows = flatten_orders(json.loads(body), raw["day"])
        conn = PostgresHook(postgres_conn_id="postgres_dwh").get_conn()
        try:
            with conn.cursor() as cur:
                # Une partition de date est remplacée en transaction : idem à chaque exécution.
                cur.execute("DELETE FROM staging.orders WHERE dt=%s::date", (raw["day"],))
                cur.executemany("""INSERT INTO staging.orders
                    (order_id,line_id,dt,seller_id,product_id,quantity,unit_price,total,status)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""", rows)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        return raw

    @task
    def sync_dimensions():
        hook = MarketplaceAPIHook()
        upsert_dimensions(hook.get_sellers(), hook.get_products())

    @task.branch
    def route_by_quality(raw: dict):
        rows = PostgresHook(postgres_conn_id="postgres_dwh").get_first(
            "SELECT COUNT(*) FROM staging.orders WHERE dt = %s::date", (raw["day"],)
        )[0]
        return "check_data_quality" if rows > 0 else "alert_data_quality"

    @task
    def alert_data_quality():
        raise RuntimeError("ALERTE : données vides en zone staging ; chargement DWH interrompu")

    @task
    def transform_to_dwh(day: str):
        execute_sql_file("transform.sql", day)

    @task
    def build_analytics(day: str):
        execute_sql_file("aggregate.sql", day)

    raw = extract_to_raw("{{ ds }}")
    staged = stage_orders(raw)
    dimensions = sync_dimensions()
    branch = route_by_quality(staged)
    check = DataQualityOperator(task_id="check_data_quality", day="{{ ds }}")
    warning = alert_data_quality()
    transformed = transform_to_dwh("{{ ds }}")
    aggregated = build_analytics("{{ ds }}")

    branch >> [check, warning]
    dimensions >> check
    check >> transformed >> aggregated


marketplace_orders_ingest_daily()
