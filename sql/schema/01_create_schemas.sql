-- 01_create_schemas.sql
-- Initializes analytical namespaces in DuckDB

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;
