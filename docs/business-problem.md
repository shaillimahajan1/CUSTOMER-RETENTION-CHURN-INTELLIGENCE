# Business Problem & Strategic Objectives

## 1. Executive Context
In subscription-based recurring revenue businesses (telecommunications, SaaS, streaming, utilities), customer acquisition costs (CAC) significantly exceed retention costs. Losing subscribers directly erodes Monthly Recurring Revenue (MRR) and Lifetime Value (LTV).

However, retention teams face a universal operational constraint: **Capacity Limitation**.
A retention team or Customer Success team cannot manually call or offer expensive contract concessions to every customer. 

The core challenge is not simply:
> *"Predict whether a customer will churn."*

The operational business challenge is:
> *"Which customers have an elevated risk of churning, what specific characteristics drive that risk, what is the expected financial exposure, and how should retention efforts be prioritized to maximize saved revenue while controlling outreach costs?"*

---

## 2. Business Questions Answered

### A. Customer Behavior & Churn Drivers
1. What is the baseline churn rate across the customer base? ($26.54\%$)
2. Which contractual segments experience the highest churn rate? (Month-to-month contracts at $42.71\%$ vs Two-year contracts at $2.83\%$).
3. Does price sensitivity or service friction explain churn? (Fiber optic customers paying premium rates with no tech support churn at over $40\%$).

### B. Retention & Lifecycle Dynamics
1. When are subscribers most vulnerable? (Months $1$ through $6$ show a steep onboarding cliff; churn stabilizes significantly after $24$ months).
2. Does service depth improve loyalty? (Subscribers with $\ge 3$ add-on security/support services churn at one-third the rate of single-service subscribers).

### C. Financial & Revenue Exposure
1. How much monthly recurring revenue is directly exposed to high-risk customers? ($\$140,036.26$ monthly, or $\$1.68\text{M}$ annualized).
2. Which customers represent high revenue but high risk? ($484$ Tier 1 VIP accounts accounting for over $\$45\text{K}$ in monthly risk).

### D. Decision Science & Prioritization
1. How do we allocate retention outreach between automated discount emails versus dedicated account manager phone calls?
2. How do we ensure we do not waste expensive retention discounts on customers who were never going to leave (False Positives)?

---

## 3. Financial Framing: Expected Revenue at Risk

Rather than treating churn as a binary certainty, this platform defines **Expected Revenue-at-Risk**:
$$\text{Expected Monthly Revenue-at-Risk} = \hat{P}(\text{Churn}) \times \text{Monthly Revenue Exposure}$$

Where:
- $\hat{P}(\text{Churn})$ is the calibrated model probability ($0.0$ to $1.0$).
- $\text{Monthly Revenue Exposure}$ is the subscriber's monthly recurring bill.

### Example:
- **Customer A:** Churn Probability = $0.80$, Monthly Charges = $\$100.00$ $\rightarrow$ Expected Monthly Risk = $\$80.00$.
- **Customer B:** Churn Probability = $0.20$, Monthly Charges = $\$100.00$ $\rightarrow$ Expected Monthly Risk = $\$20.00$.

This expected value framework enables leadership to aggregate portfolio risk accurately across business units without overstating certainty.
