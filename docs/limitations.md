# Known Assumptions, Caveats & Limitations

To maintain uncompromising analytical integrity, this document explicitly details the boundaries and limitations of this project.

---

## 1. Dataset Limitations

1. **Cross-Sectional Static Nature:**
   - The source IBM Telco Customer Churn dataset is a static, cross-sectional snapshot containing historical churn status.
   - It does NOT contain multi-year timestamped event streams (e.g. daily session logs, usage metering, CRM ticket creation timestamps).
   - *Implication:* A true time-series forward prediction horizon (e.g. *"predict churn in next 30 days"*) cannot be validated with rolling window backtesting on this data. We treat the model as a point-in-time risk scoring engine and explicitly document this constraint.

2. **TotalCharges Blank String Anomaly:**
   - Exactly $11$ customer records contained blank strings `' '` in `TotalCharges`.
   - Inspection revealed all $11$ records correspond to `tenure = 0` (subscribers who joined in the current billing cycle and had not yet generated an end-of-month invoice).
   - *Implication:* Rather than discarding rows or fabricating data, we impute `TotalCharges = 0.0` in staging with documented rationale.

3. **Absence of Product Usage Telemetry:**
   - The dataset records whether a service is active (`OnlineSecurity = Yes`), but not how frequently the customer uses it (e.g. gigabytes streamed, login frequency, support tickets filed).
   - *Implication:* Advanced behavioral engagement features cannot be created without fabricating synthetic data. We strictly preserve empirical reality and avoid inventing unsupported CRM tables.

---

## 2. Statistical & Machine Learning Limitations

1. **Predictive Association vs Causal Inference:**
   - High SHAP values or low p-values prove *statistical association*, NOT *causal effect*.
   - Example: Month-to-month contracts are strongly associated with churn ($\text{Cramer's V} = 0.41$). This does NOT prove that forcing a customer into a 2-year contract will magically eliminate their desire to churn; it may simply cause them to refuse signing at renewal.
   - All SHAP attributions must be framed as predictive signals, not causal interventions.

2. **Expected Revenue at Risk is Not Guaranteed Loss:**
   - $\text{Expected Revenue-at-Risk} = \hat{p} \times \text{Charges}$ represents an actuarial expectation across a large cohort, not a guarantee that a specific customer's entire annual contract will vanish tomorrow.
