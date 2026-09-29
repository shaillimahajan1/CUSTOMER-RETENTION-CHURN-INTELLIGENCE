# Data Dictionary

This document details all columns present in the raw ingestion table (`raw.customers`), the cleaned staging layer (`staging.customers`), and the final analytical intelligence dataset (`analytics.customer_risk_scored`).

---

## 1. Raw Ingestion Layer (`raw.customers`)

| Column Name | Data Type | Description | Values / Range |
| :--- | :--- | :--- | :--- |
| `customerID` | VARCHAR | Unique alphanumeric customer identifier | Unique string (e.g. `7590-VHVEG`) |
| `gender` | VARCHAR | Customer biological gender | `Female`, `Male` |
| `SeniorCitizen` | VARCHAR / INT | Flag indicating if subscriber is $\ge 65$ years old | `0`, `1` |
| `Partner` | VARCHAR | Indicator if subscriber has a domestic partner | `Yes`, `No` |
| `Dependents` | VARCHAR | Indicator if subscriber has dependents / children | `Yes`, `No` |
| `tenure` | VARCHAR / INT | Number of elapsed months since account inception | `0` to `72` |
| `PhoneService` | VARCHAR | Indicator of active landline / mobile phone service | `Yes`, `No` |
| `MultipleLines` | VARCHAR | Indicator of multiple phone lines | `No phone service`, `No`, `Yes` |
| `InternetService` | VARCHAR | Technology tier for high-speed internet | `DSL`, `Fiber optic`, `No` |
| `OnlineSecurity` | VARCHAR | Add-on service: cybersecurity and firewall | `No internet service`, `No`, `Yes` |
| `OnlineBackup` | VARCHAR | Add-on service: automated cloud backup | `No internet service`, `No`, `Yes` |
| `DeviceProtection`| VARCHAR | Add-on service: hardware replacement warranty | `No internet service`, `No`, `Yes` |
| `TechSupport` | VARCHAR | Add-on service: priority 24/7 technical helpdesk | `No internet service`, `No`, `Yes` |
| `StreamingTV` | VARCHAR | Add-on service: digital streaming television | `No internet service`, `No`, `Yes` |
| `StreamingMovies`| VARCHAR | Add-on service: premium on-demand movies | `No internet service`, `No`, `Yes` |
| `Contract` | VARCHAR | Subscription commitment term | `Month-to-month`, `One year`, `Two year` |
| `PaperlessBilling`| VARCHAR | Digital paperless invoicing preference | `Yes`, `No` |
| `PaymentMethod` | VARCHAR | Customer payment channel | `Electronic check`, `Mailed check`, `Bank transfer (automatic)`, `Credit card (automatic)` |
| `MonthlyCharges` | VARCHAR / FLOAT| Recurring monthly fee billed | `18.25` to `118.75` |
| `TotalCharges` | VARCHAR | Cumulative historical charges billed (blanks for tenure=0) | Numeric string or `' '` |
| `Churn` | VARCHAR | Historical churn indicator | `Yes`, `No` |

---

## 2. Staging Layer (`staging.customers`)

Includes typed castings, TotalCharges normalization, and foundational groupings:
* `customer_id`: Trimmed uppercase primary key.
* `tenure_months`: Integer cast of `tenure`.
* `monthly_charges`: Float cast of `MonthlyCharges`.
* `total_charges`: Double cast of `TotalCharges` with blank string imputed to `0.0` for new subscribers (`tenure = 0`).
* `churn_label`: Integer `1` if Churn = 'Yes', else `0`.
* `tenure_cohort_group`: Categorical bin (`0-12 Months`, `13-24 Months`, `25-48 Months`, `49-72 Months`).
* `addon_services_count`: Integer count ($0$ to $6$) of active security, backup, protection, support, and streaming add-ons.
* `monthly_spend_tier`: Categorical spending bucket (`Low Value (<$40)`, `Medium Value ($40-$80)`, `High Value ($80+)`).

---

## 3. Scored Predictive & Retention Intelligence Layer (`outputs/predictions/customer_risk_scores.csv`)

| Column Name | Data Type | Description | Business Application |
| :--- | :--- | :--- | :--- |
| `customer_id` | STRING | Unique customer identifier | Account matching in CRM |
| `churn_probability` | FLOAT | Calibrated model churn probability ($0.0$ to $1.0$) | Granular risk quantification |
| `risk_segment` | STRING | Risk category (`Low Risk`, `Medium Risk`, `High Risk`, `Critical Risk`) | Broad strategic grouping |
| `predicted_churn_flag`| INT | Binary classification at optimal threshold ($0.30$) | Operational cutoff flag |
| `monthly_revenue_exposure`| FLOAT | Current recurring monthly bill ($\$) | Account financial value |
| `annual_revenue_exposure` | FLOAT | Annualized billing run-rate ($\$) | Strategic LTV proxy |
| `monthly_revenue_at_risk` | FLOAT | $\text{churn\_probability} \times \text{monthly\_revenue\_exposure}$ | Expected monthly financial risk |
| `annual_revenue_at_risk` | FLOAT | $\text{churn\_probability} \times \text{annual\_revenue\_exposure}$ | Expected annual financial risk |
| `customer_value_tier` | STRING | `High Value` (top 25% of spend, $\ge \$89.85$) or `Standard Value` | Prioritization segmentation |
| `retention_priority_tier` | STRING | 2x2 matrix allocation (`Tier 1: VIP Urgent Outreach`, `Tier 2: Automated Campaign Offer`, `Tier 3: Proactive Account Care`, `Tier 4: Standard Operation / Monitor`) | Workforce resource allocation |
| `top_risk_driver` | STRING | Top observable characteristic driving elevated probability | Retention rep conversation context |
| `recommended_action` | STRING | Specific operational playbook step | Tactical intervention guide |
