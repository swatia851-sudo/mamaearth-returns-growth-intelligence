-- ============================================================
-- (a) ORDER TOTALS
-- ============================================================

-- total_orders = 180
-- total_revenue = 99860.2
-- avg_order_value = 554.78

SELECT
    COUNT(*) AS total_orders,
    ROUND(SUM(
        o.quantity * p.price *
        (1 - COALESCE(o.discount_pct, 0) / 100.0)
    ), 2) AS total_revenue,
    ROUND(AVG(
        o.quantity * p.price *
        (1 - COALESCE(o.discount_pct, 0) / 100.0)
    ), 2) AS avg_order_value
FROM orders o
JOIN products p
    ON o.product_id = p.product_id;


-- ============================================================
-- (b) COUNT(*) VS COUNT(rating)
-- ============================================================

-- total_rows = 180
-- rated_orders = 165
-- unrated_orders = 15

SELECT
    COUNT(*) AS total_rows,
    COUNT(rating) AS rated_orders,
    COUNT(*) - COUNT(rating) AS unrated_orders
FROM orders;


-- ============================================================
-- (c) LEFT JOIN WITH A GENUINE ZERO-MATCH ROW
-- ============================================================

-- LEFT JOIN output:
-- customer_id = C045
-- name = Vihaan

SELECT
    c.customer_id,
    c.name
FROM customers c
LEFT JOIN orders o
    ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name
HAVING COUNT(o.order_id) = 0;


-- NOT IN output:
-- customer_id = C045
-- name = Vihaan

SELECT
    customer_id,
    name
FROM customers
WHERE customer_id NOT IN (
    SELECT DISTINCT customer_id
    FROM orders
);


-- ============================================================
-- (d) GROUP BY + HAVING
-- ============================================================

-- Jaipur = 19 total orders, 8 returned, 42.1%
-- Lucknow = 49 total orders, 15 returned, 30.6%
-- Bangalore = 33 total orders, 8 returned, 24.2%

SELECT
    c.city,
    COUNT(*) AS total_orders,
    SUM(o.returned) AS returned_orders,
    ROUND(100.0 * SUM(o.returned) / COUNT(*), 1) AS return_rate_pct
FROM orders o
JOIN customers c
    ON o.customer_id = c.customer_id
GROUP BY c.city
HAVING return_rate_pct > 20
ORDER BY return_rate_pct DESC;


-- ============================================================
-- (e) RANKING WITH ORDER BY + LIMIT/OFFSET
-- ============================================================

-- Top 5:
-- C043 | Reyansh | 12920.0
-- C026 | Isha | 8371.6
-- C008 | Meera | 4564.6
-- C011 | Arjun | 4111.0
-- C042 | Sanya | 3785.0

-- customer_id ASC provides a consistent order when total_spend values are tied.

SELECT
    c.customer_id,
    c.name,
    ROUND(SUM(
        o.quantity * p.price *
        (1 - COALESCE(o.discount_pct, 0) / 100.0)
    ), 2) AS total_spend
FROM orders o
JOIN products p
    ON o.product_id = p.product_id
JOIN customers c
    ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
ORDER BY total_spend DESC, c.customer_id ASC
LIMIT 5;


-- Ranks 3–5:
-- C008 | Meera | 4564.6
-- C011 | Arjun | 4111.0
-- C042 | Sanya | 3785.0

SELECT
    c.customer_id,
    c.name,
    ROUND(SUM(
        o.quantity * p.price *
        (1 - COALESCE(o.discount_pct, 0) / 100.0)
    ), 2) AS total_spend
FROM orders o
JOIN products p
    ON o.product_id = p.product_id
JOIN customers c
    ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
ORDER BY total_spend DESC, c.customer_id ASC
LIMIT 3 OFFSET 2;


-- ============================================================
-- (f) THREE-TABLE JOIN WITH GROUP BY
-- ============================================================

-- Haircare | 54 | 44956.1
-- Skincare | 60 | 27346.0
-- Babycare | 30 | 16805.0
-- PersonalCare | 36 | 10753.1

SELECT
    p.category,
    COUNT(*) AS order_count,
    ROUND(SUM(
        o.quantity * p.price *
        (1 - COALESCE(o.discount_pct, 0) / 100.0)
    ), 2) AS category_revenue
FROM orders o
JOIN products p
    ON o.product_id = p.product_id
JOIN customers c
    ON o.customer_id = c.customer_id
GROUP BY p.category
ORDER BY category_revenue DESC;


-- ============================================================
-- (g) LIKE PATTERN MATCH
-- ============================================================

-- C001 | Aarav
-- C003 | Aditi
-- C004 | Ananya
-- C011 | Arjun
-- C021 | Aryan
-- C030 | Anika
-- C031 | Aditya
-- C036 | Aisha
-- C041 | Ayaan
-- C044 | Aria

SELECT
    customer_id,
    name
FROM customers
WHERE name LIKE 'A%';


-- ============================================================
-- (h) DISTINCT
-- ============================================================

-- Ad
-- Organic
-- Referral
-- Social

SELECT DISTINCT acquisition_source
FROM customers
ORDER BY acquisition_source;


-- ============================================================
-- (i) ALTER TABLE + UPDATE WITH CASE
-- ============================================================

-- Gold = 28
-- Silver = 17

ALTER TABLE customers
ADD COLUMN loyalty_tier VARCHAR(10);

UPDATE customers
SET loyalty_tier =
    CASE
        WHEN city_tier = 1 THEN 'Gold'
        ELSE 'Silver'
    END;

SELECT
    loyalty_tier,
    COUNT(*)
FROM customers
GROUP BY loyalty_tier;