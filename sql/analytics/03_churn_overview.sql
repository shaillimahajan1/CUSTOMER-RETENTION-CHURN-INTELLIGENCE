-- 03_churn_overview.sql
-- Executive Churn Overview: Aggregations across contract, internet service, payment, and tenure

-- 1. Global Metrics
CREATE OR REPLACE VIEW analytics.v_executive_summary AS
SELECT
    COUNT(*) AS total_customers,
    SUM(churn_label) AS churned_customers,
    COUNT(*) - SUM(churn_label) AS retained_customers,
    ROUND(AVG(churn_label) * 100.0, 2) AS churn_rate_pct,
    ROUND(SUM(monthly_charges), 2) AS total_monthly_revenue,
    ROUND(SUM(CASE WHEN churn_label = 1 THEN monthly_charges ELSE 0 END), 2) AS churned_monthly_revenue,
    ROUND(AVG(monthly_charges), 2) AS avg_monthly_charges,
    ROUND(AVG(tenure_months), 1) AS avg_tenure_months
FROM staging.customers;

-- 2. Churn by Contract Type
CREATE OR REPLACE VIEW analytics.v_churn_by_contract AS
SELECT
    contract_type,
    COUNT(*) AS total_customers,
    SUM(churn_label) AS churned_customers,
    ROUND(AVG(churn_label) * 100.0, 2) AS churn_rate_pct,
    ROUND(SUM(monthly_charges), 2) AS total_monthly_revenue,
    ROUND(SUM(CASE WHEN churn_label = 1 THEN monthly_charges ELSE 0 END), 2) AS churned_monthly_revenue
FROM staging.customers
GROUP BY contract_type
ORDER BY churn_rate_pct DESC;

-- 3. Churn by Internet Service
CREATE OR REPLACE VIEW analytics.v_churn_by_internet AS
SELECT
    internet_service,
    COUNT(*) AS total_customers,
    SUM(churn_label) AS churned_customers,
    ROUND(AVG(churn_label) * 100.0, 2) AS churn_rate_pct,
    ROUND(AVG(monthly_charges), 2) AS avg_monthly_charges
FROM staging.customers
GROUP BY internet_service
ORDER BY churn_rate_pct DESC;

-- 4. Churn by Payment Method
CREATE OR REPLACE VIEW analytics.v_churn_by_payment AS
SELECT
    payment_method,
    COUNT(*) AS total_customers,
    SUM(churn_label) AS churned_customers,
    ROUND(AVG(churn_label) * 100.0, 2) AS churn_rate_pct,
    ROUND(AVG(monthly_charges), 2) AS avg_monthly_charges
FROM staging.customers
GROUP BY payment_method
ORDER BY churn_rate_pct DESC;

-- 5. Churn by Tenure Cohort Group
CREATE OR REPLACE VIEW analytics.v_churn_by_tenure_cohort AS
SELECT
    tenure_cohort_group,
    COUNT(*) AS total_customers,
    SUM(churn_label) AS churned_customers,
    ROUND(AVG(churn_label) * 100.0, 2) AS churn_rate_pct,
    ROUND(SUM(monthly_charges), 2) AS total_monthly_revenue,
    ROUND(AVG(monthly_charges), 2) AS avg_monthly_charges
FROM staging.customers
GROUP BY tenure_cohort_group
ORDER BY MIN(tenure_months) ASC;
