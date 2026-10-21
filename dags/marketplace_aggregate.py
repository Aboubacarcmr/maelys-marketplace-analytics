"""DAG de réagrégation à la demande (l'agrégation automatique est dans le DAG ELT)."""
from datetime import datetime, timezone
from airflow.sdk import dag, task
from etl_utils import execute_sql_file


@dag(dag_id="marketplace_analytics_aggregate_daily", schedule=None,
     start_date=datetime(2026, 4, 1, tzinfo=timezone.utc), catchup=False,
     tags=["maelys", "analytics"])
def marketplace_analytics_aggregate_daily():
    @task
    def rebuild(day: str):
        execute_sql_file("aggregate.sql", day)

    rebuild("{{ ds }}")


marketplace_analytics_aggregate_daily()
