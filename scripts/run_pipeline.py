"""Master End-to-End Pipeline Runner for Customer Retention & Churn Intelligence.

Executes:
1. Raw Data Ingestion & DuckDB Schema Creation
2. SQL Analytical Views & Data Quality Assertions
3. Statistical Profiling & Hypothesis Testing (Mann-Whitney U, Chi-Square, FDR)
4. Leakage-Safe Feature Engineering & Stratified Train/Test Split
5. Baseline Logistic Regression vs Advanced XGBoost Modeling
6. Threshold Optimization & Business Cost Analysis
7. Global & Local SHAP Explainability
8. Customer Risk Scoring & Revenue-at-Risk Quantification
9. 2x2 Retention Prioritization Matrix & Action Playbook
10. Power BI Dataset Exports & Diagnostic Charts
"""

from __future__ import annotations

import datetime
from pathlib import Path
import sys

# Ensure repository root is on Python path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import precision_recall_curve, roc_curve

from src.data.db import DuckDBManager
from src.data.loader import download_raw_dataset, load_raw_data
from src.explainability.explainer import ChurnExplainer
from src.features.builder import DomainFeatureEngineer
from src.modeling.train import ModelTrainer
from src.retention.prioritization import RetentionPrioritizer
from src.utils.helpers import ensure_directories, load_config, save_json, set_seed, setup_logger
from src.validation.profiler import DataProfiler

logger = setup_logger("run_pipeline")


def generate_diagnostic_plots(
    y_test: pd.Series,
    lr_probs: np.ndarray,
    xgb_probs: np.ndarray,
    optimal_thresh: float,
    charts_dir: Path,
) -> None:
    """Generates ROC curves, PR curves, and Calibration curves for the model comparison."""
    charts_dir.mkdir(parents=True, exist_ok=True)

    # 1. ROC Curve
    plt.figure(figsize=(8, 6))
    fpr_lr, tpr_lr, _ = roc_curve(y_test, lr_probs)
    fpr_xgb, tpr_xgb, _ = roc_curve(y_test, xgb_probs)
    from sklearn.metrics import auc
    auc_lr = auc(fpr_lr, tpr_lr)
    auc_xgb = auc(fpr_xgb, tpr_xgb)
    plt.plot(fpr_lr, tpr_lr, label=f"Logistic Regression (AUC = {auc_lr:.3f})", color="#6c757d", linestyle="--")
    plt.plot(fpr_xgb, tpr_xgb, label=f"XGBoost Advanced (AUC = {auc_xgb:.3f})", color="#1f77b4", linewidth=2)
    plt.plot([0, 1], [0, 1], "k:", alpha=0.6, label="Random Guess (AUC = 0.500)")
    plt.xlabel("False Positive Rate (1 - Specificity)", fontsize=11)
    plt.ylabel("True Positive Rate (Recall)", fontsize=11)
    plt.title("Receiver Operating Characteristic (ROC) Comparison", fontsize=13, pad=12)
    plt.legend(loc="lower right", frameon=True)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(charts_dir / "roc_curve_comparison.png", dpi=200)
    plt.close()

    # 2. Precision-Recall Curve
    plt.figure(figsize=(8, 6))
    p_lr, r_lr, _ = precision_recall_curve(y_test, lr_probs)
    p_xgb, r_xgb, thresh_xgb = precision_recall_curve(y_test, xgb_probs)
    plt.plot(r_lr, p_lr, label="Logistic Regression Baseline", color="#6c757d", linestyle="--")
    plt.plot(r_xgb, p_xgb, label="XGBoost Classifier", color="#1f77b4", linewidth=2)
    # Highlight chosen threshold
    closest_idx = np.argmin(np.abs(thresh_xgb - optimal_thresh))
    plt.scatter(
        [r_xgb[closest_idx]], [p_xgb[closest_idx]],
        color="#d62728", s=100, zorder=5,
        label=f"Selected Threshold ({optimal_thresh:.2f})"
    )
    plt.xlabel("Recall (Fraction of Actual Churners Captured)", fontsize=11)
    plt.ylabel("Precision (Fraction of Outreach That Is Churner)", fontsize=11)
    plt.title("Precision-Recall Curve (Minority Class Optimization)", fontsize=13, pad=12)
    plt.legend(loc="upper right", frameon=True)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(charts_dir / "precision_recall_comparison.png", dpi=200)
    plt.close()

    # 3. Probability Calibration Curve
    plt.figure(figsize=(8, 6))
    prob_true_lr, prob_pred_lr = calibration_curve(y_test, lr_probs, n_bins=10, strategy="uniform")
    prob_true_xgb, prob_pred_xgb = calibration_curve(y_test, xgb_probs, n_bins=10, strategy="uniform")
    plt.plot([0, 1], [0, 1], "k:", label="Perfect Calibration")
    plt.plot(prob_pred_lr, prob_true_lr, "s-", label="Logistic Regression", color="#6c757d")
    plt.plot(prob_pred_xgb, prob_true_xgb, "o-", label="XGBoost", color="#1f77b4")
    plt.xlabel("Mean Predicted Probability", fontsize=11)
    plt.ylabel("Fraction of Positives (Actual Churn)", fontsize=11)
    plt.title("Probability Calibration Curve (Reliability Diagram)", fontsize=13, pad=12)
    plt.legend(loc="upper left", frameon=True)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(charts_dir / "calibration_curve.png", dpi=200)
    plt.close()


