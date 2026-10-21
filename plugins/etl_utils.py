"""Opérations SQL réutilisables : transactions garanties, paramètres préparés."""
from pathlib import Path

from airflow.providers.postgres.hooks.postgres import PostgresHook

SQL_DIR = Path('/opt/airflow/sql')


def execute_sql_file(file_name: str, day: str) -> None:
    sql = (SQL_DIR / file_name).read_text(encoding='utf-8')
    statements = [x.strip() for x in sql.split(';') if x.strip()]
    hook = PostgresHook(postgres_conn_id='postgres_dwh')
    conn = hook.get_conn()
    try:
        with conn.cursor() as cursor:
            for stmt in statements:
                cursor.execute(stmt, (day,) * stmt.count('%s'))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def upsert_dimensions(sellers: list[dict], products: list[dict]) -> None:
    if not sellers or not products:
        raise ValueError('Dimensions API vides')
    hook = PostgresHook(postgres_conn_id='postgres_dwh')
    conn = hook.get_conn()
    try:
        with conn.cursor() as cur:
            cur.executemany('''INSERT INTO dwh.dim_seller(id,name,country,joined_date)
                VALUES (%s,%s,%s,%s) ON CONFLICT(id) DO UPDATE SET
                name=EXCLUDED.name,country=EXCLUDED.country,joined_date=EXCLUDED.joined_date''',
                [(r['id'],r['name'],r['country'],r['joined_date']) for r in sellers])
            cur.executemany('''INSERT INTO dwh.dim_product(id,name,category,seller_id,price)
                VALUES (%s,%s,%s,%s,%s) ON CONFLICT(id) DO UPDATE SET
                name=EXCLUDED.name,category=EXCLUDED.category,
                seller_id=EXCLUDED.seller_id,price=EXCLUDED.price''',
                [(r['id'],r['name'],r['category'],r['seller_id'],r['price']) for r in products])
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
