-- Run AFTER:
--   python etl/transform.py
--   psql -U postgres -d sales_bi -f sql/create_tables.sql
--
-- Execute this script from the repository root.

\copy dim_region FROM 'data/processed/dim_region.csv' WITH (FORMAT csv, HEADER true);
\copy dim_customer FROM 'data/processed/dim_customer.csv' WITH (FORMAT csv, HEADER true);
\copy dim_product FROM 'data/processed/dim_product.csv' WITH (FORMAT csv, HEADER true);
\copy dim_seller FROM 'data/processed/dim_seller.csv' WITH (FORMAT csv, HEADER true);
\copy dim_date FROM 'data/processed/dim_date.csv' WITH (FORMAT csv, HEADER true);
\copy fact_sales FROM 'data/processed/fact_sales.csv' WITH (FORMAT csv, HEADER true);
