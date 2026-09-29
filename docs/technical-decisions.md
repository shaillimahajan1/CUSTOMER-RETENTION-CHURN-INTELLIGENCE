# Technical Decisions & Architectural Trade-offs

## 1. Local Analytical Engine: DuckDB vs PostgreSQL

* **Decision:** Selected **DuckDB** as the primary local analytical engine.
* **Context:** The prompt requests PostgreSQL or DuckDB for local reproducibility, preferring DuckDB if PostgreSQL introduces local setup friction.
* **Rationale:**
  1. DuckDB is an in-process, columnar OLAP database requiring zero background daemon installation, passwords, or port binding.
  2. Executes complex analytical SQL window functions (`PERCENT_RANK`, `NTILE`, `LAG`, `CUME_DIST`) with zero friction.
  3. Seamlessly integrates with Python (`conn.query_df()`) and can be queried directly from Power BI, dbt, or CLI.
  4. The SQL scripts are written in standard ANSI SQL and can be migrated directly to PostgreSQL or Snowflake.

---

## 2. Advanced Classifier Selection: XGBoost vs LightGBM / Random Forest

* **Decision:** Selected **XGBoost** as the primary advanced model compared against the Logistic Regression baseline.
* **Rationale:**
  1. XGBoost handles tabular interactions effectively with explicit depth constraints (`max_depth=4`) and split penalties (`gamma=0.2`).
  2. Works natively with `shap.TreeExplainer` without requiring slow kernel approximations.
  3. Provides stable probability calibration out-of-the-box (Brier score = $0.1341$).
  4. Random Forest was rejected because it produces stepped probability distributions with poorer calibration in low-density boundaries.

---

## 3. Threshold Selection: Business Cost Matrix vs Default 0.50

* **Decision:** Optimized decision threshold to $\tau = 0.30$ based on precision-recall economics rather than the default $\tau = 0.50$.
* **Rationale:**
  1. Default 0.50 cutoff assumes equal misclassification penalties ($C_{FP} = C_{FN}$).
  2. In subscription retention, missing a high-value churner ($FN$, losing $\$600\text{--}\$1,200$ in annual gross margin) is far more damaging than sending an automated promotional nudge to a customer who would have stayed anyway ($FP$, costing $\$10\text{--}\$20$ in outreach).
  3. At $\tau = 0.30$, Recall jumps from $52.9\%$ to **$77.27\%$** while maintaining Precision at **$50.62\%$** and reaching peak F1-score (**$0.6117$**).
