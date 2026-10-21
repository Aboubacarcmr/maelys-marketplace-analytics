# Justification des choix — Maelys Marketplace

- **API Flask déterministe** : conformément au cahier, elle renvoie les mêmes commandes pour une date donnée ; le code utilise MD5 pour produire une graine pseudo-aléatoire et permet une vérification de l'idempotence.
- **Airflow 3.1.8 / CeleryExecutor** : orchestre les tâches, exécute les relances et propose une interface de monitoring. Il est plus lourd que LocalExecutor, mais correspond au kit décrit dans le sujet.
- **MinIO** : conserve les réponses JSON brutes dans `data-lake/raw/orders/dt=YYYY-MM-DD/data.json`, réutilisables en cas de retraitement.
- **PostgreSQL 18** : sépare `staging`, `dwh` et `analytics` ; type numeric plutôt que float pour les montants financiers.
- **Schéma en étoile** : table des lignes de commande `dwh.fact_orders` (grain : une ligne d'article par commande), dimensions `dim_seller`, `dim_product`, `dim_date`, FKs et clés primaires. Un ordre multi-vendeur génère plusieurs faits. Le nombre de commandes doit être calculé avec `COUNT(DISTINCT order_id)`.
- **Commissions de 12 %** : calculées par ligne sur le prix de ligne ; la somme peut différer de quelques centimes d'un arrondi sur le total global de commande.
- **Données annulées** : stockées pour la traçabilité, mais exclues des tableaux de bord de CA/commissions.
- **Idempotence** : remplacement en transaction des partitions par `DELETE` puis `INSERT` dans staging et dwh ; les agrégations journalières sont remplacées.
- **Metabase 0.59** : tableaux de bord simples, volume persistant, connexion au réseau Docker sur l'hôte `postgres-dwh`.
- **Pas de Spark/dbt** : inutilement complexes pour cet exercice.
- **Testabilité** : code métier indépendant d'Airflow (`marketplace_data.py`), tests du JSON, schéma, contrôles et DAGs.

## Écarts volontaires / limites

- Le **kit API Flask d'origine** et la **documentation commune** référencés dans le sujet n'étaient pas joints. L'API incluse reproduit les routes et la logique déterministe documentées, mais pas nécessairement son format JSON exact.
- Volume fictif réduit à environ **135–174 commandes par jour**, afin de rester dans les ressources de Codespaces. Les chiffres d'activité de Maelys dans le contexte sont narratifs, pas des données réelles.
- Le DAG `marketplace_analytics_aggregate_daily` est déclenchable à la demande, tandis que l'agrégation systématique après ingestion est garantie par le DAG principal. L'architecture « asset-scheduled » est une piste d'évolution, non une exigence du MVP.
- Les métriques Prometheus/Grafana (bonus) ne sont pas installées par défaut pour économiser mémoire et stockage.
- **Usage uniquement pédagogique :** secrets locaux, services ouverts par redirection privée Codespaces, pas de chiffrement TLS entre services, ni sauvegardes externalisées.
