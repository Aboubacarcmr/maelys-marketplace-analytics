#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
DAY="${1:-2026-04-07}"
query="SELECT COUNT(*) FROM dwh.fact_orders WHERE dt = '$DAY';"
run_dag() {
  docker compose exec -T airflow-worker airflow dags test marketplace_orders_ingest_daily "$DAY" >/dev/null
}
read_count() {
  docker compose exec -T postgres-dwh psql -U "$(sed -n 's/^DWH_USER=//p' .env)" -d dwh -At -c "$query" | tr -d '\r'
}
run_dag
FIRST=$(read_count)
run_dag
SECOND=$(read_count)
echo "Idempotence pour $DAY : premier run=$FIRST ; deuxième run=$SECOND"
if [[ "$FIRST" -gt 0 && "$FIRST" == "$SECOND" ]]; then
  echo 'SUCCÈS : même nombre de lignes, sans duplication.'
else
  echo 'ÉCHEC : données absentes ou idempotence non respectée.' >&2
  exit 1
fi
