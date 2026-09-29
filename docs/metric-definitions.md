# Metric Definitions & Business KPIs

## 1. Statistical & Machine Learning Metrics

### Receiver Operating Characteristic Area Under the Curve (ROC-AUC)
$$\text{ROC-AUC} = \int_{0}^{1} \text{TPR}(\text{FPR}^{-1}(t)) \, dt$$
* **Definition:** Probability that a randomly chosen churned customer is assigned a higher predicted churn probability than a randomly chosen retained customer.
* **Our Model:** Baseline Logistic Regression = **0.8477** | Advanced XGBoost = **0.8460**.
* **Business Limitation:** In imbalanced datasets ($\approx 26.5\%$ churn), ROC-AUC can present an overly optimistic assessment because the True Negative count dominates the False Positive Rate denominator.

### Precision-Recall Area Under the Curve (PR-AUC / Average Precision)
$$\text{PR-AUC} = \sum_{n} (R_n - R_{n-1}) P_n$$
* **Definition:** Evaluates the trade-off between Precision and Recall exclusively over the positive (churn) class.
* **Our Model:** Baseline Logistic Regression = **0.6652** | Advanced XGBoost = **0.6565**.
* **Business Rationale:** Crucial for retention teams. Because outreach resources are scarce, PR-AUC evaluates how well the model identifies true churners without generating excessive false alarm outreach.

### Precision
$$\text{Precision} = \frac{\text{True Positives}}{\text{True Positives} + \text{False Positives}}$$
* **Definition:** Fraction of contacted customers who would have actually churned.
* **Business Cost of Low Precision:** Retention teams waste call time and hand out unnecessary discounts to customers who were happy to stay anyway.

### Recall (Sensitivity)
$$\text{Recall} = \frac{\text{True Positives}}{\text{True Positives} + \text{False Negatives}}$$
* **Definition:** Fraction of all actual churners successfully identified by the model.
* **Business Cost of Low Recall:** Churners slip through unnoticed and permanently cancel their service.

### Brier Score (Calibration Metric)
$$\text{Brier Score} = \frac{1}{N} \sum_{i=1}^{N} (f_i - o_i)^2$$
* **Definition:** Mean squared error between predicted probabilities $f_i$ and true binary outcomes $o_i \in \{0, 1\}$.
* **Our Model:** XGBoost = **0.1341** (close to 0 represents well-calibrated probabilities).

---

## 2. Business & Financial KPIs

### Historical Churn Rate
$$\text{Churn Rate} = \frac{\text{Churned Customers}}{\text{Total Customer Base}} \times 100$$
* **Dataset Value:** $26.54\%$ ($1,869$ of $7,043$).

### Expected Monthly Revenue-at-Risk
$$\text{Monthly Expected Revenue-at-Risk} = \sum_{i=1}^{N} \hat{p}_i \times \text{MonthlyCharges}_i$$
* **Dataset Value:** **$140,036.26** per month.
* **Interpretation:** The expected monthly value exposed to churn across the customer portfolio under current risk estimates.

### Annualized Expected Revenue-at-Risk
$$\text{Annualized Expected Revenue-at-Risk} = \text{Monthly Expected Revenue-at-Risk} \times 12$$
* **Dataset Value:** **$1,680,431.97** per year.

### Decision Threshold ($\tau$)
* **Default Benchmark:** $\tau = 0.50$ (yields Recall = $52.9\%$, Precision = $65.8\%$).
* **Optimized Operational Threshold:** $\tau = 0.30$ (yields Recall = **$77.27\%$**, Precision = **$50.62\%$**, F1 = **$0.6117$**).
* **Optimization Rationale:** Setting $\tau = 0.30$ captures an additional $24.4\%$ of all churners while controlling campaign outreach costs.
