#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo '### Configuration Docker'
docker compose config -q && echo 'Compose OK'
echo '### État conteneurs'
docker compose ps
echo '### État API'
curl -sf http://localhost:5000/health || true
echo
echo '### Airflow API (dernières lignes)'
docker compose logs --tail=60 airflow-apiserver || true
echo '### Airflow worker (dernières lignes)'
docker compose logs --tail=60 airflow-worker || true
echo '### PostgreSQL (dernières lignes)'
docker compose logs --tail=30 postgres-dwh || true
