# Fallback : Metabase à configurer à la main

Si `python3 scripts/bootstrap_metabase.py` renvoie un code d'erreur (l'API Metabase est non versionnée), les dashboards restent réalisables sans changer les autres services.

1. Ouvrir le port **3000** depuis l'onglet **Ports** de Codespaces.
2. Premier login : créer le compte admin dont l'adresse et le mot de passe figurent dans `.env`.
3. Administration → Bases de données → Ajouter PostgreSQL :
   - Hôte : `postgres-dwh`
   - Port : `5432`
   - Base : `dwh`
   - Nom utilisateur : valeur `DWH_USER` du `.env`
   - Mot de passe : valeur `DWH_PASSWORD` du `.env`
4. Créer des **Questions → Nouvelle question → Requête SQL** avec les requêtes de `scripts/bootstrap_metabase.py` (fonction `sql_cards`). Ajouter ces questions à deux nouveaux dashboards.

## Tableau de bord 1 — Executive Summary
- **CA du dernier jour chargé** : indicateur / Scalar.
- **CA quotidien - 30 jours** : graphique en ligne.
- **Top 5 vendeurs du dernier jour** : graphique en barres.

## Tableau de bord 2 — Top Sellers
- **Top 10 vendeurs du mois** : barres.
- **Évolution CA des top 3 vendeurs** : lignes.
- **Vendeurs inactifs depuis 7 jours** : tableau.

## Bonus
- Finance et commissions : **Commissions totales** (indicateur) et **Commissions et chiffre d’affaires par jour** (courbe).
- Catégories : **CA par catégorie** (barres).

Les dates affichées correspondent aux dates des données importées. Le « dernier jour chargé » est préférable à `CURRENT_DATE` pour les données pédagogiques historiques.

Le compte Metabase et les dashboards sont dans le volume `metabase-data` : `docker compose down` les préserve, mais `docker compose down -v` les supprime !
