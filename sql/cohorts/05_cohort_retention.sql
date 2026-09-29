-- 05_cohort_retention.sql
-- Tenure-based Cohort & Lifecycle Retention Dynamics

-- 1. Monthly Tenure Lifecycle Curve (Month 0 to Month 72)
CREATE OR REPLACE VIEW analytics.v_tenure_lifecycle_curve AS
WITH tenure_counts AS (
    SELECT
        tenure_months,
        COUNT(*) AS total_at_tenure,
        SUM(churn_label) AS churned_at_tenure,
        COUNT(*) - SUM(churn_label) AS active_at_tenure,
        ROUND(AVG(monthly_charges), 2) AS avg_monthly_charges
    FROM staging.customers
    GROUP BY tenure_months
),
tenure_metrics AS (
    SELECT
        tenure_months,
        total_at_tenure,
        churned_at_tenure,
        active_at_tenure,
        avg_monthly_charges,
        SUM(total_at_tenure) OVER (ORDER BY tenure_months ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_customers,
        SUM(churned_at_tenure) OVER (ORDER BY tenure_months ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_churned,
        ROUND(churned_at_tenure * 100.0 / NULLIF(total_at_tenure, 0), 2) AS tenure_specific_churn_rate,
        LAG(total_at_tenure, 1) OVER (ORDER BY tenure_months) AS prev_month_customers
    FROM tenure_counts
)
SELECT
    tenure_months,
    total_at_tenure,
    churned_at_tenure,
    active_at_tenure,
    avg_monthly_charges,
    cumulative_customers,
    cumulative_churned,
    tenure_specific_churn_rate,
    ROUND((total_at_tenure - COALESCE(prev_month_customers, total_at_tenure)) * 100.0 / NULLIF(prev_month_customers, 0), 2) AS mom_volume_change_pct
FROM tenure_metrics
ORDER BY tenure_months ASC;

-- 2. Six-Month Cohort Retention Matrix
CREATE OR REPLACE VIEW analytics.v_cohort_retention_matrix AS
WITH binned_cohorts AS (
    SELECT
        customer_id,
        CASE
            WHEN tenure_months BETWEEN 0 AND 6 THEN '0-6m'
            WHEN tenure_months BETWEEN 7 AND 12 THEN '7-12m'
            WHEN tenure_months BETWEEN 13 AND 24 THEN '13-24m'
            WHEN tenure_months BETWEEN 25 AND 36 THEN '25-36m'
            WHEN tenure_months BETWEEN 37 AND 48 THEN '37-48m'
            WHEN tenure_months BETWEEN 49 AND 60 THEN '49-60m'
            ELSE '61-72m'
        END AS cohort_window,
        CASE
            WHEN tenure_months BETWEEN 0 AND 6 THEN 1
            WHEN tenure_months BETWEEN 7 AND 12 THEN 2
            WHEN tenure_months BETWEEN 13 AND 24 THEN 3
            WHEN tenure_months BETWEEN 25 AND 36 THEN 4
            WHEN tenure_months BETWEEN 37 AND 48 THEN 5
            WHEN tenure_months BETWEEN 49 AND 60 THEN 6
            ELSE 7
        END AS cohort_sort_order,
        contract_type,
        churn_label,
        monthly_charges
    FROM staging.customers
)
SELECT
    cohort_window,
    cohort_sort_order,
    contract_type,
    COUNT(*) AS total_customers,
    SUM(churn_label) AS churned_count,
    COUNT(*) - SUM(churn_label) AS retained_count,
    ROUND((COUNT(*) - SUM(churn_label)) * 100.0 / COUNT(*), 2) AS retention_rate_pct,
    ROUND(SUM(churn_label) * 100.0 / COUNT(*), 2) AS churn_rate_pct,
    ROUND(SUM(monthly_charges), 2) AS monthly_revenue_exposure
FROM binned_cohorts
GROUP BY cohort_window, cohort_sort_order, contract_type
ORDER BY cohort_sort_order ASC, contract_type ASC;
