"""DuckDB Database connector and SQL query engine for Customer Retention & Churn Intelligence."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import duckdb
import pandas as pd

from src.utils.helpers import setup_logger

logger = setup_logger(__name__)

DEFAULT_DB_PATH = Path("data/processed/customer_retention.duckdb")


class DuckDBManager:
    """Manages DuckDB connections, schema creation, raw ingestion, and analytical queries."""

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = duckdb.connect(database=str(self.db_path), read_only=False)
        logger.info(f"Connected to DuckDB at: {self.db_path.resolve()}")

    def close(self) -> None:
        """Closes active database connection."""
        if self.conn:
            self.conn.close()
            logger.info("DuckDB connection closed.")

    def __enter__(self) -> DuckDBManager:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def execute(self, query: str, parameters: Optional[list | dict] = None) -> duckdb.DuckDBPyConnection:
        """Executes a SQL statement."""
        if parameters:
            return self.conn.execute(query, parameters)
        return self.conn.execute(query)

    def query_df(self, query: str, parameters: Optional[list | dict] = None) -> pd.DataFrame:
        """Executes a query and returns a pandas DataFrame."""
        if parameters:
            return self.conn.execute(query, parameters).df()
        return self.conn.execute(query).df()

    def run_sql_script(self, script_path: str | Path) -> None:
        """Reads and executes all SQL statements in a script file."""
        path = Path(script_path)
        if not path.exists():
            raise FileNotFoundError(f"SQL file not found at: {path.resolve()}")
        sql = path.read_text(encoding="utf-8")
        self.conn.execute(sql)
        logger.info(f"Executed SQL script: {path.name}")

    def initialize_schemas(self) -> None:
        """Creates the logical schemas in DuckDB."""
        self.conn.execute("CREATE SCHEMA IF NOT EXISTS raw;")
        self.conn.execute("CREATE SCHEMA IF NOT EXISTS staging;")
        self.conn.execute("CREATE SCHEMA IF NOT EXISTS analytics;")
        logger.info("Schemas initialized: raw, staging, analytics")

    def load_raw_csv(self, csv_path: str | Path = "data/raw/Telco-Customer-Churn.csv") -> int:
        """Ingests raw CSV directly into raw.customers table."""
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(f"Raw CSV not found at: {path.resolve()}")

        self.initialize_schemas()

        # Ingest raw CSV as text/variant table to preserve raw fidelity
        ingest_sql = f"""
            CREATE OR REPLACE TABLE raw.customers AS
            SELECT * FROM read_csv_auto('{path.as_posix()}', all_varchar=True);
        """
        self.conn.execute(ingest_sql)
        row_count = self.conn.execute("SELECT COUNT(*) FROM raw.customers").fetchone()[0]
        logger.info(f"Loaded raw.customers with {row_count:,} records.")
        return row_count
