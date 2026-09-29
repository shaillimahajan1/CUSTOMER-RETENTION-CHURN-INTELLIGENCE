# Retention Strategy & Intervention Playbook

## 1. The 2x2 Risk vs Revenue Decision Matrix

Retention capacity is finite. To optimize return on intervention spend, accounts are partitioned across two orthogonal dimensions:
1. **Predicted Churn Vulnerability:** High / Critical Risk vs Low / Medium Risk.
2. **Customer Financial Value:** High Value (top 25% of spend, $\ge \$89.85/\text{mo}$) vs Standard Value ($< \$89.85/\text{mo}$).

```text
                                  Customer Financial Value
                         Standard Value               High Value (Top 25%)
                ┌──────────────────────────────┬──────────────────────────────┐
                │ Tier 2: Automated Campaign   │ Tier 1: VIP Urgent Outreach  │
   High /       │ • Volume: 1,031 accounts     │ • Volume: 484 accounts       │
   Critical     │ • Rev@Risk: $38.1K / mo      │ • Rev@Risk: $45.2K / mo      │
   Risk         │ • Action: Digital Offer /    │ • Action: Dedicated CSM Call │
                │   In-app Contract Upgrade    │   + Custom Lock-in Credit    │
                ├──────────────────────────────┼──────────────────────────────┤
                │ Tier 4: Standard Operation   │ Tier 3: Proactive Care       │
   Low /        │ • Volume: 4,251 accounts     │ • Volume: 1,277 accounts     │
   Medium       │ • Rev@Risk: Baseline low     │ • Rev@Risk: $21.4K (monitor) │
   Risk         │ • Action: Standard lifecycle │ • Action: Quarterly Health   │
                │   support / Self-serve       │   Check / Feature Adoption   │
                └──────────────────────────────┴──────────────────────────────┘
```

---

## 2. Action Playbooks by Driver Profile

| Observable Risk Driver | Primary Mechanism | Recommended Intervention Playbook | Estimated Delivery Cost |
| :--- | :--- | :--- | :--- |
| **New Subscriber on Month-to-Month Contract** | Customer has not formed product habits; zero exit barrier. | **Contract Upgrade Incentive:** Offer $\$15/\text{mo}$ billing credit for 3 months upon upgrading to 1-Year agreement. | Low (\$45 total concession) |
| **Fiber Optic with No TechSupport** | High-speed fiber users experience setup or speed glitches without guidance. | **Support Safety Net:** Provide complimentary 3-month trial of Premium 24/7 TechSupport + onboarding check-in. | Negligible marginal cost |
| **Electronic Check Payment Friction** | Manual electronic check requires monthly manual effort and has higher failure rates. | **AutoPay Bonus:** $\$10$ one-time account credit upon enrolling in automated Credit Card / Bank transfer billing. | One-time \$10 |
| **High Monthly Spend ($>\$90) on Month-to-Month** | Account feels price strain and has no contractual commitment. | **VIP Executive Call:** Senior retention manager conducts plan optimization audit to eliminate unused add-ons. | Medium (\$25 labor cost) |

---

## 3. Intervention Experimentation Framework (A/B Testing)

*Crucial Reality:* **A predictive model identifies risk; it does NOT prove which retention action works.**
Before scaling retention discounts company-wide, the team must run randomized controlled trials (RCTs):
1. **Target Population:** Tier 1 VIP high-risk accounts.
2. **Treatment Group (50%):** Receives dedicated CSM phone outreach and contract upgrade credit.
3. **Control Group (50%):** Receives standard operational communication without intervention.
4. **Primary KPI:** Incremental Churn Reduction = $\text{Churn Rate}_{\text{control}} - \text{Churn Rate}_{\text{treatment}}$.
5. **Economic KPI:** Net Incremental Revenue Saved vs Cost of Discounts.
