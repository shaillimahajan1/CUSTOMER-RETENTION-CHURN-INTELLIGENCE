# Modeling Methodology & Validation Strategy

## 1. Baseline Benchmark: Logistic Regression

Rather than leaping directly to gradient boosting, we establish a robust benchmark using **Logistic Regression** ($L_2$ regularization, $C=0.1$, L-BFGS solver).
* **Why Logistic Regression?**
  1. Provides an interpretable linear log-odds benchmark.
  2. Naturally outputs well-calibrated posterior probabilities.
  3. Establishes the performance floor that complex tree models must beat to justify operational overhead.
* **Baseline Test Results:**
  - ROC-AUC: **0.8477**
  - PR-AUC: **0.6652**
  - Brier Score: **0.1345**

---

## 2. Advanced Classifier: XGBoost

We deploy an **XGBoost (eXtreme Gradient Boosting)** tree ensemble configured to avoid overfitting on tabular subscription data:
* `n_estimators`: 180
* `max_depth`: 4 (shallow trees to prevent memorization of high-cardinality interactions)
* `learning_rate`: 0.05
* `subsample`: 0.85
* `colsample_bytree`: 0.80
* `min_child_weight`: 3
* `gamma`: 0.2 (regularization split penalty)

### Advanced Model Test Results:
* ROC-AUC: **0.8460**
* PR-AUC: **0.6565**
* Brier Score: **0.1341**
* Calibration: High fidelity across probability deciles without requiring external isotonic scaling.

---

## 3. Train / Validation / Test Strategy

* **Split Ratio:** $80\%$ Training ($5,634$ accounts), $20\%$ Held-Out Test ($1,409$ accounts).
* **Stratification:** Stratified by the target label (`Churn`) to ensure identical base rates ($26.54\%$) across splits.
* **Cross-Validation:** 5-Fold Stratified Cross-Validation on the training partition used during hyperparameter exploration. The test partition was touched exactly once during final evaluation.

---

## 4. Class Imbalance & Threshold Optimization

* **Class Distribution:** Approximately $73.5\%$ Non-Churn vs $26.5\%$ Churn ($2.77:1$ negative-to-positive ratio).
* **SMOTE Evaluation:** Synthetic Minority Over-sampling Technique (SMOTE) was deliberately evaluated and rejected. In customer subscription churn, SMOTE generates synthetic customer vectors in low-density feature space that distort true probability calibration. Instead, empirical decision threshold optimization is employed.
* **Threshold Sweep:**
  - Standard $\tau = 0.50$: Precision = $65.8\%$, Recall = $52.9\%$, F1 = $0.587$. Misses nearly half of all churners.
  - Optimal $\tau = 0.30$: Precision = **$50.62\%$**, Recall = **$77.27\%$**, F1 = **$0.6117$**.
  - **Business Impact:** Captures an additional $91$ churned customers in the test cohort ($364$ annualized across full base) while maintaining an outreach precision over $50\%$.
