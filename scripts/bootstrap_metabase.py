"""Initialise l'instance Metabase, 4 dashboards et leurs questions SQL.

API Metabase non versionnée : les étapes peuvent demander des adaptations si
la version change. Si le bootstrapping échoue, voir docs/METABASE_MANUEL.md.
"""
from __future__ import annotations

import json
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = 'http://localhost:3000'
ROOT = Path(__file__).resolve().parents[1]


def env_file():
    return {k: v for line in (ROOT / '.env').read_text().splitlines()
            if '=' in line and not line.strip().startswith('#')
            for k,v in [line.split('=',1)]}


def api(method, path, data=None, token=None):
    req = Request(BASE + path, method=method,
                  headers={'Content-Type':'application/json',
                           **({'X-Metabase-Session':token} if token else {})},
                  data=json.dumps(data).encode() if data is not None else None)
    try:
        with urlopen(req, timeout=25) as r:
            result = r.read()
            return json.loads(result) if result else {}
    except HTTPError as exc:
        raise RuntimeError(f'{method} {path}: {exc.code} {exc.read().decode()[:600]}') from exc


def wait_ready():
    for i in range(48):
        try:
            if api('GET','/api/health').get('status') == 'ok':
                return
        except (URLError, RuntimeError):
            pass
        print(f'En attente de Metabase... {i+1}/48', flush=True)
        time.sleep(5)
    raise TimeoutError('Metabase indisponible sur le port 3000')


def sql_cards():
    return {
        'CA du dernier jour chargé': ('scalar', '''SELECT COALESCE(total_revenue,0) AS ca_eur
            FROM analytics.daily_summary ORDER BY dt DESC LIMIT 1'''),
        'CA quotidien - 30 jours': ('line', '''SELECT dt AS date, total_revenue AS ca_eur
            FROM analytics.daily_summary WHERE dt >=
            (SELECT MAX(dt)-29 FROM analytics.daily_summary) ORDER BY dt'''),
        'Top 5 vendeurs du dernier jour': ('bar', '''SELECT s.name AS vendeur, sd.revenue AS ca_eur
            FROM analytics.seller_daily sd JOIN dwh.dim_seller s ON s.id=sd.seller_id
            WHERE sd.dt=(SELECT MAX(dt) FROM analytics.seller_daily)
            ORDER BY sd.revenue DESC LIMIT 5'''),
        'Top 10 vendeurs du mois': ('bar', '''SELECT s.name AS vendeur, SUM(sd.revenue) AS ca_eur
            FROM analytics.seller_daily sd JOIN dwh.dim_seller s ON s.id=sd.seller_id
            WHERE date_trunc('month',sd.dt) = date_trunc('month',
            (SELECT MAX(dt) FROM analytics.seller_daily))
            GROUP BY s.name ORDER BY ca_eur DESC LIMIT 10'''),
        'Évolution CA des top 3 vendeurs': ('line', '''WITH tops AS (
            SELECT seller_id FROM analytics.seller_daily
            WHERE dt >= (SELECT MAX(dt)-29 FROM analytics.seller_daily)
            GROUP BY seller_id ORDER BY SUM(revenue) DESC LIMIT 3)
            SELECT d.dt AS date, s.name AS vendeur, d.revenue AS ca_eur
            FROM analytics.seller_daily d JOIN tops t ON t.seller_id=d.seller_id
            JOIN dwh.dim_seller s ON s.id=d.seller_id ORDER BY d.dt, s.name'''),
        'Vendeurs inactifs depuis 7 jours': ('table', '''SELECT s.name AS vendeur, MAX(sd.dt) AS derniere_vente
            FROM dwh.dim_seller s LEFT JOIN analytics.seller_daily sd ON sd.seller_id=s.id
            GROUP BY s.name HAVING MAX(sd.dt) IS NULL OR MAX(sd.dt) <
            (SELECT MAX(dt)-7 FROM analytics.daily_summary)
            ORDER BY derniere_vente NULLS FIRST'''),
        'Commissions et chiffre d’affaires par jour': ('line', '''SELECT dt AS date,
            total_revenue AS ca_eur,total_commission AS commission_eur
            FROM analytics.daily_summary ORDER BY dt'''),
        'Commissions totales': ('scalar', '''SELECT COALESCE(SUM(total_commission),0) AS commissions_eur
            FROM analytics.daily_summary'''),
        'CA par catégorie': ('bar', '''SELECT category AS categorie,
            SUM(revenue) AS ca_eur FROM analytics.category_daily
            GROUP BY category ORDER BY ca_eur DESC'''),
    }


