"""API simulée Maelys (compatible avec les routes annoncées dans le cahier).

DONNÉES FICTIVES ET DÉTERMINISTES : même date => mêmes commandes.
La vraie API du kit pédagogique n'était pas fournie dans la pièce jointe.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from hashlib import md5
import os
import random

from flask import Flask, jsonify, request

app = Flask(__name__)
CATEGORIES = ["Maison", "Mode", "Beauté", "High-tech", "Sport", "Livres"]
COUNTRIES = ["FR", "BE", "ES", "DE"]


def sellers() -> list[dict]:
    return [
        {"id": i, "name": f"Vendeur {i:03d}", "country": COUNTRIES[i % len(COUNTRIES)],
         "joined_date": "2025-01-15"}
        for i in range(1, 41)
    ]


def products() -> list[dict]:
    return [
        {"id": i, "name": f"Produit {i:04d}", "category": CATEGORIES[i % len(CATEGORIES)],
         "seller_id": ((i - 1) % 40) + 1,
         "price": str(Decimal(9 + (i * 11) % 115) + Decimal("0.90"))}
        for i in range(1, 241)
    ]


def generate_orders(day: str) -> list[dict]:
    """Création reproductible d'un échantillon de commandes pour un jour donné."""
    date.fromisoformat(day)
    rng = random.Random(int(md5(day.encode()).hexdigest(), 16))
    count = 135 + rng.randrange(40)   # ECHANTILLON (non 8500/jour)
    catalogue = products()
    result = []
    for i in range(count):
        item_count = rng.choices([1, 2, 3], weights=[70, 25, 5])[0]
        items = []
        for j in range(item_count):
            product = catalogue[rng.randrange(len(catalogue))]
            qty = rng.randint(1, 3)
            items.append({
                "item_id": j + 1,
                "product_id": product["id"],
                "seller_id": product["seller_id"],
                "quantity": qty,
                "unit_price": product["price"],
            })
        result.append({
            "order_id": f"ORD-{day.replace('-', '')}-{i+1:05d}",
            "date": day,
            "customer_id": f"CUS-{rng.randint(1, 3000):05d}",
            "status": rng.choices(["paid", "cancelled"], weights=[96, 4])[0],
            "items": items,
        })
    return result


@app.before_request
def check_bearer():
    if request.path == "/health":
        return None
    expected = os.environ.get("MARKETPLACE_API_TOKEN", "formation-token-2026")
    if request.headers.get("Authorization") != f"Bearer {expected}":
        return jsonify({"error": "Unauthorized"}), 401
    return None


@app.get("/health")
def health():
    return jsonify({"status": "ok", "version": "1.0-educational"})


@app.get("/orders")
def orders_endpoint():
    day = request.args.get("date", "")
    try:
        return jsonify(generate_orders(day))
    except ValueError:
        return jsonify({"error": "Date attendue au format YYYY-MM-DD"}), 400


@app.get("/sellers")
def sellers_endpoint():
    limit = request.args.get("limit", type=int)
    data = sellers()
    return jsonify(data[:max(0, limit)] if limit is not None else data)


@app.get("/products")
def products_endpoint():
    return jsonify(products())


@app.get("/customers")
def customers_endpoint():
    limit = min(max(request.args.get("limit", default=10, type=int), 0), 3000)
    return jsonify([{"id": f"CUS-{i:05d}"} for i in range(1, limit + 1)])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
