"""Script to export and refresh Power BI analytical assets and schemas."""

from pathlib import Path
import pandas as pd
from src.data.db import DuckDBManager
from src.utils.helpers import setup_logger

logger = setup_logger("export_powerbi")


def export_powerbi_tables():
    output_dir = Path("outputs/powerbi")
    output_dir.mkdir(parents=True, exist_ok=True)
    db_path = "data/processed/customer_retention.duckdb"

    with DuckDBManager(db_path) as db:
        logger.info("Extracting analytical views for Power BI reporting...")

        # 1. Main Scored Customer Table
        df_scored = db.query_df("SELECT * FROM analytics.customer_risk_scored")
        df_scored.to_csv(output_dir / "powerbi_customer_retention_dataset.csv", index=False)

        # 2. Executive Summary View
        df_exec = db.query_df("SELECT * FROM analytics.v_executive_summary")
        df_exec.to_csv(output_dir / "v_executive_summary.csv", index=False)

        # 3. Churn by Contract
        df_contract = db.query_df("SELECT * FROM analytics.v_churn_by_contract")
        df_contract.to_csv(output_dir / "v_churn_by_contract.csv", index=False)

        # 4. Cohort Retention Matrix
        df_cohort = db.query_df("SELECT * FROM analytics.v_cohort_retention_matrix")
        df_cohort.to_csv(output_dir / "v_cohort_retention_matrix.csv", index=False)

        # 5. Revenue Exposure by Segment
        df_rev = db.query_df("SELECT * FROM analytics.v_revenue_exposure_by_segment")
        df_rev.to_csv(output_dir / "v_revenue_exposure_by_segment.csv", index=False)

    logger.info(f"Successfully exported 5 Power BI tables to {output_dir.resolve()}")


if __name__ == "__main__":
    export_powerbi_tables()
