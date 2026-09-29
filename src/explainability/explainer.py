"""SHAP TreeExplainer module for global and customer-level model interpretability."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

from src.utils.helpers import save_json, setup_logger

logger = setup_logger(__name__)


class ChurnExplainer:
    """Computes global and local SHAP explanations for tree-based churn models."""

    def __init__(self, model: Any, preprocessor: Any, feature_names: List[str]):
        self.model = model
        self.preprocessor = preprocessor
        self.feature_names = feature_names
        # Initialize SHAP TreeExplainer
        self.explainer = shap.TreeExplainer(self.model)
        logger.info(f"Initialized SHAP TreeExplainer with {len(feature_names)} features.")

    def explain_dataset(
        self,
        X_df: pd.DataFrame,
        output_dir: str | Path = "outputs/shap",
        charts_dir: str | Path = "outputs/charts",
        max_samples: int = 1500,
    ) -> Tuple[np.ndarray, pd.DataFrame]:
        """Calculates SHAP values for a sample of customers, generating global importances and summary chart."""
        out_path = Path(output_dir)
        chart_path = Path(charts_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        chart_path.mkdir(parents=True, exist_ok=True)

        # Sample if dataset is large to maintain fast interactive performance
        if len(X_df) > max_samples:
            sample_df = X_df.sample(n=max_samples, random_state=42)
        else:
            sample_df = X_df.copy()

        X_transformed = self.preprocessor.transform(sample_df)
        shap_values = self.explainer.shap_values(X_transformed)

        # In binary classification, check shape
        if isinstance(shap_values, list):
            sv = shap_values[1]
        elif len(shap_values.shape) == 3:
            sv = shap_values[:, :, 1]
        else:
            sv = shap_values

        mean_abs_shap = np.mean(np.abs(sv), axis=0)
        importance_df = pd.DataFrame({
            "feature": self.feature_names,
            "mean_abs_shap": mean_abs_shap,
        }).sort_values(by="mean_abs_shap", ascending=False).reset_index(drop=True)

        # Save global importance table
        save_json(
            importance_df.to_dict(orient="records"),
            out_path / "global_shap_importance.json",
        )

        # Generate and save SHAP summary plot
        plt.figure(figsize=(10, 8))
        shap.summary_plot(
            sv,
            X_transformed,
            feature_names=self.feature_names,
            show=False,
            max_display=15,
        )
        plt.title("SHAP Global Feature Importance (Top Predictive Associations)", fontsize=13, pad=15)
        plt.tight_layout()
        plt.savefig(chart_path / "shap_summary_plot.png", dpi=200, bbox_inches="tight")
        plt.close()

        logger.info(f"Global SHAP calculations complete. Top 3 features: {importance_df['feature'].iloc[:3].tolist()}")
        return sv, importance_df

    def explain_single_customer(
        self, customer_features: pd.DataFrame
    ) -> Dict[str, Any]:
        """Extracts individual feature contributions for a specific customer."""
        X_trans = self.preprocessor.transform(customer_features)
        shap_vals = self.explainer.shap_values(X_trans)

        if isinstance(shap_vals, list):
            c_sv = shap_vals[1][0]
        elif len(shap_vals.shape) == 3:
            c_sv = shap_vals[0, :, 1]
        else:
            c_sv = shap_vals[0]

        contributions = []
        for feat, val in zip(self.feature_names, c_sv):
            contributions.append({
                "feature": feat,
                "shap_value": round(float(val), 4),
                "direction": "Risk Driver (Increases Churn Risk)" if val > 0 else "Protective (Reduces Churn Risk)",
            })

        # Sort by absolute impact
        contributions.sort(key=lambda x: abs(x["shap_value"]), reverse=True)

        top_risk_driver = next(
            (c["feature"] for c in contributions if c["shap_value"] > 0), "None"
        )
        top_protective = next(
            (c["feature"] for c in contributions if c["shap_value"] < 0), "None"
        )

        return {
            "top_risk_driver": top_risk_driver,
            "top_protective_factor": top_protective,
            "detailed_contributions": contributions[:8],
        }
