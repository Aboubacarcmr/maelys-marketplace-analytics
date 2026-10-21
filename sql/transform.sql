-- Exécuté dans une transaction (une seule connexion) par date.
-- DELETE + INSERT : l'exécution répétée ne multiplie pas les lignes.
INSERT INTO dwh.dim_date(dt, year, month, day_of_week)
VALUES (%s::date, EXTRACT(YEAR FROM %s::date), EXTRACT(MONTH FROM %s::date), EXTRACT(ISODOW FROM %s::date))
ON CONFLICT(dt) DO NOTHING;

DELETE FROM dwh.fact_orders WHERE dt = %s::date;

INSERT INTO dwh.fact_orders(
    order_id, line_id, dt, seller_id, product_id, quantity, unit_price, total, commission, status
)
SELECT order_id, line_id, dt, seller_id, product_id, quantity, unit_price,
       total, ROUND(total * 0.12, 2), status
FROM staging.orders
WHERE dt = %s::date;
