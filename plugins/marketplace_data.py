"""Transformations métier testables indépendamment du moteur Airflow."""
from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

COMMISSION_RATE = Decimal("0.12")


def flatten_orders(payload: list[dict], expected_day: str) -> list[tuple]:
    date.fromisoformat(expected_day)
    lines = []
    unique = set()
    for order in payload:
        if order["date"] != expected_day:
            raise ValueError(f"Date inattendue dans commande {order.get('order_id')}")
        if order.get("status") not in ("paid", "cancelled"):
            raise ValueError("Statut de commande inconnu")
        for item in order["items"]:
            quantity = int(item["quantity"])
            price = Decimal(str(item["unit_price"]))
            if quantity <= 0 or price < 0:
                raise ValueError("Quantité/prix invalide")
            key = (str(order["order_id"]), int(item["item_id"]))
            if key in unique:
                raise ValueError(f"Ligne de commande dupliquée : {key}")
            unique.add(key)
            total = (price * quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            lines.append((order["order_id"], item["item_id"], expected_day,
                          item["seller_id"], item["product_id"], quantity, price,
                          total, order["status"]))
    return lines


def validate_records(rows: list[tuple], day: str) -> None:
    """Règles de Data Quality : non vide, NOT NULL, pas de date future."""
    if not rows:
        raise ValueError("Staging vide")
    if any(any(value is None for value in row) for row in rows):
        raise ValueError("Valeur NULL détectée")
    if date.fromisoformat(day) > date.today():
        raise ValueError("La date source est dans le futur")
