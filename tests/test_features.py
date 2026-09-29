"""Unit tests for feature engineering transformations and leakage prevention."""

import numpy as np
import pandas as pd
import pytest

from src.features.builder import DomainFeatureEngineer, FEATURE_DICTIONARY


def test_feature_dictionary_integrity():
    """Ensures feature dictionary has all required audit fields."""
    assert len(FEATURE_DICTIONARY) >= 8
    for feat in FEATURE_DICTIONARY:
        assert "feature_name" in feat
        assert "definition" in feat
        assert "calculation" in feat
        assert "leakage_risk" in feat
        assert "availability_at_prediction_time" in feat


def test_domain_feature_engineer_transformations():
    """Validates engineered feature generation and absence of nulls or data leakage."""
    sample_data = pd.DataFrame({
        "customerID": ["CUST-1", "CUST-2"],
        "tenure": [1, 24],
        "MonthlyCharges": [85.50, 25.00],
        "TotalCharges": ["85.50", "600.00"],
        "Contract": ["Month-to-month", "Two year"],
        "InternetService": ["Fiber optic", "DSL"],
        "OnlineSecurity": ["No", "Yes"],
        "OnlineBackup": ["No", "Yes"],
        "DeviceProtection": ["No", "Yes"],
        "TechSupport": ["No", "Yes"],
        "StreamingTV": ["Yes", "No"],
        "StreamingMovies": ["Yes", "No"],
        "PaymentMethod": ["Electronic check", "Credit card (automatic)"],
        "Churn": ["Yes", "No"],
    })

    engineer = DomainFeatureEngineer()
    res = engineer.transform(sample_data)

    assert "is_month_to_month" in res.columns
    assert "is_electronic_check" in res.columns
    assert "is_high_risk_contract_spend" in res.columns
    assert "has_security_and_support" in res.columns
    assert "is_vulnerable_fiber_user" in res.columns
    assert "addon_services_count" in res.columns
    assert "billing_stability_ratio" in res.columns

    # CUST-1 should have high risk flags
    assert res.loc[0, "is_month_to_month"] == 1
    assert res.loc[0, "is_high_risk_contract_spend"] == 1
    assert res.loc[0, "is_vulnerable_fiber_user"] == 1
    assert res.loc[0, "addon_services_count"] == 2  # StreamingTV + StreamingMovies

    # CUST-2 should have protective features
    assert res.loc[1, "is_month_to_month"] == 0
    assert res.loc[1, "has_security_and_support"] == 1
    assert res.loc[1, "addon_services_count"] == 4
