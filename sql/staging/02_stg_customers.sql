-- 02_stg_customers.sql
-- Clean, typed, validated staging table for customer records

CREATE OR REPLACE TABLE staging.customers AS
SELECT
    TRIM(customerID) AS customer_id,
    TRIM(gender) AS gender,
    CAST(SeniorCitizen AS INTEGER) AS is_senior_citizen,
    CASE WHEN TRIM(Partner) = 'Yes' THEN 1 ELSE 0 END AS has_partner,
    CASE WHEN TRIM(Dependents) = 'Yes' THEN 1 ELSE 0 END AS has_dependents,
    CAST(tenure AS INTEGER) AS tenure_months,
    CASE WHEN TRIM(PhoneService) = 'Yes' THEN 1 ELSE 0 END AS has_phone_service,
    TRIM(MultipleLines) AS multiple_lines,
    TRIM(InternetService) AS internet_service,
    TRIM(OnlineSecurity) AS online_security,
    TRIM(OnlineBackup) AS online_backup,
    TRIM(DeviceProtection) AS device_protection,
    TRIM(TechSupport) AS tech_support,
    TRIM(StreamingTV) AS streaming_tv,
    TRIM(StreamingMovies) AS streaming_movies,
    TRIM(Contract) AS contract_type,
    CASE WHEN TRIM(PaperlessBilling) = 'Yes' THEN 1 ELSE 0 END AS has_paperless_billing,
    TRIM(PaymentMethod) AS payment_method,
    CAST(MonthlyCharges AS DOUBLE) AS monthly_charges,
    -- Handle blank TotalCharges for tenure=0 new subscribers
    COALESCE(TRY_CAST(NULLIF(TRIM(TotalCharges), '') AS DOUBLE), 0.0) AS total_charges,
    CASE WHEN TRIM(Churn) = 'Yes' THEN 1 ELSE 0 END AS churn_label,
    TRIM(Churn) AS churn_str,

    -- Feature helpers & groupings
    CASE
        WHEN CAST(tenure AS INTEGER) <= 12 THEN '0-12 Months'
        WHEN CAST(tenure AS INTEGER) <= 24 THEN '13-24 Months'
        WHEN CAST(tenure AS INTEGER) <= 48 THEN '25-48 Months'
        ELSE '49-72 Months'
    END AS tenure_cohort_group,

    (
        CASE WHEN TRIM(OnlineSecurity) = 'Yes' THEN 1 ELSE 0 END +
        CASE WHEN TRIM(OnlineBackup) = 'Yes' THEN 1 ELSE 0 END +
        CASE WHEN TRIM(DeviceProtection) = 'Yes' THEN 1 ELSE 0 END +
        CASE WHEN TRIM(TechSupport) = 'Yes' THEN 1 ELSE 0 END +
        CASE WHEN TRIM(StreamingTV) = 'Yes' THEN 1 ELSE 0 END +
        CASE WHEN TRIM(StreamingMovies) = 'Yes' THEN 1 ELSE 0 END
    ) AS addon_services_count,

    CASE
        WHEN CAST(MonthlyCharges AS DOUBLE) >= 80.0 THEN 'High Value ($80+)'
        WHEN CAST(MonthlyCharges AS DOUBLE) >= 40.0 THEN 'Medium Value ($40-$80)'
        ELSE 'Low Value (<$40)'
    END AS monthly_spend_tier

FROM raw.customers;
