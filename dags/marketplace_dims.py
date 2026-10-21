"""Rafraîchissement quotidien, indépendant, des dimensions catalogue/vendeurs."""
from datetime import datetime, timezone
from airflow.sdk import dag, task
from marketplace_hook import MarketplaceAPIHook
from etl_utils import upsert_dimensions


@dag(dag_id="marketplace_dims_refresh_daily", schedule="@daily",
     start_date=datetime(2026, 4, 1, tzinfo=timezone.utc), catchup=False,
     max_active_runs=1, tags=["maelys", "dimensions"])
def marketplace_dims_refresh_daily():
    @task
    def refresh():
        hook = MarketplaceAPIHook()
        upsert_dimensions(hook.get_sellers(), hook.get_products())

    refresh()


marketplace_dims_refresh_daily()
