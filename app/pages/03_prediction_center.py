"""
FinSight AI - Prediction Center (Supervised ML)
Forward return regression (5d, 20d) & market direction classification with walk-forward validation.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from app.components.header import render_global_header
from app.components.kpi_card import render_kpi_card
from app.services.stock_service import stock_service
from app.ml.feature_engineering import generate_ml_features, train_test_split_temporal
from app.ml.regression_models import ReturnRegressionSuite
from app.ml.classification_models import MarketDirectionClassifierSuite
from app.ml.mlflow_tracker import mlflow_tracker
from app.database.repository import Repository
from app.core.constants import MARKET_IN, DEFAULT_SYMBOLS, COLOR_CARD_BG, COLOR_BORDER, COLOR_PRIMARY_ACCENT, COLOR_SECONDARY_ACCENT

def show():
    render_global_header("Predictive Intelligence Center", "Rigorous supervised machine learning: Ridge, Random Forest, & XGBoost forecasting")

    market = st.session_state.get("market", MARKET_IN)
    symbols_list = [s["symbol"] for s in DEFAULT_SYMBOLS.get(market, [])]

    # Model Configuration Controls
    col_sym, col_task, col_horizon = st.columns([4, 3, 3])
    with col_sym:
        selected_symbol = st.selectbox("Target Ticker", options=symbols_list, index=0)
    with col_task:
        task_type = st.radio("Predictive Task", ["Forward Return Regression", "Market Direction Classification"], horizontal=True)
    with col_horizon:
        horizon_days = st.selectbox("Forecast Horizon", [5, 20], format_func=lambda x: f"{x} Trading Days (~{x//5} Wk)")

    # Data Fetching
    tech_data = stock_service.get_technical_data(selected_symbol, market)
    raw_df = tech_data.get("df")

    if raw_df is None or len(raw_df) < 100:
        st.error(f"Insufficient history ({len(raw_df) if raw_df is not None else 0} days) to train predictive models on {selected_symbol}.")
        return

    # Feature Engineering (Chronological)
    X, y_reg, y_clf = generate_ml_features(raw_df, horizon=horizon_days)
    target_series = y_reg if "Regression" in task_type else y_clf
    X_train, X_test, y_train, y_test = train_test_split_temporal(X, target_series, train_ratio=0.80)

    as_of_price = float(raw_df["Close"].iloc[-1])

    # Run Models
    if "Regression" in task_type:
        suite = ReturnRegressionSuite()
        eval_output = suite.fit_and_evaluate(X_train, y_train, X_test, y_test)
        comp = eval_output["comparison"]
        best_name = eval_output["best_model_name"]
        best_metrics = eval_output["best_metrics"]
        feat_imp = eval_output["feature_importances"]

        # Predict next period return using latest features
        latest_X = X.iloc[[-1]]
        pred_return = float(suite.predict(best_name, latest_X)[0])
        pred_price = as_of_price * (1.0 + pred_return)

        # Log to MLflow
        mlflow_tracker.log_run(
            experiment_name="Stock_Return_Regression",
            model_name=best_name,
            task_type="REGRESSION",
            market=market,
            symbol=selected_symbol,
            params={"horizon": horizon_days, "train_size": len(X_train)},
            metrics=best_metrics
        )
        Repository.record_prediction(
            symbol=selected_symbol, market=market, task="REGRESSION",
            model_name=best_name, horizon=horizon_days, as_of_price=as_of_price,
            return_pred=pred_return, version="v1.2", features={"features_count": len(X.columns)}
        )

        # Top Metric Cards
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_kpi_card(
                label=f"Expected {horizon_days}d Return",
                value=f"{pred_return*100.0:+.2f}%",
                delta=f"Projected: {pred_price:,.2f}",
                delta_type="positive" if pred_return >= 0 else "negative",
                badge_text=best_name.split()[0].upper(),
                badge_style="badge-live"
            )
        with c2:
            render_kpi_card(label="Test Set R² Score", value=f"{best_metrics['r2']:.3f}", delta="Out-of-sample fit", delta_type="neutral")
        with c3:
            render_kpi_card(label="Mean Absolute Error", value=f"{best_metrics['mae']*100.0:.2f}%", delta="Avg return deviation", delta_type="neutral")
        with c4:
            render_kpi_card(label="Directional Accuracy", value=f"{best_metrics['directional_accuracy']*100.0:.1f}%", delta="Sign accuracy", delta_type="positive")

        # Visualizations
        tab_comparison, tab_importance, tab_disclaimer = st.tabs(["Model Leaderboard", "Feature Importance", "Methodology & Disclaimers"])
        with tab_comparison:
            st.markdown("##### Model Benchmark Comparison (Out-of-Sample Test Set)")
            comp_rows = [
                {"Model": m, "MAE (%)": f"{vals['mae']*100.0:.2f}%", "RMSE (%)": f"{vals['rmse']*100.0:.2f}%", "R² Score": f"{vals['r2']:.4f}", "Directional Accuracy": f"{vals['directional_accuracy']*100.0:.1f}%"}
                for m, vals in comp.items()
            ]
            st.dataframe(pd.DataFrame(comp_rows), use_container_width=True, hide_index=True)

        with tab_importance:
            st.markdown(f"##### Key Drivers of {best_name} Forecast")
            if feat_imp:
                top_feats = list(feat_imp.items())[:10]
                fig_imp = go.Figure(go.Bar(
                    x=[f[1] for f in top_feats][::-1],
                    y=[f[0] for f in top_feats][::-1],
                    orientation="h",
                    marker_color=COLOR_PRIMARY_ACCENT
                ))
                fig_imp.update_layout(
                    paper_bgcolor=COLOR_CARD_BG, plot_bgcolor=COLOR_CARD_BG,
                    font=dict(color="#F1F5F9"), margin=dict(l=40, r=20, t=20, b=20),
                    xaxis=dict(gridcolor=COLOR_BORDER)
                )
                st.plotly_chart(fig_imp, use_container_width=True)

        with tab_disclaimer:
            st.info(
                "**Educational Notice**: Supervised machine learning return predictions represent statistical expected values "
                "conditional on historical indicators and do NOT guarantee actual future stock market prices. All models enforce "
                "temporal train-test splits to avoid look-ahead data leakage."
            )

    else:
        # Classification
        suite = MarketDirectionClassifierSuite()
        eval_output = suite.fit_and_evaluate(X_train, y_train, X_test, y_test)
        comp = eval_output["comparison"]
        best_name = eval_output["best_model_name"]
        best_metrics = eval_output["best_metrics"]
        feat_imp = eval_output["feature_importances"]

        latest_X = X.iloc[[-1]]
        pred_dir_int, pred_prob = suite.predict(best_name, latest_X)
        pred_dir = "BULLISH (UP)" if pred_dir_int[0] == 1 else "BEARISH (DOWN)"
        prob_val = float(pred_prob[0]) if pred_dir_int[0] == 1 else float(1.0 - pred_prob[0])

        mlflow_tracker.log_run(
            experiment_name="Market_Direction_Classification",
            model_name=best_name,
            task_type="CLASSIFICATION",
            market=market,
            symbol=selected_symbol,
            params={"horizon": horizon_days, "train_size": len(X_train)},
            metrics=best_metrics
        )
        Repository.record_prediction(
            symbol=selected_symbol, market=market, task="CLASSIFICATION",
            model_name=best_name, horizon=horizon_days, as_of_price=as_of_price,
            direction_pred=pred_dir, prob=prob_val, version="v1.2"
        )

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_kpi_card(
                label=f"Projected {horizon_days}d Direction",
                value=pred_dir,
                delta=f"{prob_val*100.0:.1f}% Confidence",
                delta_type="positive" if "UP" in pred_dir else "negative",
                badge_text=best_name.split()[0].upper(),
                badge_style="badge-live"
            )
        with c2:
            render_kpi_card(label="Test Accuracy", value=f"{best_metrics['accuracy']*100.0:.1f}%", delta="Out-of-sample score", delta_type="neutral")
        with c3:
            render_kpi_card(label="F1 Score", value=f"{best_metrics['f1']:.3f}", delta="Harmonic mean prec/rec", delta_type="neutral")
        with c4:
            render_kpi_card(label="ROC-AUC Score", value=f"{best_metrics['roc_auc']:.3f}", delta="Discriminative power", delta_type="positive")

        tab_comp, tab_feats = st.tabs(["Classifier Leaderboard", "Feature Importance"])
        with tab_comp:
            st.markdown("##### Classifier Test Evaluation (Chronological Split)")
            clf_rows = [
                {"Model": m, "Accuracy": f"{v['accuracy']*100.0:.1f}%", "Precision": f"{v['precision']*100.0:.1f}%", "Recall": f"{v['recall']*100.0:.1f}%", "F1 Score": f"{v['f1']:.3f}", "ROC-AUC": f"{v['roc_auc']:.3f}"}
                for m, v in comp.items()
            ]
            st.dataframe(pd.DataFrame(clf_rows), use_container_width=True, hide_index=True)

        with tab_feats:
            if feat_imp:
                top_feats = list(feat_imp.items())[:10]
                fig_imp = go.Figure(go.Bar(
                    x=[f[1] for f in top_feats][::-1],
                    y=[f[0] for f in top_feats][::-1],
                    orientation="h",
                    marker_color=COLOR_SECONDARY_ACCENT
                ))
                fig_imp.update_layout(
                    paper_bgcolor=COLOR_CARD_BG, plot_bgcolor=COLOR_CARD_BG,
                    font=dict(color="#F1F5F9"), margin=dict(l=40, r=20, t=20, b=20),
                    xaxis=dict(gridcolor=COLOR_BORDER)
                )
                st.plotly_chart(fig_imp, use_container_width=True)

if __name__ == "__main__":
    show()
