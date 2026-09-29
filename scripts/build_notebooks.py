"""Programmatic builder for notebooks 01 to 05, ensuring valid nbformat v4 structure."""

from pathlib import Path
import nbformat as nbf


def make_notebook_01():
    nb = nbf.v4.new_notebook()
    nb.cells = [
        nbf.v4.new_markdown_cell("""# 01 - Data Quality Profiling & Hygiene Audit
**Customer Retention & Churn Intelligence Platform**

This notebook performs:
1. Raw schema validation and column completeness
2. Missing values and blank string whitespace audit (notably `TotalCharges`)
3. Target class distribution and imbalance ratio
4. Numerical outlier analysis (IQR method) and categorical cardinalities
"""),
        nbf.v4.new_code_cell("""import json
import pandas as pd
import numpy as np
from src.data.loader import load_raw_data
from src.validation.profiler import DataProfiler

# 1. Load Raw Dataset
df_raw = load_raw_data("data/raw/Telco-Customer-Churn.csv")
print(f"Loaded {df_raw.shape[0]:,} rows x {df_raw.shape[1]} columns")
df_raw.head()
"""),
        nbf.v4.new_code_cell("""# 2. Execute Data Profiler
profiler = DataProfiler(target_col="Churn", positive_val="Yes")
report = profiler.generate_quality_report(df_raw)

print("--- DATASET OVERVIEW ---")
print(json.dumps(report["dataset_overview"], indent=2))

print("\\n--- TARGET DISTRIBUTION ---")
print(json.dumps(report["target_distribution"], indent=2))

print("\\n--- WHITESPACE ANOMALIES (TotalCharges) ---")
print(json.dumps(report["missing_values"]["whitespace_anomalies"], indent=2))
"""),
        nbf.v4.new_markdown_cell("""### Finding & Treatment: TotalCharges Blanks
There are exactly 11 customer records with blank spaces `' '` in `TotalCharges`. All 11 records have `tenure = 0` (brand new subscribers). 
In our SQL staging pipeline (`sql/staging/02_stg_customers.sql`), we convert these to `0.0` with explicit documentation rather than dropping them.
""")
    ]
    return nb


def make_notebook_02():
    nb = nbf.v4.new_notebook()
    nb.cells = [
        nbf.v4.new_markdown_cell("""# 02 - Customer Analytics & Statistical Hypothesis Testing
**Customer Retention & Churn Intelligence Platform**

This notebook queries the analytical DuckDB layer and evaluates statistical significance:
1. SQL aggregations across contract, internet service, payment method, and tenure
2. Mann-Whitney U tests for numerical variables
3. Chi-Square tests of independence and Cramer's V for categorical features
4. Benjamini-Hochberg (FDR) multiple testing corrections
"""),
        nbf.v4.new_code_cell("""import pandas as pd
from src.data.db import DuckDBManager
from src.validation.profiler import DataProfiler

# Connect to DuckDB
with DuckDBManager("data/processed/customer_retention.duckdb") as db:
    df_contract = db.query_df("SELECT * FROM analytics.v_churn_by_contract")
    df_internet = db.query_df("SELECT * FROM analytics.v_churn_by_internet")
    df_payment = db.query_df("SELECT * FROM analytics.v_churn_by_payment")
    df_staged = db.query_df("SELECT * FROM staging.customers")

print("--- CHURN BY CONTRACT TYPE ---")
print(df_contract)

print("\\n--- CHURN BY PAYMENT METHOD ---")
print(df_payment)
"""),
        nbf.v4.new_code_cell("""# Run Statistical Hypothesis Tests
profiler = DataProfiler(target_col="Churn", positive_val="Yes")
stat_tests = profiler.run_statistical_hypothesis_tests(df_staged)
df_stats = pd.DataFrame(stat_tests)
df_stats[["feature", "test_type", "test_statistic", "raw_p_value", "p_value_bh_adjusted", "effect_size", "business_importance"]].head(10)
""")
    ]
    return nb


