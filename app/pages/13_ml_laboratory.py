"""
FinSight AI - Machine Learning Laboratory & MLflow Tracking
Experiment run comparisons, hyperparameter audits, test metric rankings, and model versions.
"""
import streamlit as st
import pandas as pd
from app.components.header import render_global_header
from app.components.kpi_card import render_kpi_card
from app.database.repository import Repository
from app.config import settings

def show():
    render_global_header("ML Experiments Laboratory & Registry", "MLflow-integrated model governance, hyperparameter tracking & out-of-sample test rankings")

    experiments = Repository.get_ml_experiments(limit=50)

    # Top KPI Cards
    reg_runs = sum(1 for e in experiments if e.get("task_type") == "REGRESSION")
    clf_runs = sum(1 for e in experiments if e.get("task_type") == "CLASSIFICATION")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card(
            label="Total Logged Runs",
            value=f"{len(experiments)} Runs",
            delta="MLflow Tracking Active",
            delta_type="positive",
            badge_text="EXPERIMENTS",
            badge_style="badge-live"
        )
    with k2:
        render_kpi_card(label="Regression Experiments", value=f"{reg_runs} Models", delta="Return forecasting", delta_type="neutral")
    with k3:
        render_kpi_card(label="Classification Experiments", value=f"{clf_runs} Models", delta="Direction prediction", delta_type="neutral")
    with k4:
        render_kpi_card(label="Storage Engine", value="SQLite / Postgres", delta=settings.MLFLOW_TRACKING_URI.split("/")[-1], delta_type="neutral")

    tab_runs, tab_mlflow_info = st.tabs(["Experiment Run Leaderboard", "MLflow Tracking Architecture"])

    with tab_runs:
        if experiments:
            rows = []
            for e in experiments:
                metrics = e.get("metrics", {})
                params = e.get("parameters", {})
                
                # Format primary metric
                score_str = f"R²: {metrics.get('r2', 0):.3f}" if e.get("task_type") == "REGRESSION" else f"Acc: {metrics.get('accuracy', 0)*100:.1f}%"
                
                rows.append({
                    "Run ID": e["run_id"][:18] + "...",
                    "Experiment": e["experiment"],
                    "Model": e["model_name"],
                    "Task": e["task_type"],
                    "Symbol": e["symbol"],
                    "Market": e["market"],
                    "Primary Score": score_str,
                    "Parameters": str(params),
                    "Logged At": e["created_at"].strftime("%Y-%m-%d %H:%M") if hasattr(e["created_at"], "strftime") else str(e["created_at"])[:16]
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("No training runs logged yet. Execute regression or classification in the Prediction Center to record experiment metadata.")

    with tab_mlflow_info:
        st.markdown("##### MLflow Architecture & Governance Policy")
        st.markdown(f"""
        - **Tracking URI:** `{settings.MLFLOW_TRACKING_URI}`
        - **Artifact Registry:** Model weights and serialized pipelines saved using standard Joblib with version hashing.
        - **Walk-Forward Policy:** Only models validated on strictly chronologically held-out test splits can be registered for production predictions.
        """)

if __name__ == "__main__":
    show()
