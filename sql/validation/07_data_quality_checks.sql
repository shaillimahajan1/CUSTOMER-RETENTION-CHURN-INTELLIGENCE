-- 07_data_quality_checks.sql
-- Automated data quality validation assertions in DuckDB

-- 1. Uniqueness check on customer_id
SELECT
    'PK Uniqueness Check' AS check_name,
    COUNT(*) AS total_rows,
    COUNT(DISTINCT customer_id) AS distinct_keys,
    CASE WHEN COUNT(*) = COUNT(DISTINCT customer_id) THEN 'PASSED' ELSE 'FAILED' END AS status
FROM staging.customers;

-- 2. Null Value Audit across critical fields
SELECT
    'Null Value Audit' AS check_name,
    SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) AS null_customer_id,
    SUM(CASE WHEN tenure_months IS NULL THEN 1 ELSE 0 END) AS null_tenure,
    SUM(CASE WHEN monthly_charges IS NULL THEN 1 ELSE 0 END) AS null_monthly_charges,
    SUM(CASE WHEN total_charges IS NULL THEN 1 ELSE 0 END) AS null_total_charges,
    SUM(CASE WHEN churn_label IS NULL THEN 1 ELSE 0 END) AS null_churn_label,
    CASE
        WHEN SUM(CASE WHEN customer_id IS NULL OR tenure_months IS NULL OR monthly_charges IS NULL OR total_charges IS NULL OR churn_label IS NULL THEN 1 ELSE 0 END) = 0
        THEN 'PASSED'
        ELSE 'FAILED'
    END AS status
FROM staging.customers;

-- 3. Range and Validity Integrity
SELECT
    'Range & Domain Validation' AS check_name,
    SUM(CASE WHEN tenure_months < 0 OR tenure_months > 120 THEN 1 ELSE 0 END) AS invalid_tenure_count,
    SUM(CASE WHEN monthly_charges < 0 THEN 1 ELSE 0 END) AS invalid_monthly_charges_count,
    SUM(CASE WHEN total_charges < 0 THEN 1 ELSE 0 END) AS invalid_total_charges_count,
    SUM(CASE WHEN churn_label NOT IN (0, 1) THEN 1 ELSE 0 END) AS invalid_target_count,
    CASE
        WHEN SUM(CASE WHEN tenure_months < 0 OR monthly_charges < 0 OR total_charges < 0 OR churn_label NOT IN (0, 1) THEN 1 ELSE 0 END) = 0
        THEN 'PASSED'
        ELSE 'FAILED'
    END AS status
FROM staging.customers;