def make_notebook_03():
    nb = nbf.v4.new_notebook()
    nb.cells = [
        nbf.v4.new_markdown_cell("""# 03 - Cohort Retention & Lifecycle Dynamics
**Customer Retention & Churn Intelligence Platform**

Examines the relationship between customer tenure and retention:
1. 72-month tenure lifecycle hazard curve
2. Contract cohort retention matrix
3. Service add-on bundle stickiness
"""),
        nbf.v4.new_code_cell("""import pandas as pd
import matplotlib.pyplot as plt
from src.data.db import DuckDBManager

with DuckDBManager("data/processed/customer_retention.duckdb") as db:
    df_lifecycle = db.query_df("SELECT * FROM analytics.v_tenure_lifecycle_curve")
    df_cohort_matrix = db.query_df("SELECT * FROM analytics.v_cohort_retention_matrix")

print("--- COHORT RETENTION MATRIX (FIRST 10 ROWS) ---")
print(df_cohort_matrix.head(10))

# Plot Tenure Lifecycle Curve
plt.figure(figsize=(10, 5))
plt.plot(df_lifecycle["tenure_months"], df_lifecycle["tenure_specific_churn_rate"], color="#d62728", lw=2)
plt.title("Tenure-Specific Churn Rate (Months 0 to 72)")
plt.xlabel("Tenure (Months)")
plt.ylabel("Observed Churn Rate (%)")
plt.grid(alpha=0.3)
plt.show()
""")
    ]
    return nb


def make_notebook_04():
    nb = nbf.v4.new_notebook()
    nb.cells = [
        nbf.v4.new_markdown_cell("""# 04 - Leakage-Safe Churn Modeling & Threshold Optimization
**Customer Retention & Churn Intelligence Platform**

This notebook develops, compares, and evaluates predictive churn models:
1. Logistic Regression benchmark vs XGBoost Classifier
2. Precision-Recall AUC (PR-AUC) and ROC-AUC evaluation on held-out test data
3. Probability calibration curve & Brier score analysis
4. Empirical threshold optimization based on business cost matrix
"""),
        nbf.v4.new_code_cell("""import json
import pandas as pd
import matplotlib.pyplot as plt
from src.utils.helpers import load_json

metadata = load_json("models/model_metadata.json")
metrics = metadata["metrics"]

print("--- BASELINE VS ADVANCED MODEL METRICS ---")
lr = metrics["Logistic_Regression_Baseline"]
xgb_def = metrics["XGBoost_Advanced"]
xgb_opt = metrics["XGBoost_Optimal_Threshold"]

summary = pd.DataFrame([
    {"Model": "Logistic Regression Baseline", **lr},
    {"Model": "XGBoost (Default 0.50 Threshold)", **xgb_def},
    {"Model": "XGBoost (Optimized 0.30 Threshold)", **xgb_opt}
])
summary[["Model", "threshold", "roc_auc", "pr_auc", "precision", "recall", "f1", "brier_score"]]
""")
    ]
    return nb


def make_notebook_05():
    nb = nbf.v4.new_notebook()
    nb.cells = [
        nbf.v4.new_markdown_cell("""# 05 - Explainable AI (SHAP), Revenue-at-Risk & Retention Prioritization
**Customer Retention & Churn Intelligence Platform**

Translates model outputs into actionable business intelligence:
1. Global SHAP feature importance
2. Individual customer risk driver attribution
3. Expected Revenue-at-Risk ($Churn Probability \times Monthly Revenue Exposure$)
4. 2x2 Retention Prioritization Matrix & Action Playbook
"""),
        nbf.v4.new_code_cell("""import pandas as pd
import matplotlib.pyplot as plt
from src.utils.helpers import load_json

# Load Scored Customer Population
df_scored = pd.read_csv("outputs/predictions/customer_risk_scores.csv")
print(f"Loaded {len(df_scored):,} scored customer accounts.")

# Retention Priority Summary
tier_summary = df_scored.groupby("retention_priority_tier").agg(
    Customer_Count=("customer_id", "count"),
    Monthly_Rev_at_Risk=("monthly_revenue_at_risk", "sum"),
    Annual_Rev_at_Risk=("annual_revenue_at_risk", "sum"),
    Avg_Churn_Probability=("churn_probability", "mean")
).reset_index()

tier_summary
""")
    ]
    return nb


def build_all_notebooks():
    out_dir = Path("notebooks")
    out_dir.mkdir(parents=True, exist_ok=True)

    notebooks = {
        "01_data_quality.ipynb": make_notebook_01(),
        "02_customer_analytics.ipynb": make_notebook_02(),
        "03_cohort_retention.ipynb": make_notebook_03(),
        "04_model_development.ipynb": make_notebook_04(),
        "05_model_explainability.ipynb": make_notebook_05(),
    }

    for name, nb in notebooks.items():
        dest = out_dir / name
        with open(dest, "w", encoding="utf-8") as f:
            nbf.write(nb, f)
        print(f"Created notebook: {dest.name}")


if __name__ == "__main__":
    build_all_notebooks()
