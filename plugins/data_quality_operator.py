"""Operator de contrôle qualité réutilisable (bonus du cahier)."""
from airflow.exceptions import AirflowException
from airflow.sdk import BaseOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook


class DataQualityOperator(BaseOperator):
    template_fields = ("day",)

    def __init__(self, *, day: str, conn_id: str = "postgres_dwh", rules=None, **kwargs):
        super().__init__(**kwargs)
        self.day = day
        self.conn_id = conn_id
        self.rules = rules or ["not_empty", "not_null", "no_future_date"]

    def execute(self, context):
        hook = PostgresHook(postgres_conn_id=self.conn_id)
        allowed = {"not_empty", "not_null", "no_future_date"}
        for rule in self.rules:
            if rule not in allowed:
                raise AirflowException(f"Règle DQ non reconnue : {rule}")
        if "not_empty" in self.rules:
            total = hook.get_first("SELECT COUNT(*) FROM staging.orders WHERE dt = %s::date", (self.day,))[0]
            if total == 0:
                raise AirflowException(f"Pas de lignes staging pour {self.day}")
        if "not_null" in self.rules:
            nulls = hook.get_first("""SELECT COUNT(*) FROM staging.orders
                WHERE dt=%s::date AND (order_id IS NULL OR product_id IS NULL OR seller_id IS NULL
                OR total IS NULL OR quantity IS NULL)""", (self.day,))[0]
            if nulls:
                raise AirflowException(f"{nulls} lignes contenant des champs NULL")
        if "no_future_date" in self.rules:
            future = hook.get_first("SELECT (%s::date > CURRENT_DATE)", (self.day,))[0]
            if future:
                raise AirflowException("Données datées dans le futur")
        self.log.info("3 contrôles de qualité validés pour %s", self.day)
        return True
