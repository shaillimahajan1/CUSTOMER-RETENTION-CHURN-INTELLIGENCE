# Model Governance & Responsible AI

## 1. Model Card & Purpose

* **Model Name:** Customer Churn Probability Classifier (XGBoost)
* **Model Version:** `v1.0.0`
* **Intended Purpose:** Predict individual customer churn risk probabilities to enable proactive retention outreach and quantify expected revenue exposure.
* **Intended Users:** Customer Success Managers, Retention Specialists, Marketing Automation Systems, Financial Planning & Analysis (FP&A).
* **Out-of-Scope / Prohibited Uses:**
  - Automated service termination or punitive pricing based on predicted risk.
  - Making credit or underwriting eligibility decisions.
  - Using predictions to deny mandatory warranty or statutory customer support.

---

## 2. Demographic & Fairness Considerations

* **Protected Attributes in Dataset:** `gender` (Female/Male), `SeniorCitizen` (0/1), `Partner`, `Dependents`.
* **Statistical Independence Audit:**
  - `gender`: Chi-square test statistic = $0.48$, p-value = $0.4865$ (Fail to reject $H_0$; no statistically significant association with churn).
  - `SeniorCitizen`: Chi-square test statistic = $158.46$, p-value $< 10^{-35}$. Senior citizens exhibit higher churn ($41.7\%$ vs $23.6\%$), primarily driven by higher adoption of unbundled fiber internet and lower adoption of auto-pay.
* **Ethical Guardrail:** The model must NOT be used to systematically deprioritize older demographics for support or digital services.

---

## 3. Retraining Schedule & Lifecycle Management

* **Cadence:** Retrain quarterly or whenever significant macroeconomic/pricing changes occur.
* **Drift Triggers for Emergency Retraining:**
  1. **Concept Drift:** Historical churn rate shifts by $> 3.0\%$ quarter-over-quarter.
  2. **Data Drift:** Population Stability Index (PSI) $> 0.25$ on key continuous features (`monthly_charges`, `tenure`).
  3. **Prediction Drift:** Kolmogorov-Smirnov test statistic on predicted probability distributions reveals significant shift ($p < 0.01$).
  4. **Performance Degradation:** PR-AUC on rolling 30-day verified outcomes falls below $0.58$.
