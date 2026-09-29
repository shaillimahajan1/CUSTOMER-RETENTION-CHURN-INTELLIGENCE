"""Unit tests for revenue at risk, risk segmentation, and retention prioritization logic."""

import numpy as np
import pandas as pd
import pytest

from src.retention.prioritization import RetentionPrioritizer


def test_revenue_at_risk_calculation():
    """Validates that Revenue-at-Risk equals Churn Probability * Revenue Exposure."""
    sample_df = pd.DataFrame({
        "customer_id": ["C1", "C2", "C3"],
        "monthly_charges": [100.0, 50.0, 20.0],
        "contract_type": ["Month-to-month", "Month-to-month", "Two year"],
        "internet_service": ["Fiber optic", "DSL", "No"],
        "payment_method": ["Electronic check", "Mailed check", "Bank transfer"],
        "tenure_months": [3, 12, 60],
    })
    probs = np.array([0.80, 0.40, 0.10])

    prioritizer = RetentionPrioritizer(
        decision_threshold=0.35,
        risk_cutoffs=(0.25, 0.50, 0.75),
        high_value_percentile=60.0,
    )
    scored = prioritizer.score_customers(sample_df, probs)

    # C1: 0.80 * 100.0 = 80.0
    assert scored.loc[0, "monthly_revenue_at_risk"] == pytest.approx(80.0, rel=1e-3)
    assert scored.loc[0, "annual_revenue_at_risk"] == pytest.approx(960.0, rel=1e-3)
    assert scored.loc[0, "risk_segment"] == "Critical Risk"

    # C2: 0.40 * 50.0 = 20.0
    assert scored.loc[1, "monthly_revenue_at_risk"] == pytest.approx(20.0, rel=1e-3)
    assert scored.loc[1, "risk_segment"] == "Medium Risk"

    # C3: 0.10 * 20.0 = 2.0
    assert scored.loc[2, "monthly_revenue_at_risk"] == pytest.approx(2.0, rel=1e-3)
    assert scored.loc[2, "risk_segment"] == "Low Risk"


def test_retention_prioritization_tiers():
    """Validates allocation of customers into Tier 1 (VIP Urgent) through Tier 4 (Monitor)."""
    sample_df = pd.DataFrame({
        "customer_id": ["HIGH_VAL_HIGH_RISK", "LOW_VAL_HIGH_RISK", "HIGH_VAL_LOW_RISK", "LOW_VAL_LOW_RISK"],
        "monthly_charges": [120.0, 20.0, 115.0, 25.0],
        "contract_type": ["Month-to-month", "Month-to-month", "Two year", "Two year"],
        "internet_service": ["Fiber optic", "DSL", "Fiber optic", "No"],
        "payment_method": ["Electronic check", "Electronic check", "Credit card", "Mailed check"],
        "tenure_months": [2, 4, 48, 55],
    })
    # Probabilities: Critical, High, Low, Low
    probs = np.array([0.85, 0.65, 0.15, 0.05])

    prioritizer = RetentionPrioritizer(
        decision_threshold=0.35,
        risk_cutoffs=(0.25, 0.50, 0.75),
        high_value_percentile=50.0,
    )
    scored = prioritizer.score_customers(sample_df, probs)

    assert scored.loc[0, "retention_priority_tier"] == "Tier 1: VIP Urgent Outreach"
    assert scored.loc[1, "retention_priority_tier"] == "Tier 2: Automated Campaign Offer"
    assert scored.loc[2, "retention_priority_tier"] == "Tier 3: Proactive Account Care"
    assert scored.loc[3, "retention_priority_tier"] == "Tier 4: Standard Operation / Monitor"
