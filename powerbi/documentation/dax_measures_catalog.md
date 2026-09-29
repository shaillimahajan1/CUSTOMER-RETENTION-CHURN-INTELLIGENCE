# Power BI DAX Measures Catalog

This catalog provides production-ready, standardized DAX formulas for the **Customer Retention & Churn Intelligence** report.

---

## 1. Core Volume Measures

```dax
Total Customers = 
COUNTROWS('powerbi_customer_retention_dataset')
```

```dax
Retained Customers = 
CALCULATE(
    COUNTROWS('powerbi_customer_retention_dataset'),
    'powerbi_customer_retention_dataset'[churn_label] = 0
)
```

```dax
Historical Churned Customers = 
CALCULATE(
    COUNTROWS('powerbi_customer_retention_dataset'),
    'powerbi_customer_retention_dataset'[churn_label] = 1
)
```

```dax
Historical Churn Rate % = 
DIVIDE(
    [Historical Churned Customers],
    [Total Customers],
    0
) * 100
```

---

## 2. Predictive Risk Measures

```dax
High Risk Customer Count = 
CALCULATE(
    COUNTROWS('powerbi_customer_retention_dataset'),
    'powerbi_customer_retention_dataset'[risk_segment] IN {"High Risk", "Critical Risk"}
)
```

```dax
High Risk Customer % = 
DIVIDE(
    [High Risk Customer Count],
    [Total Customers],
    0
) * 100
```

```dax
Average Churn Probability = 
AVERAGE('powerbi_customer_retention_dataset'[churn_probability])
```

---

## 3. Revenue Exposure & Expected Revenue at Risk

```dax
Total Monthly Revenue Exposure = 
SUM('powerbi_customer_retention_dataset'[monthly_revenue_exposure])
```

```dax
Total Annual Revenue Exposure = 
SUM('powerbi_customer_retention_dataset'[annual_revenue_exposure])
```

```dax
Monthly Expected Revenue at Risk = 
SUM('powerbi_customer_retention_dataset'[monthly_revenue_at_risk])
```

```dax
Annualized Expected Revenue at Risk = 
SUM('powerbi_customer_retention_dataset'[annual_revenue_at_risk])
```

```dax
Revenue at Risk % of Total = 
DIVIDE(
    [Monthly Expected Revenue at Risk],
    [Total Monthly Revenue Exposure],
    0
) * 100
```

---

## 4. Priority Tiers & Business Decision Measures

```dax
Tier 1 VIP Customer Count = 
CALCULATE(
    COUNTROWS('powerbi_customer_retention_dataset'),
    'powerbi_customer_retention_dataset'[retention_priority_tier] = "Tier 1: VIP Urgent Outreach"
)
```

```dax
Tier 1 Monthly Revenue at Risk = 
CALCULATE(
    [Monthly Expected Revenue at Risk],
    'powerbi_customer_retention_dataset'[retention_priority_tier] = "Tier 1: VIP Urgent Outreach"
)
```

```dax
Estimated Retention Savings (35% Success Assumption) = 
[Monthly Expected Revenue at Risk] * 0.35
```

```dax
Estimated Annual Net Retention ROI = 
VAR SavedRevenue = [Annualized Expected Revenue at Risk] * 0.35
VAR OutreachCost = [High Risk Customer Count] * 20.0 * 12.0
RETURN
SavedRevenue - OutreachCost
```
