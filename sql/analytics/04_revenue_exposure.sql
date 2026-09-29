-- 04_revenue_exposure.sql
-- Revenue Exposure, Value Quartiles, and Cumulative Revenue Analytics

CREATE OR REPLACE VIEW analytics.v_revenue_exposure_by_segment AS
WITH customer_ranks AS (
    SELECT
        customer_id,
        contract_type,
        internet_service,
        tenure_months,
        monthly_charges,
        total_charges,
        churn_label,
        NTILE(4) OVER (ORDER BY monthly_charges DESC) AS revenue_quartile,
        PERCENT_RANK() OVER (ORDER BY monthly_charges) AS revenue_percentile,
        SUM(monthly_charges) OVER (ORDER BY monthly_charges DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_monthly_revenue,
        SUM(monthly_charges) OVER () AS total_monthly_revenue
    FROM staging.customers
)
SELECT
    CASE revenue_quartile
        WHEN 1 THEN 'Q1 - Top 25% (High Value)'
        WHEN 2 THEN 'Q2 - Upper Mid 25%'
        WHEN 3 THEN 'Q3 - Lower Mid 25%'
        ELSE 'Q4 - Bottom 25% (Low Value)'
    END AS value_tier,
    COUNT(*) AS total_customers,
    SUM(churn_label) AS churned_customers,
    ROUND(AVG(churn_label) * 100.0, 2) AS churn_rate_pct,
    ROUND(SUM(monthly_charges), 2) AS tier_monthly_revenue,
    ROUND(SUM(CASE WHEN churn_label = 1 THEN monthly_charges ELSE 0 END), 2) AS churned_monthly_revenue,
    ROUND(SUM(monthly_charges) * 100.0 / MAX(total_monthly_revenue), 2) AS pct_of_total_revenue,
    ROUND(AVG(monthly_charges), 2) AS avg_monthly_charges
FROM customer_ranks
GROUP BY revenue_quartile
ORDER BY revenue_quartile ASC;

-- High Value Vulnerability Matrix
CREATE OR REPLACE VIEW analytics.v_high_value_contract_vulnerability AS
SELECT
    contract_type,
    monthly_spend_tier,
    COUNT(*) AS customer_count,
    SUM(churn_label) AS churned_count,
    ROUND(AVG(churn_label) * 100.0, 2) AS churn_rate_pct,
    ROUND(SUM(monthly_charges), 2) AS total_revenue_exposure,
    ROUND(SUM(CASE WHEN churn_label = 1 THEN monthly_charges ELSE 0 END), 2) AS realized_churn_revenue_loss
FROM staging.customers
GROUP BY contract_type, monthly_spend_tier
ORDER BY total_revenue_exposure DESC;
