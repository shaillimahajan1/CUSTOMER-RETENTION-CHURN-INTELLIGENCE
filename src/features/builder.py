"""Leakage-safe feature engineering pipeline and feature dictionary generator."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, RobustScaler

from src.utils.helpers import setup_logger

logger = setup_logger(__name__)

FEATURE_DICTIONARY: List[Dict[str, str]] = [
    {
        "feature_name": "tenure_months",
        "definition": "Number of months the customer has stayed with the company.",
        "source": "tenure",
        "calculation": "Direct integer cast from raw tenure.",
        "business_meaning": "Proxy for customer relationship maturity and habitual brand loyalty.",
        "availability_at_prediction_time": "Available at any point during active subscription.",
        "leakage_risk": "None. Measured up to prediction cutoff.",
    },
    {
        "feature_name": "monthly_charges",
        "definition": "Current recurring monthly charge billed to customer.",
        "source": "MonthlyCharges",
        "calculation": "Direct numeric cast from raw MonthlyCharges.",
        "business_meaning": "Current recurring price burden and subscription complexity tier.",
        "availability_at_prediction_time": "Available in active billing system.",
        "leakage_risk": "None. Relates to current subscription plan.",
    },
    {
        "feature_name": "total_charges",
        "definition": "Cumulative historical payments billed to the customer.",
        "source": "TotalCharges",
        "calculation": "Parsed double; missing blanks for tenure=0 imputed to 0.0.",
        "business_meaning": "Total lifetime monetary commitment to the company.",
        "availability_at_prediction_time": "Available in ledger at prediction timestamp.",
        "leakage_risk": "None. Only encompasses charges billed up to current date.",
    },
    {
        "feature_name": "addon_services_count",
        "definition": "Total count of auxiliary services activated.",
        "source": "OnlineSecurity, OnlineBackup, DeviceProtection, TechSupport, StreamingTV, StreamingMovies",
        "calculation": "Sum of positive indicator flags across the 6 optional services (0-6).",
        "business_meaning": "Indicates customer service depth and switching friction (stickiness).",
        "availability_at_prediction_time": "Available in active service catalog.",
        "leakage_risk": "None.",
    },
    {
        "feature_name": "billing_stability_ratio",
        "definition": "Ratio of cumulative historical charges to expected run-rate (tenure * monthly_charges).",
        "source": "TotalCharges, MonthlyCharges, tenure",
        "calculation": "TotalCharges / ((tenure + 1) * MonthlyCharges).",
        "business_meaning": "Identifies recent pricing plan changes or historical promotional discounts ending.",
        "availability_at_prediction_time": "Available at prediction time.",
        "leakage_risk": "None. Uses historical ledger figures.",
    },
    {
        "feature_name": "is_month_to_month",
        "definition": "Indicator if customer has no long-term contractual commitment.",
        "source": "Contract",
        "calculation": "1 if Contract == 'Month-to-month' else 0.",
        "business_meaning": "Zero contractual switching penalty; highest transactional elasticity.",
        "availability_at_prediction_time": "Available in CRM/Billing.",
        "leakage_risk": "None.",
    },
    {
        "feature_name": "is_high_risk_contract_spend",
        "definition": "Interaction between Month-to-Month contract and premium monthly charges (> $70).",
        "source": "Contract, MonthlyCharges",
        "calculation": "1 if (Contract == 'Month-to-month' and MonthlyCharges > 70.0) else 0.",
        "business_meaning": "High expense with zero commitment represents peak vulnerability.",
        "availability_at_prediction_time": "Available in CRM/Billing.",
        "leakage_risk": "None.",
    },
    {
        "feature_name": "has_security_and_support",
        "definition": "Indicator if customer subscribes to both OnlineSecurity and TechSupport.",
        "source": "OnlineSecurity, TechSupport",
        "calculation": "1 if (OnlineSecurity == 'Yes' and TechSupport == 'Yes') else 0.",
        "business_meaning": "Protective service bundle known to dramatically increase retention stickiness.",
        "availability_at_prediction_time": "Available in CRM/Billing.",
        "leakage_risk": "None.",
    },
    {
        "feature_name": "is_vulnerable_fiber_user",
        "definition": "Indicator if customer has high-speed Fiber Optic internet without TechSupport.",
        "source": "InternetService, TechSupport",
        "calculation": "1 if (InternetService == 'Fiber optic' and TechSupport == 'No') else 0.",
        "business_meaning": "High-fee fiber users without technical assistance exhibit peak churn hazard.",
        "availability_at_prediction_time": "Available in CRM/Billing.",
        "leakage_risk": "None.",
    },
]


class DomainFeatureEngineer(BaseEstimator, TransformerMixin):
    """Generates leakage-safe domain features in a scikit-learn compatible pipeline."""

    def __init__(self):
        pass

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        df = X.copy()

        # Handle TotalCharges if present as string
        if "TotalCharges" in df.columns and df["TotalCharges"].dtype == "object":
            df["TotalCharges"] = pd.to_numeric(df["TotalCharges"].astype(str).str.strip(), errors="coerce").fillna(0.0)

        # Standardize column naming if needed
        tenure_col = "tenure_months" if "tenure_months" in df.columns else "tenure"
        monthly_col = "monthly_charges" if "monthly_charges" in df.columns else "MonthlyCharges"
        total_col = "total_charges" if "total_charges" in df.columns else "TotalCharges"
        contract_col = "contract_type" if "contract_type" in df.columns else "Contract"
        internet_col = "internet_service" if "internet_service" in df.columns else "InternetService"
        tech_col = "tech_support" if "tech_support" in df.columns else "TechSupport"
        sec_col = "online_security" if "online_security" in df.columns else "OnlineSecurity"
        pay_col = "payment_method" if "payment_method" in df.columns else "PaymentMethod"

        # Safe numeric casts
        tenure_vals = pd.to_numeric(df[tenure_col], errors="coerce").fillna(0.0)
        monthly_vals = pd.to_numeric(df[monthly_col], errors="coerce").fillna(0.0)
        total_vals = pd.to_numeric(df[total_col], errors="coerce").fillna(0.0)

        # 1. Add-on services count (0 to 6)
        addon_cols = ["OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies"]
        addon_count = np.zeros(len(df))
        for ac in addon_cols:
            alt_ac = ac.lower()
            if ac in df.columns:
                addon_count += (df[ac].astype(str).str.strip() == "Yes").astype(int)
            elif alt_ac in df.columns:
                addon_count += (df[alt_ac].astype(str).str.strip() == "Yes").astype(int)
            elif f"has_{alt_ac}" in df.columns:
                addon_count += (df[f"has_{alt_ac}"] == 1).astype(int)

        df["addon_services_count"] = addon_count

        # 2. Billing stability ratio
        expected_runrate = (tenure_vals + 1.0) * monthly_vals
        df["billing_stability_ratio"] = np.where(
            expected_runrate > 0,
            np.clip(total_vals / expected_runrate, 0.0, 5.0),
            1.0
        )

        # 3. Domain binary flags
        df["is_month_to_month"] = (df[contract_col].astype(str).str.strip() == "Month-to-month").astype(int)
        df["is_electronic_check"] = (df[pay_col].astype(str).str.strip() == "Electronic check").astype(int)
        df["is_fiber_optic"] = (df[internet_col].astype(str).str.strip() == "Fiber optic").astype(int)

        # 4. Domain risk interaction terms
        df["is_high_risk_contract_spend"] = (
            (df[contract_col].astype(str).str.strip() == "Month-to-month") & (monthly_vals > 70.0)
        ).astype(int)

        df["has_security_and_support"] = (
            (df[sec_col].astype(str).str.strip() == "Yes") & (df[tech_col].astype(str).str.strip() == "Yes")
        ).astype(int)

        df["is_vulnerable_fiber_user"] = (
            (df[internet_col].astype(str).str.strip() == "Fiber optic") & (df[tech_col].astype(str).str.strip() == "No")
        ).astype(int)

        # Ensure numeric columns are standardized
        df["tenure_months"] = tenure_vals
        df["monthly_charges"] = monthly_vals
        df["total_charges"] = total_vals

        return df


def create_feature_pipeline(
    numeric_features: List[str],
    categorical_features: List[str]
) -> ColumnTransformer:
    """Builds a scikit-learn ColumnTransformer that scales numeric features with RobustScaler
    and one-hot encodes categoricals, strictly fit on training splits to prevent data leakage."""
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                RobustScaler(),
                numeric_features,
            ),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False, drop="first"),
                categorical_features,
            ),
        ],
        remainder="drop",
    )
    return preprocessor