def main():
    env = env_file()
    wait_ready()
    props = api('GET','/api/session/properties')
    setup_token = props.get('setup-token')
    if setup_token:
        print('Création du premier administrateur Metabase...')
        api('POST','/api/setup', {
            'token':setup_token,
            'user': {'first_name':env['METABASE_ADMIN_FIRST_NAME'],
                     'last_name':env['METABASE_ADMIN_LAST_NAME'],
                     'email':env['METABASE_ADMIN_EMAIL'],
                     'password':env['METABASE_ADMIN_PASSWORD']},
            'prefs':{'site_name':'Maelys Marketplace',
                     'allow_tracking':False}
        })
    session = api('POST','/api/session', {'username':env['METABASE_ADMIN_EMAIL'],
                                          'password':env['METABASE_ADMIN_PASSWORD']})['id']
    databases = api('GET','/api/database',token=session)
    known = next((x for x in databases.get('data',[]) if x['name']=='Maelys DWH'), None)
    if known:
        database_id = known['id']
    else:
        database_id = api('POST','/api/database',{
            'engine':'postgres','name':'Maelys DWH','is_full_sync':False,
            'details':{'host':'postgres-dwh','port':5432,'dbname':'dwh',
                       'user':env['DWH_USER'],'password':env['DWH_PASSWORD'],
                       'ssl':False}},token=session)['id']
    cards = {}
    existing = api('GET','/api/card?f=all',token=session)
    existing_cards = existing if isinstance(existing,list) else existing.get('data',[])
    for title,(display,sql) in sql_cards().items():
        current = next((c for c in existing_cards if c.get('name')==title), None)
        if current:
            cards[title] = current['id']
            continue
        created = api('POST','/api/card',{'name':title,'display':display,'type':'question',
            'dataset_query':{'database':database_id,'type':'native',
                             'native':{'query':sql,'template-tags':{}}},
            'visualization_settings':{}},token=session)
        cards[title] = created['id']
    definitions = {
        '01 — Executive Summary': ['CA du dernier jour chargé','CA quotidien - 30 jours',
                                   'Top 5 vendeurs du dernier jour'],
        '02 — Top Sellers': ['Top 10 vendeurs du mois','Évolution CA des top 3 vendeurs',
                             'Vendeurs inactifs depuis 7 jours'],
        '03 — Finance et commissions': ['Commissions totales',
                                       'Commissions et chiffre d’affaires par jour'],
        '04 — Catégories produits': ['CA par catégorie'],
    }
    existing_db = api('GET','/api/dashboard?f=all',token=session)
    existing_db = existing_db if isinstance(existing_db,list) else existing_db.get('data',[])
    for title,card_names in definitions.items():
        if any(x.get('name')==title for x in existing_db):
            print(f'Dashboard existant : {title}')
            continue
        dashboard_id = api('POST','/api/dashboard',{'name':title,
                            'description':'Maelys - projet final pédagogique'},token=session)['id']
        dashcards = [{'id':-(i+1),'card_id':cards[name],
                      'row':i*6,'col':0,'size_x':12,'size_y':6,
                      'parameter_mappings':[]} for i,name in enumerate(card_names)]
        api('PUT',f'/api/dashboard/{dashboard_id}',{'dashcards':dashcards},token=session)
        print(f'Créé : {title} (ID {dashboard_id})')
    print('\nMetabase opérationnel : ouvrir le port 3000 dans Codespaces.')


if __name__=='__main__':
    try:
        main()
    except Exception as exc:
        print(f'ERREUR de configuration Metabase : {exc}')
        print('Utiliser la méthode manuelle décrite dans docs/METABASE_MANUEL.md')
        raise SystemExit(1)
