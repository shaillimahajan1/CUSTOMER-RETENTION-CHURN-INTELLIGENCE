-- 06_features.sql
-- Leakage-safe feature transformations in SQL layer

CREATE OR REPLACE VIEW analytics.v_churn_features AS
SELECT
    customer_id,
    gender,
    is_senior_citizen,
    has_partner,
    has_dependents,
    tenure_months,
    has_phone_service,
    multiple_lines,
    internet_service,
    online_security,
    online_backup,
    device_protection,
    tech_support,
    streaming_tv,
    streaming_movies,
    contract_type,
    has_paperless_billing,
    payment_method,
    monthly_charges,
    total_charges,
    addon_services_count,

    -- Engineered domain features
    CASE
        WHEN contract_type = 'Month-to-month' THEN 1 ELSE 0
    END AS is_month_to_month,

    CASE
        WHEN payment_method = 'Electronic check' THEN 1 ELSE 0
    END AS is_electronic_check,

    CASE
        WHEN internet_service = 'Fiber optic' THEN 1 ELSE 0
    END AS is_fiber_optic,

    -- Risk interaction: High Monthly Charges on Month-to-Month contract
    CASE
        WHEN contract_type = 'Month-to-month' AND monthly_charges > 70.0 THEN 1 ELSE 0
    END AS is_high_risk_contract_spend,

    -- Stickiness: Has both TechSupport and OnlineSecurity
    CASE
        WHEN online_security = 'Yes' AND tech_support = 'Yes' THEN 1 ELSE 0
    END AS has_security_and_support,

    -- Vulnerability: Fiber optic user with NO tech support
    CASE
        WHEN internet_service = 'Fiber optic' AND tech_support = 'No' THEN 1 ELSE 0
    END AS is_vulnerable_fiber_user,

    -- Ratio of TotalCharges to (tenure * monthly_charges)
    -- Value near 1 indicates steady billing, >1 indicates past higher billing, <1 indicates recent rate hike
    CASE
        WHEN tenure_months > 0 AND (tenure_months * monthly_charges) > 0
        THEN ROUND(total_charges / (tenure_months * monthly_charges), 4)
        ELSE 1.0
    END AS billing_stability_ratio,

    churn_label
FROM staging.customers;
