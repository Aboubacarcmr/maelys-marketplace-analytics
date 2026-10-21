DELETE FROM analytics.seller_daily WHERE dt = %s::date;
INSERT INTO analytics.seller_daily(dt, seller_id, revenue, orders_count)
SELECT dt, seller_id, SUM(total), COUNT(DISTINCT order_id)
FROM dwh.fact_orders WHERE dt = %s::date AND status = 'paid'
GROUP BY dt, seller_id;

DELETE FROM analytics.category_daily WHERE dt = %s::date;
INSERT INTO analytics.category_daily(dt, category, revenue)
SELECT f.dt, p.category, SUM(f.total)
FROM dwh.fact_orders f JOIN dwh.dim_product p ON p.id = f.product_id
WHERE f.dt = %s::date AND f.status = 'paid'
GROUP BY f.dt, p.category;

DELETE FROM analytics.daily_summary WHERE dt = %s::date;
INSERT INTO analytics.daily_summary(dt, total_orders, total_revenue, total_commission, average_basket)
SELECT dt, COUNT(DISTINCT order_id), SUM(total), SUM(commission),
       ROUND(SUM(total)/NULLIF(COUNT(DISTINCT order_id), 0), 2)
FROM dwh.fact_orders WHERE dt = %s::date AND status = 'paid'
GROUP BY dt;
