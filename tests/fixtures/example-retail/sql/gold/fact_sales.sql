CREATE OR REPLACE TABLE gold.fact_sales AS
SELECT
    o.order_id,
    o.customer_id,
    o.order_date,
    l.product_id,
    l.quantity,
    l.line_amount,
    p.payment_amount
FROM silver.orders o
JOIN silver.order_lines l ON l.order_id = o.order_id
LEFT JOIN silver.payments p ON p.order_id = o.order_id;
