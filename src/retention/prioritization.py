"""Customer risk scoring, expected revenue-at-risk, 2x2 prioritization matrix, and action playbook."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd

from src.utils.helpers import save_json, setup_logger

logger = setup_logger(__name__)


class RetentionPrioritizer:
    """Scores customers on risk and expected revenue exposure, assigning prioritization tiers and action playbooks."""

    def __init__(
        self,
        decision_threshold: float = 0.38,
        risk_cutoffs: Tuple[float, float, float] = (0.25, 0.50, 0.75),
        high_value_percentile: float = 75.0,
    ):
        self.decision_threshold = decision_threshold
        self.risk_cutoffs = risk_cutoffs
        self.high_value_percentile = high_value_percentile

    def score_customers(
        self,
        raw_df: pd.DataFrame,
        probabilities: np.ndarray,
        top_risk_drivers: List[str] | None = None,
    ) -> pd.DataFrame:
        """Assigns churn probabilities, risk segments, revenue-at-risk, priority tiers, and recommendations."""
        df = raw_df.copy()

        # Handle customer identifier
        id_col = "customer_id" if "customer_id" in df.columns else "customerID"
        df["customer_id"] = df[id_col].astype(str)

        # Monthly Charges
        m_col = "monthly_charges" if "monthly_charges" in df.columns else "MonthlyCharges"
        df["monthly_revenue_exposure"] = pd.to_numeric(df[m_col], errors="coerce").fillna(0.0)
        df["annual_revenue_exposure"] = (df["monthly_revenue_exposure"] * 12.0).round(2)

        # Churn Probability
        df["churn_probability"] = np.clip(probabilities, 0.0, 1.0).round(4)
        df["predicted_churn_flag"] = (df["churn_probability"] >= self.decision_threshold).astype(int)

        # Risk Segments
        c1, c2, c3 = self.risk_cutoffs
        df["risk_segment"] = np.select(
            [
                df["churn_probability"] < c1,
                (df["churn_probability"] >= c1) & (df["churn_probability"] < c2),
                (df["churn_probability"] >= c2) & (df["churn_probability"] < c3),
                df["churn_probability"] >= c3,
            ],
            ["Low Risk", "Medium Risk", "High Risk", "Critical Risk"],
            default="Medium Risk",
        )

        # Expected Revenue at Risk = Churn Probability * Revenue Exposure
        df["monthly_revenue_at_risk"] = (
            df["churn_probability"] * df["monthly_revenue_exposure"]
        ).round(2)
        df["annual_revenue_at_risk"] = (
            df["churn_probability"] * df["annual_revenue_exposure"]
        ).round(2)

        # Value Tier based on 75th percentile of monthly charges
        high_val_cutoff = df["monthly_revenue_exposure"].quantile(self.high_value_percentile / 100.0)
        df["customer_value_tier"] = np.where(
            df["monthly_revenue_exposure"] >= high_val_cutoff, "High Value", "Standard Value"
        )

        # 2x2 Retention Prioritization Matrix
        # Risk (High/Critical vs Low/Med) x Revenue (High vs Standard)
        is_elevated_risk = df["risk_segment"].isin(["High Risk", "Critical Risk"])
        is_high_value = df["customer_value_tier"] == "High Value"

        df["retention_priority_tier"] = np.select(
            [
                is_elevated_risk & is_high_value,      # Tier 1: High Risk + High Value
                is_elevated_risk & (~is_high_value),   # Tier 2: High Risk + Standard Value
                (~is_elevated_risk) & is_high_value,   # Tier 3: Low/Med Risk + High Value
            ],
            [
                "Tier 1: VIP Urgent Outreach",
                "Tier 2: Automated Campaign Offer",
                "Tier 3: Proactive Account Care",
            ],
            default="Tier 4: Standard Operation / Monitor",
        )

        # Risk drivers if provided
        if top_risk_drivers and len(top_risk_drivers) == len(df):
            df["top_risk_driver"] = top_risk_drivers
        else:
            df["top_risk_driver"] = self._heuristic_risk_drivers(df)

        # Playbook-based recommended retention action
        df["recommended_action"] = self._assign_recommended_actions(df)

        # Clean selected columns for final analytical delivery
        final_cols = [
            "customer_id",
            "risk_segment",
            "churn_probability",
            "predicted_churn_flag",
            "monthly_revenue_exposure",
            "annual_revenue_exposure",
            "monthly_revenue_at_risk",
            "annual_revenue_at_risk",
            "customer_value_tier",
            "retention_priority_tier",
            "top_risk_driver",
            "recommended_action",
        ]
        # Return final columns first, followed by all domain and contextual features
        existing_cols = [c for c in df.columns if c not in final_cols]
        return df[final_cols + existing_cols]

    def _heuristic_risk_drivers(self, df: pd.DataFrame) -> pd.Series:
        """Determines predominant observable risk driver based on rule hierarchy."""
        contract_col = "contract_type" if "contract_type" in df.columns else "Contract"
        pay_col = "payment_method" if "payment_method" in df.columns else "PaymentMethod"
        internet_col = "internet_service" if "internet_service" in df.columns else "InternetService"
        tenure_col = "tenure_months" if "tenure_months" in df.columns else "tenure"

        conds = [
            (df[contract_col].astype(str) == "Month-to-month") & (pd.to_numeric(df[tenure_col], errors="coerce") <= 6),
            (df[contract_col].astype(str) == "Month-to-month"),
            (df[internet_col].astype(str) == "Fiber optic") & (df["monthly_revenue_exposure"] > 80.0),
            (df[pay_col].astype(str) == "Electronic check"),
            (pd.to_numeric(df[tenure_col], errors="coerce") <= 12),
        ]
        choices = [
            "New Subscriber on Month-to-Month Contract",
            "Uncommitted Month-to-Month Contract",
            "High Premium Fiber Billing with No Commitment",
            "Electronic Check Payment Friction",
            "Early Relationship Churn Vulnerability",
        ]
        return pd.Series(np.select(conds, choices, default="General Service Under-utilization"), index=df.index)

    def _assign_recommended_actions(self, df: pd.DataFrame) -> pd.Series:
        """Maps customer profile to actionable retention intervention playbook."""
        tier = df["retention_priority_tier"]
        driver = df["top_risk_driver"]

        conds = [
            tier == "Tier 1: VIP Urgent Outreach",
            (tier == "Tier 2: Automated Campaign Offer") & driver.str.contains("Contract", na=False),
            (tier == "Tier 2: Automated Campaign Offer") & driver.str.contains("Electronic Check", na=False),
            tier == "Tier 2: Automated Campaign Offer",
            tier == "Tier 3: Proactive Account Care",
        ]
        choices = [
            "Dedicated Account Rep Call + 20% Annual Contract Lock-in Credit",
            "Targeted Email: Offer $15/mo discount on 1-Year Contract Upgrade",
            "Automated App Prompt: $10 one-time bill credit to enroll in AutoPay",
            "Automated Digital Voucher + Free 3-Month TechSupport Trial",
            "Quarterly Relationship Check-in + Loyalty Service Audit",
        ]
        return pd.Series(
            np.select(conds, choices, default="No Active Outreach - Monitor Quarterly Usage"),
            index=df.index,
        )
