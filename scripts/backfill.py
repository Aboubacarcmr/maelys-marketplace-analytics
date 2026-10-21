"""Charge chronologiquement N jours via la commande officielle Airflow DAG test.
Lancer depuis le terminal Codespaces après démarrage des services.
"""
from __future__ import annotations
import argparse
from datetime import date, timedelta
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--days', type=int, default=10, help='jours (1 à 60)')
parser.add_argument('--end-date', default=date.today().isoformat())
args = parser.parse_args()
if not 1 <= args.days <= 60:
    parser.error('--days doit être entre 1 et 60')
end = date.fromisoformat(args.end_date)
# Dernier jour complet : hier par défaut (peut être fixé par l'utilisateur)
if args.end_date == date.today().isoformat():
    end -= timedelta(days=1)
for offset in reversed(range(args.days)):
    day = (end - timedelta(days=offset)).isoformat()
    print(f'\n=== Pipeline {day} ===', flush=True)
    subprocess.run(['docker', 'compose', 'exec', '-T', 'airflow-worker', 'airflow',
                    'dags', 'test', 'marketplace_orders_ingest_daily', day], check=True)
print(f'\n{args.days} dates traitées (rejouables sans doublons).')
