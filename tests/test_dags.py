"""Exécuter dans le conteneur Airflow (airflow-worker) pour les vrais tests DAG."""
from pathlib import Path
import pytest

try:
    from airflow.models.dagbag import DagBag
except ImportError:
    DagBag = None


@pytest.fixture(scope='module')
def dagbag():
    if DagBag is None:
        pytest.skip('Airflow absent de cet environnement ; exécuter dans airflow-worker')
    folder = Path(__file__).resolve().parents[1]/'dags'
    return DagBag(dag_folder=str(folder), include_examples=False)


def test_no_import_errors(dagbag):
    assert dagbag.import_errors == {}, dagbag.import_errors


def test_all_dags_catchup_false(dagbag):
    assert dagbag.dags
    assert all(dag.catchup is False for dag in dagbag.dags.values())


def test_marketplace_ingest_has_idempotent_transform(dagbag):
    dag = dagbag.get_dag('marketplace_orders_ingest_daily')
    assert dag is not None
    for task in ['extract_to_raw', 'stage_orders','route_by_quality',
                 'check_data_quality','transform_to_dwh','build_analytics']:
        assert task in dag.task_ids
    transform = dag.get_task('transform_to_dwh')
    assert 'check_data_quality' in transform.upstream_task_ids


def test_idempotent_sql_pattern():
    path = Path(__file__).resolve().parents[1]/'sql/transform.sql'
    sql = path.read_text()
    assert 'DELETE FROM dwh.fact_orders WHERE dt = %s::date' in sql
    assert 'INSERT INTO dwh.fact_orders' in sql