def run_full_pipeline() -> None:
    """Executes the complete end-to-end customer retention intelligence pipeline."""
    start_time = datetime.datetime.now()
    logger.info("=================================================================")
    logger.info("Starting Customer Retention & Churn Intelligence Pipeline")
    logger.info("=================================================================")

    # 1. Load Configuration
    config = load_config("config/config.yaml")
    set_seed(config.get("project", {}).get("random_state", 42))

    # Ensure all target directories exist
    ensure_directories([
        config["paths"]["raw_data_dir"],
        config["paths"]["processed_data_dir"],
        config["paths"]["models_dir"],
        config["paths"]["metrics_dir"],
        config["paths"]["predictions_dir"],
        config["paths"]["shap_dir"],
        config["paths"]["charts_dir"],
        config["paths"]["reports_dir"],
        config["paths"]["powerbi_dir"],
    ])

    # 2. Ingest Raw Dataset
    raw_path = Path(config["paths"]["raw_csv"])
    if not raw_path.exists():
        download_raw_dataset(raw_path)
    df_raw = load_raw_data(raw_path)

    # 3. DuckDB SQL Layer Execution
    logger.info("Initializing DuckDB and running SQL analytical layer...")
    db_path = config["paths"]["duckdb_database"]
    with DuckDBManager(db_path) as db:
        # Load raw table
        db.load_raw_csv(raw_path)

        # Run SQL migration scripts in order
        sql_scripts = [
            "sql/schema/01_create_schemas.sql",
            "sql/staging/02_stg_customers.sql",
            "sql/analytics/03_churn_overview.sql",
            "sql/analytics/04_revenue_exposure.sql",
            "sql/cohorts/05_cohort_retention.sql",
            "sql/feature_engineering/06_features.sql",
            "sql/validation/07_data_quality_checks.sql",
        ]
        for script in sql_scripts:
            db.run_sql_script(script)

        # Run Quality Assertions
        quality_check_sql = "sql/validation/07_data_quality_checks.sql"
        pk_check = db.query_df("SELECT * FROM (SELECT COUNT(*) AS total, COUNT(DISTINCT customer_id) AS distinct_keys FROM staging.customers)")
        logger.info(f"Primary key uniqueness check: Total={pk_check['total'].iloc[0]}, Distinct={pk_check['distinct_keys'].iloc[0]}")

        # Retrieve cleaned staging data for analytical pipeline
        df_staged = db.query_df("SELECT * FROM staging.customers")

    # 4. Data Quality & Statistical Hypothesis Testing
    logger.info("Running Data Profiler and Statistical Hypothesis Tests...")
    profiler = DataProfiler(target_col="Churn", positive_val="Yes")
    quality_report = profiler.generate_quality_report(df_raw)
    save_json(quality_report, Path(config["paths"]["reports_dir"]) / "data_quality_report.json")

    stat_test_results = profiler.run_statistical_hypothesis_tests(df_staged)
    save_json(stat_test_results, Path(config["paths"]["reports_dir"]) / "statistical_tests.json")
    logger.info(f"Completed {len(stat_test_results)} statistical tests with Benjamini-Hochberg FDR correction.")

    # 5. Leakage-Safe Feature Engineering & Modeling
    logger.info("Building model pipeline and executing training...")
    trainer = ModelTrainer(config)
    X_train, X_test, y_train, y_test, num_feats, cat_feats = trainer.prepare_data(df_staged)

    comparison_results = trainer.train_and_compare(
        X_train, X_test, y_train, y_test, num_feats, cat_feats
    )
    trainer.save_artifacts(comparison_results)

    optimal_threshold = comparison_results["chosen_optimal_threshold"]

    # Generate Model Diagnostic Charts
    X_test_trans = trainer.preprocessor.transform(X_test)
    lr_probs = trainer.baseline_model.predict_proba(X_test_trans)[:, 1]
    xgb_probs = trainer.advanced_model.predict_proba(X_test_trans)[:, 1]
    charts_dir = Path(config["paths"]["charts_dir"])
    generate_diagnostic_plots(y_test, lr_probs, xgb_probs, optimal_threshold, charts_dir)

    # 6. SHAP TreeExplainer
    logger.info("Computing SHAP explanations (Global and Customer-level)...")
    explainer = ChurnExplainer(trainer.advanced_model, trainer.preprocessor, trainer.feature_names)
    _, importance_df = explainer.explain_dataset(
        X_test,
        output_dir=config["paths"]["shap_dir"],
        charts_dir=config["paths"]["charts_dir"],
    )

    # 7. Customer Risk Scoring, Expected Revenue at Risk, and Retention Prioritization
    logger.info("Scoring full customer population and allocating retention priorities...")
    prioritizer = RetentionPrioritizer(
        decision_threshold=optimal_threshold,
        risk_cutoffs=(0.25, 0.50, 0.75),
        high_value_percentile=75.0,
    )

    # Score full customer base
    engineer = DomainFeatureEngineer()
    full_transformed = engineer.transform(df_staged)
    drop_cols = [
        "customerID", "customer_id", "Churn", "churn_label", "churn_str",
        "tenure_cohort_group", "monthly_spend_tier"
    ]
    X_full = full_transformed.drop(columns=[c for c in drop_cols if c in full_transformed.columns], errors="ignore")
    X_full_trans = trainer.preprocessor.transform(X_full)
    all_probabilities = trainer.advanced_model.predict_proba(X_full_trans)[:, 1]

    scored_customers = prioritizer.score_customers(df_staged, all_probabilities)

    # Save Scored Datasets
    pred_dir = Path(config["paths"]["predictions_dir"])
    scored_customers.to_csv(pred_dir / "customer_risk_scores.csv", index=False)
    scored_customers.to_parquet(pred_dir / "customer_risk_scores.parquet", index=False)
    logger.info(f"Saved scored customer population ({len(scored_customers):,} records) to {pred_dir.resolve()}")

    # 8. Power BI Analytical Export
    logger.info("Exporting Power BI data assets...")
    pbi_dir = Path(config["paths"]["powerbi_dir"])
    scored_customers.to_csv(pbi_dir / "powerbi_customer_retention_dataset.csv", index=False)

    # Aggregate summaries for Power BI
    executive_kpis = {
        "total_active_customers": int(len(scored_customers)),
        "historical_churn_rate_pct": round(float(scored_customers["churn_label"].mean() * 100.0), 2),
        "customers_at_high_or_critical_risk": int(scored_customers["risk_segment"].isin(["High Risk", "Critical Risk"]).sum()),
        "total_monthly_revenue_exposure": round(float(scored_customers["monthly_revenue_exposure"].sum()), 2),
        "total_monthly_expected_revenue_at_risk": round(float(scored_customers["monthly_revenue_at_risk"].sum()), 2),
        "annualized_expected_revenue_at_risk": round(float(scored_customers["annual_revenue_at_risk"].sum()), 2),
        "tier_1_vip_retention_priority_count": int((scored_customers["retention_priority_tier"] == "Tier 1: VIP Urgent Outreach").sum()),
        "tier_1_monthly_revenue_at_risk": round(
            float(scored_customers.loc[scored_customers["retention_priority_tier"] == "Tier 1: VIP Urgent Outreach", "monthly_revenue_at_risk"].sum()), 2
        ),
    }
    save_json(executive_kpis, pbi_dir / "executive_kpis_summary.json")

    # Ingest scored customers back into DuckDB for fast ad-hoc SQL querying
    with DuckDBManager(db_path) as db:
        db.conn.execute("""
            CREATE OR REPLACE TABLE analytics.customer_risk_scored AS
            SELECT * FROM read_csv_auto('outputs/predictions/customer_risk_scores.csv');
        """)
        logger.info("Ingested analytics.customer_risk_scored table into DuckDB.")

    elapsed = datetime.datetime.now() - start_time
    logger.info("=================================================================")
    logger.info(f"Pipeline Execution Successfully Completed in {elapsed.total_seconds():.2f} seconds.")
    logger.info(f"High/Critical Risk Customers: {executive_kpis['customers_at_high_or_critical_risk']:,}")
    logger.info(f"Monthly Expected Revenue-at-Risk: ${executive_kpis['total_monthly_expected_revenue_at_risk']:,.2f}")
    logger.info(f"Annualized Expected Revenue-at-Risk: ${executive_kpis['annualized_expected_revenue_at_risk']:,.2f}")
    logger.info("=================================================================")


if __name__ == "__main__":
    run_full_pipeline()
