"""Customer Retention & Churn Intelligence - Interactive Streamlit Web Application.

Provides:
- Executive Risk & Revenue Exposure Dashboard
- Customer 360 Risk Lookup with Local SHAP Explanations
- Model Performance, Calibration & Threshold Optimization
- 2x2 Retention Prioritization Matrix & Action Playbook
"""

from __future__ import annotations

from pathlib import Path
import sys

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import joblib
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from src.explainability.explainer import ChurnExplainer
from src.features.builder import DomainFeatureEngineer
from src.utils.helpers import load_json

st.set_page_config(
    page_title="Customer Retention & Churn Intelligence",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for executive aesthetic
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 16px;
        border-left: 5px solid #1f77b4;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .badge-critical { background-color: #ffebee; color: #c62828; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    .badge-high { background-color: #fff3e0; color: #ef6c00; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    .badge-medium { background-color: #fffde7; color: #f57f17; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    .badge-low { background-color: #e8f5e9; color: #2e7d32; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_datasets():
    csv_path = Path("outputs/predictions/customer_risk_scores.csv")
    if not csv_path.exists():
        st.error("Predictions file not found. Please run `python scripts/run_pipeline.py` first.")
        st.stop()
    df = pd.read_csv(csv_path)
    metadata = load_json("models/model_metadata.json")
    kpis = load_json("outputs/powerbi/executive_kpis_summary.json")
    shap_importance = load_json("outputs/shap/global_shap_importance.json")
    return df, metadata, kpis, shap_importance


@st.cache_resource
def load_model_pipeline() -> ChurnExplainer:
    model = joblib.load("models/churn_model.joblib")
    preprocessor = joblib.load("models/preprocessing_pipeline.joblib")
    metadata = load_json("models/model_metadata.json")
    feature_names = metadata["feature_names"]
    return ChurnExplainer(model, preprocessor, feature_names)


df_customers, metadata, kpis, shap_importance = load_datasets()
explainer = load_model_pipeline()

# Sidebar Navigation
st.sidebar.title("🎯 Retention Platform")
st.sidebar.caption("End-to-End Customer Churn Intelligence")
page = st.sidebar.radio(
    "Navigation",
    [
        "Executive Overview",
        "Customer Risk 360 & SHAP",
        "Model Governance & Metrics",
        "Retention Prioritization Matrix",
    ],
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Decision Threshold:** `0.30`")
st.sidebar.markdown("**Optimal Metric:** PR-AUC")
st.sidebar.markdown(f"**Total Base:** {len(df_customers):,} Subscribers")

# -------------------------------------------------------------
# PAGE 1: EXECUTIVE OVERVIEW
# -------------------------------------------------------------
if page == "Executive Overview":
    st.title("📊 Executive Retention & Revenue Risk Dashboard")
    st.caption("Quantifying customer vulnerability and expected revenue-at-risk across recurring subscription tiers.")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="Total Active Subscribers",
            value=f"{kpis['total_active_customers']:,}",
            help="Total customers tracked in the billing catalog.",
        )
    with col2:
        st.metric(
            label="Historical Churn Rate",
            value=f"{kpis['historical_churn_rate_pct']:.2f}%",
            delta="-1.4% vs benchmark",
            delta_color="inverse",
        )
    with col3:
        st.metric(
            label="High / Critical Risk Base",
            value=f"{kpis['customers_at_high_or_critical_risk']:,}",
            delta=f"{kpis['customers_at_high_or_critical_risk']/kpis['total_active_customers']*100:.1f}% of total",
            delta_color="off",
        )
    with col4:
        st.metric(
            label="Monthly Revenue at Risk",
            value=f"${kpis['total_monthly_expected_revenue_at_risk']:,.2f}",
            delta=f"${kpis['annualized_expected_revenue_at_risk']:,.2f}/yr",
            delta_color="off",
        )

    st.markdown("---")

    # Filters
    st.subheader("Segment Deep-Dive Filters")
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        sel_contract = st.multiselect(
            "Contract Type",
            options=df_customers["contract_type"].unique().tolist(),
            default=df_customers["contract_type"].unique().tolist(),
        )
    with f_col2:
        sel_internet = st.multiselect(
            "Internet Service",
            options=df_customers["internet_service"].unique().tolist(),
            default=df_customers["internet_service"].unique().tolist(),
        )
    with f_col3:
        sel_risk = st.multiselect(
            "Risk Segment",
            options=["Low Risk", "Medium Risk", "High Risk", "Critical Risk"],
            default=["High Risk", "Critical Risk"],
        )

    filtered_df = df_customers[
        (df_customers["contract_type"].isin(sel_contract))
        & (df_customers["internet_service"].isin(sel_internet))
        & (df_customers["risk_segment"].isin(sel_risk))
    ]

    st.markdown(f"**Filtered Cohort Size:** {len(filtered_df):,} customers | **Cohort Monthly Revenue Exposure:** ${filtered_df['monthly_revenue_exposure'].sum():,.2f}")

    # Charts
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown("#### Risk Distribution Breakdown")
        risk_counts = df_customers["risk_segment"].value_counts()
        st.bar_chart(risk_counts, color="#1f77b4")

    with chart_col2:
        st.markdown("#### Monthly Expected Revenue-at-Risk by Priority Tier")
        tier_rev = df_customers.groupby("retention_priority_tier")["monthly_revenue_at_risk"].sum()
        st.bar_chart(tier_rev, color="#ff7f0e")

# -------------------------------------------------------------
# PAGE 2: CUSTOMER RISK 360 & SHAP
# -------------------------------------------------------------
elif page == "Customer Risk 360 & SHAP":
    st.title("🔍 Customer 360 Risk Profile & SHAP Explainability")
    st.caption("Inspect individual subscriber risk factors, predictive drivers, and tailored retention intervention playbooks.")

    # High risk selector across full customer cohort
    high_risk_ids = df_customers.sort_values(by="churn_probability", ascending=False)["customer_id"].tolist()
    selected_cust_id = st.selectbox(
        "Select Customer ID (ordered from highest to lowest predicted churn risk):",
        options=high_risk_ids,
        index=0,
        help="Search or select any customer ID across the entire 7,043 subscriber cohort."
    )

    cust_row = df_customers[df_customers["customer_id"] == selected_cust_id].iloc[0]

    c_col1, c_col2, c_col3, c_col4 = st.columns(4)
    with c_col1:
        prob = cust_row["churn_probability"]
        st.metric("Predicted Churn Probability", f"{prob*100:.1f}%")
    with c_col2:
        st.metric("Risk Segment", cust_row["risk_segment"])
    with c_col3:
        st.metric("Monthly Revenue Exposure", f"${cust_row['monthly_revenue_exposure']:.2f}")
    with c_col4:
        st.metric("Monthly Expected Revenue-at-Risk", f"${cust_row['monthly_revenue_at_risk']:.2f}")

    st.info(f"🎯 **Recommended Action:** {cust_row['recommended_action']}")

    # Customer Attributes Table (3-column responsive grid layout)
    st.subheader("Customer Characteristics")
    attr_col1, attr_col2, attr_col3 = st.columns(3)
    with attr_col1:
        st.write(f"**Tenure:** {cust_row.get('tenure_months', cust_row.get('tenure', 'N/A'))} months")
        st.write(f"**Contract:** {cust_row.get('contract_type', cust_row.get('Contract', 'N/A'))}")
        st.write(f"**Partner / Dependents:** {cust_row.get('Partner', 'N/A')} / {cust_row.get('Dependents', 'N/A')}")
    with attr_col2:
        st.write(f"**Internet Service:** {cust_row.get('internet_service', cust_row.get('InternetService', 'N/A'))}")
        st.write(f"**Payment Method:** {cust_row.get('payment_method', cust_row.get('PaymentMethod', 'N/A'))}")
        st.write(f"**Paperless Billing:** {cust_row.get('PaperlessBilling', 'N/A')}")
    with attr_col3:
        st.write(f"**Priority Tier:** {cust_row['retention_priority_tier']}")
        st.write(f"**Observed Top Driver:** {cust_row['top_risk_driver']}")
        st.write(f"**Add-on Services:** {cust_row.get('addon_services_count', 'N/A')} active bundles")

    # SHAP Local Explanation
    st.subheader("Explainable AI (SHAP) - Individual Feature Attribution")
    st.caption("Features pushing risk upward (red/positive) versus protective factors pushing risk downward (blue/negative). Note: SHAP reflects model predictive association, not causal proof.")

    # Reconstruct single feature row
    cust_df = pd.DataFrame([cust_row])
    engineer = DomainFeatureEngineer()
    cust_transformed = engineer.transform(cust_df)
    drop_cols = [
        "customerID", "customer_id", "Churn", "churn_label", "churn_str",
        "tenure_cohort_group", "monthly_spend_tier", "predicted_churn_flag",
        "churn_probability", "monthly_revenue_exposure", "annual_revenue_exposure",
        "monthly_revenue_at_risk", "annual_revenue_at_risk", "customer_value_tier",
        "retention_priority_tier", "top_risk_driver", "recommended_action", "risk_segment"
    ]
    X_single = cust_transformed.drop(columns=[c for c in drop_cols if c in cust_transformed.columns], errors="ignore")

    explanation = explainer.explain_single_customer(X_single)
    contrib_df = pd.DataFrame(explanation["detailed_contributions"])

    # Plot local horizontal bar chart
    fig, ax = plt.subplots(figsize=(9, 4.5))
    colors = ["#d62728" if v > 0 else "#1f77b4" for v in contrib_df["shap_value"]]
    ax.barh(contrib_df["feature"], contrib_df["shap_value"], color=colors)
    ax.axvline(0, color="black", linestyle="--", alpha=0.5)
    ax.set_xlabel("SHAP Impact on Predicted Churn Risk (Log-odds Margin)")
    ax.invert_yaxis()
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

# -------------------------------------------------------------
# PAGE 3: MODEL GOVERNANCE & METRICS
# -------------------------------------------------------------
elif page == "Model Governance & Metrics":
    st.title("⚙️ Model Governance, Evaluation & Validation")
    st.caption("Leakage-safe validation, benchmark comparisons, and probability calibration.")

    metrics_data = metadata.get("metrics", {})
    lr_metrics = metrics_data.get("Logistic_Regression_Baseline", {})
    xgb_metrics = metrics_data.get("XGBoost_Advanced", {})
    xgb_opt = metrics_data.get("XGBoost_Optimal_Threshold", {})

    st.subheader("Model Comparison Scorecard (Held-Out Test Set)")
    comp_df = pd.DataFrame([
        {
            "Model": "Logistic Regression Baseline",
            "Threshold": lr_metrics.get("threshold", 0.50),
            "ROC-AUC": lr_metrics.get("roc_auc", 0.0),
            "PR-AUC": lr_metrics.get("pr_auc", 0.0),
            "Precision": lr_metrics.get("precision", 0.0),
            "Recall": lr_metrics.get("recall", 0.0),
            "F1-Score": lr_metrics.get("f1", 0.0),
            "Brier Score": lr_metrics.get("brier_score", 0.0),
        },
        {
            "Model": "XGBoost (Default 0.50)",
            "Threshold": xgb_metrics.get("threshold", 0.50),
            "ROC-AUC": xgb_metrics.get("roc_auc", 0.0),
            "PR-AUC": xgb_metrics.get("pr_auc", 0.0),
            "Precision": xgb_metrics.get("precision", 0.0),
            "Recall": xgb_metrics.get("recall", 0.0),
            "F1-Score": xgb_metrics.get("f1", 0.0),
            "Brier Score": xgb_metrics.get("brier_score", 0.0),
        },
        {
            "Model": "XGBoost (Optimized Threshold)",
            "Threshold": xgb_opt.get("threshold", 0.30),
            "ROC-AUC": xgb_opt.get("roc_auc", 0.0),
            "PR-AUC": xgb_opt.get("pr_auc", 0.0),
            "Precision": xgb_opt.get("precision", 0.0),
            "Recall": xgb_opt.get("recall", 0.0),
            "F1-Score": xgb_opt.get("f1", 0.0),
            "Brier Score": xgb_opt.get("brier_score", 0.0),
        },
    ])
    st.dataframe(comp_df, use_container_width=True)

    st.markdown("---")
    st.subheader("Model Diagnostic Curves")
    diag_col1, diag_col2, diag_col3 = st.columns(3)
    with diag_col1:
        roc_img = Path("outputs/charts/roc_curve_comparison.png")
        if roc_img.exists():
            st.image(str(roc_img), caption="ROC Curves (Discrimination Capacity)")
    with diag_col2:
        pr_img = Path("outputs/charts/precision_recall_comparison.png")
        if pr_img.exists():
            st.image(str(pr_img), caption="Precision-Recall Curve (Minority Class)")
    with diag_col3:
        calib_img = Path("outputs/charts/calibration_curve.png")
        if calib_img.exists():
            st.image(str(calib_img), caption="Probability Calibration Curve")

    st.markdown("---")
    st.subheader("Global Feature Importance (SHAP)")
    shap_img = Path("outputs/charts/shap_summary_plot.png")
    if shap_img.exists():
        st.image(str(shap_img), caption="SHAP Summary Plot (Top Predictive Associations)")

    st.markdown("#### Global Feature Importance Rankings")
    st.dataframe(pd.DataFrame(shap_importance).head(15), use_container_width=True)

# -------------------------------------------------------------
# PAGE 4: RETENTION PRIORITIZATION MATRIX
# -------------------------------------------------------------
elif page == "Retention Prioritization Matrix":
    st.title("🎯 Retention Prioritization Matrix & Action Playbook")
    st.caption("Optimizing limited Customer Success capacity by aligning predictive risk with customer revenue exposure.")

    st.markdown("""
    ```
                      Customer Revenue Exposure
                  Standard Value            High Value (Top 25%)
    Risk High   │ Tier 2: Automated Campaign │ Tier 1: Urgent VIP Outreach │
    Risk Low    │ Tier 4: Standard Operation │ Tier 3: Proactive Care      │
    ```
    """)

    matrix_counts = df_customers.groupby(["retention_priority_tier"]).agg(
        Total_Customers=("customer_id", "count"),
        Monthly_Revenue_Exposure=("monthly_revenue_exposure", "sum"),
        Monthly_Revenue_at_Risk=("monthly_revenue_at_risk", "sum"),
        Avg_Churn_Probability=("churn_probability", "mean"),
    ).reset_index()

    matrix_counts["Avg_Churn_Probability"] = (matrix_counts["Avg_Churn_Probability"] * 100.0).round(1).astype(str) + "%"
    matrix_counts["Monthly_Revenue_Exposure"] = matrix_counts["Monthly_Revenue_Exposure"].apply(lambda x: f"${x:,.2f}")
    matrix_counts["Monthly_Revenue_at_Risk"] = matrix_counts["Monthly_Revenue_at_Risk"].apply(lambda x: f"${x:,.2f}")

    st.subheader("Priority Tier Resource Allocation Summary")
    st.dataframe(matrix_counts, use_container_width=True)

    st.markdown("---")
    priority_mask = df_customers["retention_priority_tier"].isin([
        "Tier 1: VIP Urgent Outreach", "Tier 2: Automated Campaign Offer"
    ])
    selected_cols = [
        "customer_id", "retention_priority_tier", "risk_segment", "churn_probability",
        "monthly_revenue_exposure", "monthly_revenue_at_risk", "top_risk_driver", "recommended_action"
    ]
    export_df = df_customers.loc[priority_mask, selected_cols].sort_values(
        by="monthly_revenue_at_risk", ascending=False
    )

    st.dataframe(export_df.head(25), use_container_width=True)

    csv_data = export_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Priority Outreach List (CSV)",
        data=csv_data,
        file_name="priority_retention_outreach.csv",
        mime="text/csv",
    )
