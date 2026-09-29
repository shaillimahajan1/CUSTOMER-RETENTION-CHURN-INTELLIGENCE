# Feature Engineering & Leakage Prevention

## 1. Feature Engineering Principles

Every feature included in this platform satisfies six criteria:
1. **Explicit Business Meaning:** Maps directly to customer behavior, contract elasticity, or financial exposure.
2. **Point-in-Time Availability:** All inputs must be known and recorded in billing or CRM *before* the prediction timestamp.
3. **No Target Leakage:** No target-derived statistics (e.g. out-of-fold target encoding without strict out-of-sample discipline) are utilized.
4. **No Post-Churn Data:** Variables that are only updated when an account closes (e.g. exit surveys, cancellation reason codes) are strictly excluded.
5. **Leakage-Safe Preprocessing:** All scaling, imputations, and one-hot encoders are fitted exclusively on the training fold (`X_train`) and applied downstream to validation/test sets.

---

## 2. Engineered Domain Features

| Feature Name | Calculation / Formula | Business Rationale | Leakage Audit |
| :--- | :--- | :--- | :--- |
| `addon_services_count` | $\sum (\text{Security, Backup, DeviceProtection, TechSupport, TV, Movies})$ | Measures service breadth and switching friction (stickiness). | Safe: Active service catalog at scoring date. |
| `billing_stability_ratio`| $\frac{\text{TotalCharges}}{(\text{tenure} + 1) \times \text{MonthlyCharges}}$ | Evaluates whether recent charges surged relative to historical run-rate. Ratio $< 1.0$ flags recent price increases. | Safe: Computed solely from historical ledger entries. |
| `is_month_to_month` | $1 \text{ if Contract} = \text{'Month-to-month'} \text{ else } 0$ | Captures zero contractual exit barrier. | Safe: Active contract field. |
| `is_high_risk_contract_spend` | $1 \text{ if (Month-to-month and MonthlyCharges} > \$70) \text{ else } 0$ | High monthly expenditure without commitment represents peak customer price sensitivity. | Safe: Billing parameters. |
| `has_security_and_support` | $1 \text{ if (OnlineSecurity and TechSupport} = \text{'Yes'}) \text{ else } 0$ | High-utility protective bundle known to dramatically increase account stickiness. | Safe: Active subscription items. |
| `is_vulnerable_fiber_user` | $1 \text{ if (Fiber optic and TechSupport} = \text{'No'}) \text{ else } 0$ | Fiber users experiencing technical issues without dedicated support exhibit the highest churn hazard. | Safe: Active subscription items. |

---

## 3. Data Leakage Checklist & Safeguards

```text
[✓] Prediction Cutoff Defined: Cross-sectional customer snapshot date.
[✓] Excluded Post-Churn Attributes: Cancellation dates, exit surveys, refund claims post-termination.
[✓] Train/Test Independence: ColumnTransformer fit() called strictly on X_train.
[✓] OneHotEncoder Configuration: handle_unknown='ignore' to prevent test-set data bleeding.
[✓] Target Separation: Churn column stripped from X prior to preprocessor execution.
```
