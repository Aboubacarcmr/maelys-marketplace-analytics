#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

COMPOSE=(docker compose -f docker-compose-simple.yaml)

echo "=== 1. Démarrage des bases de données ==="
"${COMPOSE[@]}" up -d --no-deps postgres-airflow postgres-dwh minio

echo "=== 2. Configuration du réseau Docker ==="
NET_ID=$(docker network inspect -f '{{.Id}}' maelys-marketplace-analytics_default)
BR="br-${NET_ID:0:12}"

sudo iptables-legacy -C FORWARD -i "$BR" -o "$BR" -j ACCEPT 2>/dev/null || \
sudo iptables-legacy -I FORWARD 1 -i "$BR" -o "$BR" -j ACCEPT

echo "Réseau Docker configuré."

echo "=== 3. Démarrage de tous les services ==="
"${COMPOSE[@]}" up -d

echo "=== 4. Vérification des services ==="
"${COMPOSE[@]}" ps -a

echo "=== Démarrage terminé ==="
