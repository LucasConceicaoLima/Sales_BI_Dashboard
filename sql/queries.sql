-- ============================================================
-- 1. Executive KPIs
-- ============================================================

SELECT
    ROUND(SUM(net_revenue), 2) AS revenue,

    ROUND(SUM(gross_profit), 2) AS gross_profit,

    ROUND(
        SUM(gross_profit)
        / NULLIF(SUM(net_revenue), 0) * 100,
        2
    ) AS margin_pct,

    COUNT(DISTINCT sale_id) AS transactions,

    ROUND(
        SUM(net_revenue)
        / NULLIF(COUNT(DISTINCT sale_id), 0),
        2
    ) AS avg_ticket

FROM fact_sales;


-- ============================================================
-- 2. Monthly revenue trend
-- ============================================================

SELECT *
FROM vw_sales_monthly
ORDER BY
    year,
    month_number;


-- ============================================================
-- 3. Top 10 products by revenue
-- ============================================================

SELECT
    p.product_name,
    p.category,

    ROUND(SUM(f.net_revenue), 2) AS revenue,

    ROUND(SUM(f.gross_profit), 2) AS gross_profit

FROM fact_sales f

JOIN dim_product p
    ON p.product_id = f.product_id

GROUP BY
    p.product_name,
    p.category

ORDER BY
    revenue DESC

LIMIT 10;


-- ============================================================
-- 4. Seller ranking
-- ============================================================

SELECT
    s.seller_name,
    s.seller_team,

    ROUND(SUM(f.net_revenue), 2) AS revenue,

    ROUND(SUM(f.gross_profit), 2) AS gross_profit,

    COUNT(DISTINCT f.sale_id) AS transactions

FROM fact_sales f

JOIN dim_seller s
    ON s.seller_id = f.seller_id

GROUP BY
    s.seller_name,
    s.seller_team

ORDER BY
    revenue DESC;


-- ============================================================
-- 5. Year-over-year growth
-- ============================================================

WITH yearly AS (
    SELECT
        d.year,
        SUM(f.net_revenue) AS revenue

    FROM fact_sales f

    JOIN dim_date d
        ON d.date_id = f.date_id

    GROUP BY
        d.year
)

SELECT
    year,

    ROUND(revenue, 2) AS revenue,

    ROUND(
        (
            revenue
            / NULLIF(
                LAG(revenue) OVER (ORDER BY year),
                0
            ) - 1
        ) * 100,
        2
    ) AS yoy_growth_pct

FROM yearly

ORDER BY
    year;


-- ============================================================
-- 6. Revenue and margin by channel
-- ============================================================

SELECT
    channel,

    ROUND(SUM(net_revenue), 2) AS revenue,

    ROUND(SUM(gross_profit), 2) AS gross_profit,

    ROUND(
        SUM(gross_profit)
        / NULLIF(SUM(net_revenue), 0) * 100,
        2
    ) AS margin_pct

FROM fact_sales

GROUP BY
    channel

ORDER BY
    revenue DESC;