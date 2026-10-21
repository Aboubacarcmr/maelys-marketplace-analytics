#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs config
python3 scripts/prepare_env.py
if ! docker compose version >/dev/null 2>&1; then
  echo 'Docker Compose est indisponible. Vérifier que Codespaces fournit Docker.' >&2
  exit 1
fi
printf '\n--- Vérification Compose ---\n'
docker compose config -q
printf '\n--- Construction et démarrage (plusieurs minutes la première fois) ---\n'
docker compose up -d --build
printf '\n--- État des conteneurs ---\n'
docker compose ps
printf '\nPorts Codespaces : Airflow 8080, Metabase 3000, MinIO 9001, API 5000.\n'
printf 'Identifiants dans .env (conserver confidentiel).\n'
