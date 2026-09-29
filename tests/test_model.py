"""Unit tests for model loading, predictions, and calibration range."""

from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import pytest

from src.features.builder import DomainFeatureEngineer
from src.utils.helpers import load_json


def test_model_artifacts_exist_and_load():
    """Validates serialized model files, preprocessor, and metadata schema."""
    models_dir = Path("models")
    assert (models_dir / "churn_model.joblib").exists()
    assert (models_dir / "baseline_model.joblib").exists()
    assert (models_dir / "preprocessing_pipeline.joblib").exists()
    assert (models_dir / "model_metadata.json").exists()

    model = joblib.load(models_dir / "churn_model.joblib")
    preprocessor = joblib.load(models_dir / "preprocessing_pipeline.joblib")
    metadata = load_json(models_dir / "model_metadata.json")

    assert hasattr(model, "predict_proba"), "Model must implement predict_proba"
    assert "metrics" in metadata
    assert "optimal_decision_threshold" in metadata
    assert 0.10 <= metadata["optimal_decision_threshold"] <= 0.90


def test_prediction_probabilities_validity():
    """Validates that loaded pipeline produces bounded [0, 1] probabilities on unseen input."""
    models_dir = Path("models")
    model = joblib.load(models_dir / "churn_model.joblib")
    preprocessor = joblib.load(models_dir / "preprocessing_pipeline.joblib")

    # Load a small test slice from staged customer table
    from src.data.db import DuckDBManager
    with DuckDBManager("data/processed/customer_retention.duckdb") as db:
        df = db.query_df("SELECT * FROM staging.customers LIMIT 10")

    engineer = DomainFeatureEngineer()
    df_feat = engineer.transform(df)
    drop_cols = [
        "customerID", "customer_id", "Churn", "churn_label", "churn_str",
        "tenure_cohort_group", "monthly_spend_tier"
    ]
    X = df_feat.drop(columns=[c for c in drop_cols if c in df_feat.columns], errors="ignore")

    X_trans = preprocessor.transform(X)
    probs = model.predict_proba(X_trans)[:, 1]

    assert len(probs) == 10
    assert (probs >= 0.0).all() and (probs <= 1.0).all(), "Probabilities must be within [0.0, 1.0]"
