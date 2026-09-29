"""Data loading, acquisition, and local storage utilities for Customer Retention & Churn Intelligence."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
import urllib.request

import pandas as pd

from src.utils.helpers import setup_logger

logger = setup_logger(__name__)

PRIMARY_DATASET_URL = (
    "https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv"
)
FALLBACK_DATASET_URL = (
    "https://raw.githubusercontent.com/treselle-systems/customer_churn_analysis/master/WA_Fn-UseC_-Telco-Customer-Churn.csv"
)

EXPECTED_COLUMNS = [
    "customerID",
    "gender",
    "SeniorCitizen",
    "Partner",
    "Dependents",
    "tenure",
    "PhoneService",
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "Contract",
    "PaperlessBilling",
    "PaymentMethod",
    "MonthlyCharges",
    "TotalCharges",
    "Churn",
]


def download_raw_dataset(
    target_path: str | Path = "data/raw/Telco-Customer-Churn.csv",
    force_download: bool = False,
) -> Path:
    """Downloads the Telco Customer Churn dataset if not already present."""
    dest = Path(target_path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists() and not force_download and dest.stat().st_size > 1000:
        logger.info(f"Raw dataset already exists at: {dest.resolve()} ({dest.stat().st_size:,} bytes)")
        return dest

    logger.info(f"Downloading Telco Customer Churn dataset to: {dest.resolve()}...")
    urls = [PRIMARY_DATASET_URL, FALLBACK_DATASET_URL]
    last_err: Optional[Exception] = None

    for url in urls:
        try:
            logger.info(f"Attempting download from: {url}")
            urllib.request.urlretrieve(url, dest)
            if dest.exists() and dest.stat().st_size > 1000:
                logger.info(f"Successfully downloaded {dest.stat().st_size:,} bytes.")
                return dest
        except Exception as e:
            logger.warning(f"Download failed from {url}: {e}")
            last_err = e

    raise RuntimeError(f"Failed to download dataset from all sources. Error: {last_err}")


def load_raw_data(filepath: str | Path = "data/raw/Telco-Customer-Churn.csv") -> pd.DataFrame:
    """Loads raw CSV data with initial type preservation and logging."""
    path = Path(filepath)
    if not path.exists():
        download_raw_dataset(path)

    df = pd.read_csv(path)
    logger.info(f"Loaded raw dataset with shape: {df.shape[0]:,} rows x {df.shape[1]} columns")

    missing_cols = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Dataset missing required columns: {missing_cols}")

    return df
