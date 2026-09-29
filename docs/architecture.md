# Project Architecture & System Design

## 1. Overview
The **Customer Retention & Churn Intelligence Platform** bridges modern analytics engineering, leakage-safe machine learning, explainable AI (SHAP), and business decision support.

The system processes raw subscription and customer transaction records, enforces quality assertions through an analytical DuckDB SQL layer, computes cohort dynamics and statistical tests, trains calibrated classification models, explains predictive attributions via SHAP, and translates predictions into an expected Revenue-at-Risk matrix and Power BI executive dashboards.

---

## 2. End-to-End Data Pipeline Architecture

```mermaid
flowchart TD

subgraph S1 [Data Ingestion & SQL Layer]
    A[Raw Telco CSV Ingestion] --> B[Data Quality & Whitespace Profiling]
    B --> C[(DuckDB Local Analytical Engine)]
    C --> D[raw.customers Schema]
    D --> E[staging.customers Typed Table]
    E --> F[analytics Views: Contract, Tenure, Spend]
end

subgraph S2 [Statistical & Cohort Analysis]
    E --> G[Tenure Lifecycle Hazard Curves]
    E --> H[Contract Cohort Retention Matrix]
    E --> I[Hypothesis Testing: Mann-Whitney U & Chi-Square]
    I --> J[Benjamini-Hochberg FDR Correction]
end

subgraph S3 [Leakage-Safe Machine Learning]
    E --> K[Domain Feature Engineering]
    K --> L[Stratified 80/20 Train-Test Split]
    L --> M[ColumnTransformer Preprocessing Pipeline]
    M --> N[Baseline: Logistic Regression]
    M --> O[Advanced: XGBoost Classifier]
    N --> P[Evaluation: PR-AUC, ROC-AUC, Brier Score]
    O --> P
    P --> Q[Business Cost Matrix Threshold Tuning]
end

subgraph S4 [Explainability & Business Prioritization]
    O --> R[SHAP TreeExplainer Global & Local Attribution]
    Q --> S[Customer Risk Scoring & Probabilities]
    S --> T[Expected Revenue-at-Risk Quantification]
    T --> U[2x2 Retention Prioritization Matrix]
    U --> V[Actionable Playbook Recommendations]
end

subgraph S5 [BI & Decision Delivery]
    U --> W[Power BI 5-Page Executive Dashboard]
    U --> X[Interactive Streamlit Customer 360 App]
end
```

---

## 3. Component Breakdown

| Layer | Technology | Primary Function | Outputs |
| :--- | :--- | :--- | :--- |
| **Ingestion** | Python (`urllib`, `pandas`) | Automated fetch from canonical source with checksum and schema verification | `data/raw/Telco-Customer-Churn.csv` |
| **Database** | DuckDB (In-Process SQL OLAP) | Strict typing, TotalCharges normalization, analytical cohort aggregations, quality assertions | `data/processed/customer_retention.duckdb` |
| **Data Quality & Stats** | `scipy.stats`, `statsmodels` | Null checks, outlier detection, Mann-Whitney U, Chi-Square, Benjamini-Hochberg FDR | `outputs/reports/data_quality_report.json`, `outputs/reports/statistical_tests.json` |
| **Feature Engineering** | `scikit-learn`, `numpy` | Leakage-safe domain feature creation (add-ons, billing stability ratio, vulnerability interactions) | Preprocessor transformer, clean training splits |
| **Modeling** | `sklearn`, `xgboost`, `joblib` | Logistic Regression baseline vs XGBoost, PR-AUC optimization, cost-matrix threshold tuning | `models/churn_model.joblib`, `models/model_metadata.json` |
| **Explainability** | `shap` | TreeExplainer global feature importance and individual customer waterfall explanations | `outputs/shap/global_shap_importance.json`, `outputs/charts/shap_summary_plot.png` |
| **Decision Science** | Python | Expected Revenue-at-Risk ($P(churn) \times Revenue$), 2x2 priority matrix, automated action playbooks | `outputs/predictions/customer_risk_scores.csv` |
| **Business Intelligence** | Power BI | 5-page enterprise dashboard (Executive KPIs, Cohorts, Risk Register, Drivers, Prioritization) | `outputs/powerbi/powerbi_customer_retention_dataset.csv`, DAX catalogs |
| **Interactive App** | Streamlit | Fast customer 360 lookup, real-time SHAP force plots, simulation sliders | `app/app.py` |

---

## 4. Key Design Decisions

1. **DuckDB as Local Analytical Engine:**
   - Provides serverless, fast columnar execution for complex window functions (`PERCENT_RANK`, `NTILE`, rolling sums) without requiring the user or CI to configure an external PostgreSQL server.
   - Code is written in standard ANSI SQL compatible with PostgreSQL or Snowflake.
2. **Leakage-Safe Preprocessor Separation:**
   - Scalers and encoders are strictly fitted on the 80% training set (`X_train`) and only transform `X_test` and production records.
   - No target information or post-event behavioral metrics are used.
3. **Probabilistic Decision Science:**
   - Binary predictions are decoupled from the arbitrary 0.50 threshold. The system defaults to an optimized 0.30 decision threshold selected to maximize F1 and minimize business intervention costs on the Precision-Recall curve.
