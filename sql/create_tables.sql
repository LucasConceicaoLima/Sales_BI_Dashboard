DROP VIEW IF EXISTS vw_sales_monthly CASCADE;
DROP VIEW IF EXISTS vw_sales_by_region CASCADE;
DROP VIEW IF EXISTS vw_sales_by_category CASCADE;
DROP VIEW IF EXISTS vw_customer_metrics CASCADE;

DROP TABLE IF EXISTS fact_sales CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;
DROP TABLE IF EXISTS dim_customer CASCADE;
DROP TABLE IF EXISTS dim_product CASCADE;
DROP TABLE IF EXISTS dim_seller CASCADE;
DROP TABLE IF EXISTS dim_region CASCADE;


CREATE TABLE dim_region (
    region_id   INTEGER PRIMARY KEY,
    region      VARCHAR(30) NOT NULL,
    state       CHAR(2) NOT NULL
);


CREATE TABLE dim_customer (
    customer_id     INTEGER PRIMARY KEY,
    customer_name   VARCHAR(100) NOT NULL,
    segment         VARCHAR(30) NOT NULL,
    city            VARCHAR(80) NOT NULL,
    state           CHAR(2) NOT NULL
);


CREATE TABLE dim_product (
    product_id      INTEGER PRIMARY KEY,
    product_name    VARCHAR(120) NOT NULL,
    category        VARCHAR(60) NOT NULL,
    subcategory     VARCHAR(60) NOT NULL
);


CREATE TABLE dim_seller (
    seller_id       INTEGER PRIMARY KEY,
    seller_name     VARCHAR(100) NOT NULL,
    seller_team     VARCHAR(30) NOT NULL
);


CREATE TABLE dim_date (
    date_id          INTEGER PRIMARY KEY,
    date             DATE NOT NULL UNIQUE,
    year             SMALLINT NOT NULL,
    quarter          CHAR(2) NOT NULL,
    month_number     SMALLINT NOT NULL,
    month_name       VARCHAR(20) NOT NULL,
    year_month       CHAR(7) NOT NULL,
    day              SMALLINT NOT NULL,
    weekday_number   SMALLINT NOT NULL,
    weekday_name     VARCHAR(20) NOT NULL,
    is_weekend       BOOLEAN NOT NULL
);


CREATE TABLE fact_sales (
    sale_id          VARCHAR(20) PRIMARY KEY,
    date_id          INTEGER NOT NULL REFERENCES dim_date(date_id),
    customer_id      INTEGER NOT NULL REFERENCES dim_customer(customer_id),
    product_id       INTEGER NOT NULL REFERENCES dim_product(product_id),
    seller_id        INTEGER NOT NULL REFERENCES dim_seller(seller_id),
    region_id        INTEGER NOT NULL REFERENCES dim_region(region_id),
    channel          VARCHAR(30) NOT NULL,
    order_status     VARCHAR(20) NOT NULL,
    unit_price       NUMERIC(12,2) NOT NULL,
    quantity         INTEGER NOT NULL,
    net_quantity     INTEGER NOT NULL,
    discount_pct     NUMERIC(8,4) NOT NULL,
    gross_revenue    NUMERIC(14,2) NOT NULL,
    discount_amount  NUMERIC(14,2) NOT NULL,
    net_revenue      NUMERIC(14,2) NOT NULL,
    unit_cost        NUMERIC(12,2) NOT NULL,
    total_cost       NUMERIC(14,2) NOT NULL,
    gross_profit     NUMERIC(14,2) NOT NULL,
    margin_pct       NUMERIC(8,2) NOT NULL
);


CREATE INDEX idx_fact_sales_date
    ON fact_sales(date_id);

CREATE INDEX idx_fact_sales_customer
    ON fact_sales(customer_id);

CREATE INDEX idx_fact_sales_product
    ON fact_sales(product_id);

CREATE INDEX idx_fact_sales_seller
    ON fact_sales(seller_id);

CREATE INDEX idx_fact_sales_region
    ON fact_sales(region_id);