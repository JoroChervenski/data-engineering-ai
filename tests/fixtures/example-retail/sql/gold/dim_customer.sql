CREATE OR REPLACE TABLE gold.dim_customer AS
SELECT *
FROM silver.customers;
