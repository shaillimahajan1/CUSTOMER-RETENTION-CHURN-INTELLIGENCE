"""Data profiling, validation, and statistical hypothesis testing module."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

from src.utils.helpers import save_json, setup_logger

logger = setup_logger(__name__)


class DataProfiler:
    """Profiles raw and staged customer datasets, performing quality audits and statistical tests."""

    def __init__(self, target_col: str = "Churn", positive_val: str = "Yes"):
        self.target_col = target_col
        self.positive_val = positive_val

    def generate_quality_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculates comprehensive dataset profiling metrics."""
        total_rows = len(df)
        total_cols = len(df.columns)
        duplicate_rows = int(df.duplicated().sum())

        missing_per_col = df.isnull().sum().to_dict()
        missing_pct_per_col = (df.isnull().sum() / total_rows * 100.0).round(3).to_dict()

        # Identify blank/whitespace strings that act as hidden missing values (e.g. TotalCharges)
        whitespace_anomalies = {}
        for col in df.select_dtypes(include=["object"]).columns:
            blank_count = int(df[col].astype(str).str.strip().eq("").sum())
            if blank_count > 0:
                whitespace_anomalies[col] = {
                    "blank_count": blank_count,
                    "blank_pct": round(blank_count / total_rows * 100.0, 3),
                    "impact": "Stored as string with blank spaces; fails direct numeric casting.",
                    "treatment": "Converted to NULL or 0.0 with explicit documentation (associated with tenure=0).",
                }

        # Target distribution
        target_dist = {}
        if self.target_col in df.columns:
            counts = df[self.target_col].value_counts().to_dict()
            pcts = (df[self.target_col].value_counts(normalize=True) * 100.0).round(2).to_dict()
            target_dist = {
                "counts": {str(k): int(v) for k, v in counts.items()},
                "percentages": {str(k): float(v) for k, v in pcts.items()},
                "class_imbalance_ratio": round(
                    max(counts.values()) / max(min(counts.values()), 1), 2
                ),
            }

        # Numeric distributions
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        numeric_stats = {}
        for col in numeric_cols:
            s = df[col].dropna()
            q1, q3 = s.quantile(0.25), s.quantile(0.75)
            iqr = q3 - q1
            outliers = int(((s < (q1 - 1.5 * iqr)) | (s > (q3 + 1.5 * iqr))).sum())
            numeric_stats[col] = {
                "mean": round(float(s.mean()), 2),
                "std": round(float(s.std()), 2),
                "median": round(float(s.median()), 2),
                "min": round(float(s.min()), 2),
                "max": round(float(s.max()), 2),
                "iqr": round(float(iqr), 2),
                "outliers_count": outliers,
                "outliers_pct": round(outliers / max(len(s), 1) * 100.0, 2),
                "skewness": round(float(s.skew()), 3),
            }

        # Categorical cardinalities
        cat_cols = df.select_dtypes(include=["object"]).columns.tolist()
        categorical_stats = {
            col: {
                "unique_values": int(df[col].nunique()),
                "top_value": str(df[col].mode().iloc[0]) if not df[col].empty else "",
                "top_value_frequency": int(df[col].value_counts().iloc[0]) if not df[col].empty else 0,
            }
            for col in cat_cols
        }

        report = {
            "dataset_overview": {
                "total_records": total_rows,
                "total_features": total_cols,
                "duplicate_rows": duplicate_rows,
                "duplicate_pct": round(duplicate_rows / max(total_rows, 1) * 100.0, 2),
            },
            "missing_values": {
                "counts": {k: int(v) for k, v in missing_per_col.items() if v > 0},
                "percentages": {k: float(v) for k, v in missing_pct_per_col.items() if v > 0},
                "whitespace_anomalies": whitespace_anomalies,
            },
            "target_distribution": target_dist,
            "numeric_distributions": numeric_stats,
            "categorical_summary": categorical_stats,
        }

        return report

    def run_statistical_hypothesis_tests(self, df_clean: pd.DataFrame) -> List[Dict[str, Any]]:
        """Performs hypothesis testing (Mann-Whitney U, Chi-square, Benjamini-Hochberg FDR correction)."""
        logger.info("Running statistical hypothesis tests against Churn...")
        results = []

        if "churn_label" not in df_clean.columns:
            target_series = (df_clean[self.target_col] == self.positive_val).astype(int)
        else:
            target_series = df_clean["churn_label"].astype(int)

        # 1. Numerical Tests: Mann-Whitney U & Rank-biserial effect size
        numeric_candidates = ["tenure_months", "monthly_charges", "total_charges", "addon_services_count"]
        for col in numeric_candidates:
            if col in df_clean.columns:
                group_churn = df_clean.loc[target_series == 1, col].dropna()
                group_stay = df_clean.loc[target_series == 0, col].dropna()

                stat, p_val = stats.mannwhitneyu(group_churn, group_stay, alternative="two-sided")
                # Rank-biserial correlation: r = 1 - (2*U)/(n1*n2)
                n1, n2 = len(group_churn), len(group_stay)
                rank_biserial = 1.0 - (2.0 * stat) / (n1 * n2)

                results.append({
                    "feature": col,
                    "test_type": "Mann-Whitney U",
                    "null_hypothesis": f"Distribution of {col} is identical between churn and retained customers",
                    "test_statistic": round(float(stat), 2),
                    "raw_p_value": float(p_val),
                    "effect_size_metric": "Rank-biserial correlation",
                    "effect_size": round(float(rank_biserial), 4),
                    "group_churn_mean": round(float(group_churn.mean()), 2),
                    "group_retained_mean": round(float(group_stay.mean()), 2),
                })

        # 2. Categorical Tests: Chi-Square Test of Independence & Cramer's V
        categorical_candidates = [
            "contract_type", "internet_service", "payment_method", "gender",
            "is_senior_citizen", "has_partner", "has_dependents", "has_paperless_billing",
            "online_security", "tech_support"
        ]
        for col in categorical_candidates:
            if col in df_clean.columns:
                contingency = pd.crosstab(df_clean[col], target_series)
                chi2, p_val, dof, _ = stats.chi2_contingency(contingency)
                n = contingency.values.sum()
                min_dim = min(contingency.shape) - 1
                cramers_v = np.sqrt(chi2 / (n * max(min_dim, 1))) if min_dim > 0 else 0.0

                results.append({
                    "feature": col,
                    "test_type": "Chi-Square Test of Independence",
                    "null_hypothesis": f"No association between {col} and customer churn",
                    "test_statistic": round(float(chi2), 2),
                    "raw_p_value": float(p_val),
                    "effect_size_metric": "Cramer's V",
                    "effect_size": round(float(cramers_v), 4),
                    "degrees_of_freedom": int(dof),
                })

        # 3. Apply Benjamini-Hochberg (FDR) and Bonferroni adjustments
        raw_p_vals = [r["raw_p_value"] for r in results]
        reject_fdr, p_adj_bh, _, _ = multipletests(raw_p_vals, alpha=0.05, method="fdr_bh")
        reject_bonf, p_adj_bonf, _, _ = multipletests(raw_p_vals, alpha=0.05, method="bonferroni")

        for idx, r in enumerate(results):
            r["p_value_bh_adjusted"] = float(p_adj_bh[idx])
            r["p_value_bonferroni"] = float(p_adj_bonf[idx])
            r["statistically_significant_bh"] = bool(reject_fdr[idx])
            r["statistically_significant_bonf"] = bool(reject_bonf[idx])

            # Business significance assessment based on effect size
            eff = abs(r["effect_size"])
            if eff >= 0.35:
                r["business_importance"] = "High Practical Importance"
            elif eff >= 0.15:
                r["business_importance"] = "Moderate Practical Importance"
            else:
                r["business_importance"] = "Low / Weak Practical Importance"

        return results
