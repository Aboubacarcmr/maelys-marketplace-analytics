"""Bonus : détecter une chute du CA sous 70 % d'une moyenne des 7 jours précédents."""
from datetime import datetime, timezone
from airflow.sdk import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook


@dag(dag_id="marketplace_anomaly_detect_daily", schedule=None,
     start_date=datetime(2026, 4, 1, tzinfo=timezone.utc), catchup=False,
     tags=["maelys", "bonus", "anomalies"])
def marketplace_anomaly_detect_daily():
    @task
    def detect(day: str):
        conn = PostgresHook(postgres_conn_id="postgres_dwh").get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("""SELECT total_revenue FROM analytics.daily_summary WHERE dt=%s::date""", (day,))
                target = cur.fetchone()
                cur.execute("""SELECT COUNT(*), AVG(total_revenue)
                    FROM analytics.daily_summary WHERE dt < %s::date AND dt >= %s::date - 7""",
                    (day, day))
                count, mean = cur.fetchone()
                if not target or count < 7 or not mean or mean <= 0:
                    return "Historique insuffisant : minimum 7 jours précédents complets"
                ratio = target[0] / mean
                if ratio < 0.70:
                    cur.execute("""INSERT INTO analytics.anomaly_alerts (dt,revenue,mean_7d,ratio,severity)
                        VALUES (%s,%s,%s,%s,'warning') ON CONFLICT(dt) DO UPDATE
                        SET revenue=EXCLUDED.revenue,mean_7d=EXCLUDED.mean_7d,
                            ratio=EXCLUDED.ratio,severity=EXCLUDED.severity,created_at=NOW()""",
                        (day, target[0], mean, ratio))
                    conn.commit()
                    return f"Anomalie CA détectée : ratio {ratio:.2%}"
                cur.execute("DELETE FROM analytics.anomaly_alerts WHERE dt=%s::date", (day,))
            conn.commit()
            return f"CA normal : {ratio:.2%} de la moyenne 7 jours"
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    detect("{{ ds }}")


marketplace_anomaly_detect_daily()
