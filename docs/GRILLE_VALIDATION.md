# Grille de validation à remplir après démarrage dans Codespaces

Les cases ne sont PAS encore validées : elles nécessitent une exécution réelle de la pile Docker.

- [ ] `docker compose config -q` : configuration acceptée
- [ ] `docker compose ps` : services démarrés et healthy
- [ ] `curl http://localhost:5000/health` : API OK
- [ ] API protégée : 401 sans Bearer, 200 avec Bearer
- [ ] `docker compose exec airflow-worker airflow dags list` : 4 DAGs présents
- [ ] `docker compose exec airflow-worker pytest /opt/airflow/tests -v` : tests Airflow OK
- [ ] Run Airflow `marketplace_orders_ingest_daily` sur 2026-04-07 : success
- [ ] `SELECT COUNT(*) FROM dwh.fact_orders` : > 0
- [ ] `bash scripts/check_idempotence.sh 2026-04-07` : compte identique
- [ ] `python3 scripts/backfill.py --days 10` : historique présent
- [ ] Metabase : connexion PostgreSQL réussie
- [ ] Dashboard Executive Summary : 3 graphiques affichés
- [ ] Dashboard Top Sellers : 3 graphiques affichés
- [ ] Captures d'écran réelles réalisées dans le navigateur

## Requêtes de contrôle

```sql
SELECT dt, COUNT(*) AS lignes, COUNT(DISTINCT order_id) AS commandes
FROM dwh.fact_orders GROUP BY dt ORDER BY dt DESC;

SELECT * FROM analytics.daily_summary ORDER BY dt DESC LIMIT 10;

SELECT * FROM analytics.category_daily ORDER BY dt DESC, revenue DESC LIMIT 10;
```
