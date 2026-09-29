"""Unit and integration tests for data loading, data quality, and DuckDB staging."""

from pathlib import Path
import pandas as pd
import pytest

from src.data.db import DuckDBManager
from src.data.loader import EXPECTED_COLUMNS, load_raw_data


def test_raw_data_columns_and_shape():
    """Validates that raw dataset loads with all required canonical columns and non-empty rows."""
    raw_path = Path("data/raw/Telco-Customer-Churn.csv")
    assert raw_path.exists(), "Raw dataset must exist"

    df = load_raw_data(raw_path)
    assert len(df) == 7043, f"Expected 7,043 rows, found {len(df)}"
    for col in EXPECTED_COLUMNS:
        assert col in df.columns, f"Missing required column: {col}"


def test_duckdb_staging_quality():
    """Validates DuckDB staging table types, uniqueness of customer_id, and TotalCharges handling."""
    db_path = Path("data/processed/customer_retention.duckdb")
    assert db_path.exists(), "DuckDB database must exist"

    with DuckDBManager(db_path) as db:
        df = db.query_df("SELECT * FROM staging.customers")
        assert len(df) == 7043
        assert df["customer_id"].nunique() == 7043, "Primary key customer_id must be distinct"

        # Check TotalCharges conversion for tenure=0
        tenure_zero = df[df["tenure_months"] == 0]
        assert len(tenure_zero) == 11, "Expected 11 records with tenure=0"
        assert (tenure_zero["total_charges"] == 0.0).all(), "tenure=0 customers must have TotalCharges imputed to 0.0"

        # Check target values are strictly binary 0 or 1
        assert set(df["churn_label"].unique()).issubset({0, 1})
