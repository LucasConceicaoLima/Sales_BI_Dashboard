CREATE OR REPLACE VIEW vw_sales_monthly AS
SELECT
    d.year,
    d.month_number,
    d.month_name,
    d.year_month,

    ROUND(SUM(f.net_revenue), 2) AS revenue,

    ROUND(SUM(f.gross_profit), 2) AS gross_profit,

    ROUND(
        CASE
            WHEN SUM(f.net_revenue) <> 0
            THEN SUM(f.gross_profit)
                 / SUM(f.net_revenue) * 100
            ELSE 0
        END,
        2
    ) AS margin_pct,

    SUM(f.net_quantity) AS units,

    COUNT(DISTINCT f.sale_id) AS transactions,

    COUNT(DISTINCT f.customer_id) AS active_customers

FROM fact_sales f

JOIN dim_date d
    ON d.date_id = f.date_id

GROUP BY
    d.year,
    d.month_number,
    d.month_name,
    d.year_month;


CREATE OR REPLACE VIEW vw_sales_by_region AS
SELECT
    r.region,
    r.state,

    ROUND(SUM(f.net_revenue), 2) AS revenue,

    ROUND(SUM(f.gross_profit), 2) AS gross_profit,

    SUM(f.net_quantity) AS units,

    COUNT(DISTINCT f.sale_id) AS transactions

FROM fact_sales f

JOIN dim_region r
    ON r.region_id = f.region_id

GROUP BY
    r.region,
    r.state;


CREATE OR REPLACE VIEW vw_sales_by_category AS
SELECT
    p.category,
    p.subcategory,

    ROUND(SUM(f.net_revenue), 2) AS revenue,

    ROUND(SUM(f.gross_profit), 2) AS gross_profit,

    SUM(f.net_quantity) AS units,

    ROUND(
        AVG(f.discount_pct) * 100,
        2
    ) AS avg_discount_pct

FROM fact_sales f

JOIN dim_product p
    ON p.product_id = f.product_id

GROUP BY
    p.category,
    p.subcategory;


CREATE OR REPLACE VIEW vw_customer_metrics AS
SELECT
    c.customer_id,
    c.customer_name,
    c.segment,
    c.city,
    c.state,

    ROUND(SUM(f.net_revenue), 2) AS lifetime_revenue,

    ROUND(SUM(f.gross_profit), 2) AS lifetime_profit,

    COUNT(DISTINCT f.sale_id) AS transactions,

    MIN(d.date) AS first_purchase,

    MAX(d.date) AS last_purchase

FROM fact_sales f

JOIN dim_customer c
    ON c.customer_id = f.customer_id

JOIN dim_date d
    ON d.date_id = f.date_id

GROUP BY
    c.customer_id,
    c.customer_name,
    c.segment,
    c.city,
    c.state;