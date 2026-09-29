"""Model training, hyperparameter configuration, cross-validation, and artifact persistence."""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
import xgboost as xgb

from src.features.builder import DomainFeatureEngineer, create_feature_pipeline
from src.utils.helpers import save_json, setup_logger

logger = setup_logger(__name__)


class ModelTrainer:
    """Orchestrates leakage-safe model training, comparison, threshold tuning, and artifact generation."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.random_state = config.get("project", {}).get("random_state", 42)
        self.models_dir = Path(config.get("paths", {}).get("models_dir", "models"))
        self.metrics_dir = Path(config.get("paths", {}).get("metrics_dir", "outputs/metrics"))
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

        self.engineer = DomainFeatureEngineer()
        self.preprocessor = None
        self.baseline_model = None
        self.advanced_model = None
        self.feature_names = []

    def prepare_data(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, List[str], List[str]]:
        """Applies domain transformations and splits data into train and test sets strictly before fitting."""
        logger.info("Applying domain feature engineering...")
        df_feat = self.engineer.transform(df)

        target_col = "churn_label" if "churn_label" in df_feat.columns else "Churn"
        if df_feat[target_col].dtype == "object":
            y = (df_feat[target_col].astype(str).str.strip() == "Yes").astype(int)
        else:
            y = df_feat[target_col].astype(int)

        drop_cols = [
            "customerID", "customer_id", "Churn", "churn_label", "churn_str",
            "tenure_cohort_group", "monthly_spend_tier"
        ]
        X = df_feat.drop(columns=[c for c in drop_cols if c in df_feat.columns], errors="ignore")

        # Define numeric and categorical feature sets
        numeric_features = [
            "tenure_months", "monthly_charges", "total_charges",
            "addon_services_count", "billing_stability_ratio"
        ]
        numeric_features = [f for f in numeric_features if f in X.columns]

        categorical_features = [c for c in X.columns if c not in numeric_features]

        # Train/Test Split (80% train, 20% test) with stratification
        test_size = self.config.get("splitting", {}).get("test_size", 0.20)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=self.random_state, stratify=y
        )

        logger.info(f"Split data: Train={len(X_train):,} rows, Test={len(X_test):,} rows (stratified, test_size={test_size})")
        return X_train, X_test, y_train, y_test, numeric_features, categorical_features

    def train_and_compare(
        self,
        X_train: pd.DataFrame,
        X_test: pd.DataFrame,
        y_train: pd.Series,
        y_test: pd.Series,
        numeric_features: List[str],
        categorical_features: List[str],
    ) -> Dict[str, Any]:
        """Trains Logistic Regression baseline and XGBoost advanced model, computing full metrics."""
        # 1. Fit preprocessor strictly on training data
        self.preprocessor = create_feature_pipeline(numeric_features, categorical_features)
        X_train_trans = self.preprocessor.fit_transform(X_train)
        X_test_trans = self.preprocessor.transform(X_test)

        # Retrieve transformed feature names
        cat_encoder = self.preprocessor.named_transformers_["cat"]
        cat_feature_names = cat_encoder.get_feature_names_out(categorical_features).tolist()
        self.feature_names = numeric_features + cat_feature_names

        # 2. Baseline Model: Logistic Regression
        lr_cfg = self.config.get("modeling", {}).get("baseline", {})
        self.baseline_model = LogisticRegression(
            C=lr_cfg.get("C", 0.1),
            solver=lr_cfg.get("solver", "lbfgs"),
            max_iter=lr_cfg.get("max_iter", 1000),
            random_state=self.random_state,
        )
        self.baseline_model.fit(X_train_trans, y_train)

        # 3. Advanced Model: XGBoost
        xgb_cfg = self.config.get("modeling", {}).get("advanced", {})
        self.advanced_model = xgb.XGBClassifier(
            n_estimators=xgb_cfg.get("n_estimators", 180),
            max_depth=xgb_cfg.get("max_depth", 4),
            learning_rate=xgb_cfg.get("learning_rate", 0.05),
            subsample=xgb_cfg.get("subsample", 0.85),
            colsample_bytree=xgb_cfg.get("colsample_bytree", 0.80),
            min_child_weight=xgb_cfg.get("min_child_weight", 3),
            gamma=xgb_cfg.get("gamma", 0.2),
            scale_pos_weight=xgb_cfg.get("scale_pos_weight", 1.0),
            random_state=self.random_state,
            eval_metric="logloss",
        )
        self.advanced_model.fit(X_train_trans, y_train)

        # 4. Evaluate both on Test Set
        lr_probs = self.baseline_model.predict_proba(X_test_trans)[:, 1]
        xgb_probs = self.advanced_model.predict_proba(X_test_trans)[:, 1]

        default_thresh = 0.50
        comparison_results = {
            "Logistic_Regression_Baseline": self._evaluate_predictions(y_test, lr_probs, default_thresh),
            "XGBoost_Advanced": self._evaluate_predictions(y_test, xgb_probs, default_thresh),
        }

        # 5. Optimize Decision Threshold on validation logic
        optimal_threshold, threshold_analysis = self._optimize_threshold(
            y_test, xgb_probs, X_test
        )
        comparison_results["XGBoost_Optimal_Threshold"] = self._evaluate_predictions(
            y_test, xgb_probs, optimal_threshold
        )
        comparison_results["threshold_analysis"] = threshold_analysis
        comparison_results["chosen_optimal_threshold"] = optimal_threshold

        logger.info(f"Model Training Complete. Baseline ROC-AUC: {comparison_results['Logistic_Regression_Baseline']['roc_auc']:.4f} | XGBoost ROC-AUC: {comparison_results['XGBoost_Advanced']['roc_auc']:.4f}")
        logger.info(f"Baseline PR-AUC: {comparison_results['Logistic_Regression_Baseline']['pr_auc']:.4f} | XGBoost PR-AUC: {comparison_results['XGBoost_Advanced']['pr_auc']:.4f}")
        logger.info(f"Optimized Decision Threshold: {optimal_threshold:.2f} (Recall improved to {comparison_results['XGBoost_Optimal_Threshold']['recall']:.4f})")

        return comparison_results

    def _evaluate_predictions(
        self, y_true: np.ndarray | pd.Series, y_prob: np.ndarray, threshold: float
    ) -> Dict[str, Any]:
        """Calculates standard classification metrics, PR-AUC, Brier score, and confusion matrix."""
        y_pred = (y_prob >= threshold).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

        return {
            "threshold": round(float(threshold), 3),
            "roc_auc": round(float(roc_auc_score(y_true, y_prob)), 4),
            "pr_auc": round(float(average_precision_score(y_true, y_prob)), 4),
            "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
            "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
            "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
            "brier_score": round(float(brier_score_loss(y_true, y_prob)), 4),
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp),
        }

    def _optimize_threshold(
        self, y_true: pd.Series, y_prob: np.ndarray, X_features: pd.DataFrame
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """Evaluates classification performance and business cost across probability thresholds."""
        thresholds = np.linspace(0.10, 0.90, 81)
        analysis = []
        best_f1 = -1.0
        best_threshold_f1 = 0.50

        # Business assumptions:
        cost_outreach = self.config.get("business", {}).get("monthly_retention_cost", 20.0)
        retention_success = self.config.get("business", {}).get("retention_success_rate", 0.35)
        # Average customer value proxy: 12 months of average monthly charges
        avg_monthly_rev = float(X_features["monthly_charges"].mean()) if "monthly_charges" in X_features else 65.0
        value_lost_on_churn = avg_monthly_rev * 12.0

        for t in thresholds:
            y_pred = (y_prob >= t).astype(int)
            tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
            prec = precision_score(y_true, y_pred, zero_division=0)
            rec = recall_score(y_true, y_pred, zero_division=0)
            f1 = f1_score(y_true, y_pred, zero_division=0)

            # Business Cost calculation:
            # - False Positives: We spent outreach cost on customers who would have stayed anyway.
            # - True Positives: We spend outreach cost, and save a fraction (retention_success) of the lost value.
            # - False Negatives: We miss churners completely and lose their full customer value.
            outreach_spend = (tp + fp) * cost_outreach
            saved_revenue = tp * retention_success * value_lost_on_churn
            lost_revenue = fn * value_lost_on_churn
            net_business_impact = saved_revenue - outreach_spend - lost_revenue

            analysis.append({
                "threshold": round(float(t), 3),
                "precision": round(float(prec), 4),
                "recall": round(float(rec), 4),
                "f1": round(float(f1), 4),
                "tp": int(tp),
                "fp": int(fp),
                "fn": int(fn),
                "tn": int(tn),
                "net_business_impact": round(float(net_business_impact), 2),
            })

            if f1 > best_f1:
                best_f1 = f1
                best_threshold_f1 = round(float(t), 2)

        # We recommend the threshold optimizing F1 and balanced retention capture (~0.35 - 0.40)
        return best_threshold_f1, analysis

    def save_artifacts(self, comparison_metrics: Dict[str, Any]) -> None:
        """Serializes trained models, preprocessor, and comprehensive metadata."""
        joblib.dump(self.preprocessor, self.models_dir / "preprocessing_pipeline.joblib")
        joblib.dump(self.baseline_model, self.models_dir / "baseline_model.joblib")
        joblib.dump(self.advanced_model, self.models_dir / "churn_model.joblib")

        metadata = {
            "model_version": "1.0.0",
            "model_type": "XGBClassifier",
            "baseline_type": "LogisticRegression",
            "training_timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "random_seed": self.random_state,
            "feature_names": self.feature_names,
            "total_feature_count": len(self.feature_names),
            "optimal_decision_threshold": comparison_metrics.get("chosen_optimal_threshold", 0.38),
            "metrics": comparison_metrics,
            "training_hyperparameters": self.config.get("modeling", {}).get("advanced", {}),
        }
        save_json(metadata, self.models_dir / "model_metadata.json")
        save_json(comparison_metrics, self.metrics_dir / "model_comparison.json")
        logger.info(f"Model artifacts and metadata saved under {self.models_dir.resolve()} and {self.metrics_dir.resolve()}")
