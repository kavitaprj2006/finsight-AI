"""
FinSight AI - Comprehensive Portfolio Risk Analyzer
Calculates Sharpe, Sortino, Historical VaR, CVaR, Beta, Drawdowns, and Cross-Asset Correlation.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from app.components.header import render_global_header
from app.components.kpi_card import render_kpi_card
from app.components.charts import create_correlation_heatmap
from app.services.stock_service import stock_service
from app.analytics.risk_metrics import compute_portfolio_risk_profile
from app.core.constants import MARKET_IN, DEFAULT_SYMBOLS, BENCHMARKS, COLOR_CARD_BG, COLOR_BORDER, COLOR_NEGATIVE

def show():
    render_global_header("Portfolio & Asset Risk Analytics", "Stress testing, tail-risk metrics: Value at Risk (VaR), CVaR, underwater drawdowns & Beta")

    market = st.session_state.get("market", MARKET_IN)
    symbols_list = [s["symbol"] for s in DEFAULT_SYMBOLS.get(market, [])]
    bench_sym = BENCHMARKS.get(market, "^NSEI")

    col_target, col_rf = st.columns([7, 3])
    with col_target:
        selected_asset = st.selectbox("Select Asset to Audit", options=symbols_list, index=0)
    with col_rf:
        rf_rate = st.number_input("Risk-Free Rate (%)", min_value=0.0, max_value=15.0, value=5.0, step=0.25) / 100.0

    # Load Asset & Benchmark Data
    tech_data = stock_service.get_technical_data(selected_asset, market)
    bench_data = stock_service.get_technical_data(bench_sym, market)

    df_asset = tech_data.get("df")
    df_bench = bench_data.get("df")

    if df_asset is None or df_asset.empty:
        st.error(f"Price data unavailable for {selected_asset}.")
        return

    bench_series = df_bench["Close"] if df_bench is not None else None
    risk = compute_portfolio_risk_profile(df_asset["Close"], bench_series, risk_free_rate=rf_rate)

    # Risk KPI Cards
    r1, r2, r3, r4, r5 = st.columns(5)
    with r1:
        render_kpi_card(
            label="Annualized Volatility",
            value=f"{risk['annualized_volatility']*100.0:.1f}%",
            delta=f"Return: {risk['annualized_return']*100.0:+.1f}%",
            delta_type="positive" if risk['annualized_return'] >= 0 else "negative",
            badge_text="VOLATILITY",
            badge_style="badge-cached"
        )
    with r2:
        render_kpi_card(
            label="Sharpe Ratio",
            value=f"{risk['sharpe_ratio']:.2f}",
            delta=f"Rf={rf_rate*100.0:.1f}%",
            delta_type="positive" if risk['sharpe_ratio'] > 1.0 else "neutral"
        )
    with r3:
        render_kpi_card(
            label="Sortino Ratio",
            value=f"{risk['sortino_ratio']:.2f}",
            delta="Downside penalty",
            delta_type="positive" if risk['sortino_ratio'] > 1.0 else "neutral"
        )
    with r4:
        render_kpi_card(
            label="Value at Risk (95% 1d)",
            value=f"{risk['var_95']*100.0:.2f}%",
            delta=f"CVaR: {risk['cvar_95']*100.0:.2f}%",
            delta_type="negative",
            badge_text="TAIL RISK",
            badge_style="badge-offline"
        )
    with r5:
        render_kpi_card(
            label="Maximum Drawdown",
            value=f"{abs(risk['max_drawdown'])*100.0:.1f}%",
            delta=f"Beta: {risk['beta']:.2f}",
            delta_type="neutral"
        )

    # Detailed Drawdown Chart
    tab_dd, tab_vol, tab_guide = st.tabs(["Underwater Drawdown Curve", "Rolling Realized Volatility", "Risk Glossary & Formulas"])

    with tab_dd:
        st.markdown(f"##### Peak-to-Trough Drawdown History ({selected_asset})")
        dd_series = risk["drawdown_series"] * 100.0
        fig_dd = go.Figure()
        fig_dd.add_trace(go.Scatter(
            x=dd_series.index, y=dd_series.values,
            mode="lines", fill="tozeroy",
            line=dict(color=COLOR_NEGATIVE, width=1.5),
            fillcolor="rgba(240, 100, 112, 0.2)",
            name="Drawdown %"
        ))
        fig_dd.update_layout(
            paper_bgcolor=COLOR_CARD_BG, plot_bgcolor=COLOR_CARD_BG,
            font=dict(color="#F1F5F9"), margin=dict(l=40, r=20, t=20, b=40),
            xaxis=dict(gridcolor=COLOR_BORDER),
            yaxis=dict(title="Drawdown (%)", gridcolor=COLOR_BORDER)
        )
        st.plotly_chart(fig_dd, use_container_width=True)

    with tab_vol:
        st.markdown(f"##### 21-Day Rolling Annualized Volatility ({selected_asset})")
        if "Rolling_Vol_21" in df_asset.columns:
            vol_series = df_asset["Rolling_Vol_21"] * 100.0
            fig_vol = go.Figure()
            fig_vol.add_trace(go.Scatter(
                x=vol_series.index, y=vol_series.values,
                mode="lines", line=dict(color="#4B9BFF", width=2),
                name="Rolling Volatility"
            ))
            fig_vol.update_layout(
                paper_bgcolor=COLOR_CARD_BG, plot_bgcolor=COLOR_CARD_BG,
                font=dict(color="#F1F5F9"), margin=dict(l=40, r=20, t=20, b=40),
                xaxis=dict(gridcolor=COLOR_BORDER),
                yaxis=dict(title="Annualized Vol (%)", gridcolor=COLOR_BORDER)
            )
            st.plotly_chart(fig_vol, use_container_width=True)

    with tab_guide:
        st.markdown("##### Quantitative Risk Definitions Explained")
        st.markdown("""
        - **Sharpe Ratio**: Measures excess return earned per unit of total risk: $\\frac{R_p - R_f}{\\sigma_p}$. Values $> 1.0$ indicate good risk efficiency.
        - **Sortino Ratio**: Penalizes only downside volatility: $\\frac{R_p - R_f}{\\sigma_{\\text{downside}}}$. More reflective of genuine investor loss pain.
        - **Value at Risk (VaR 95%)**: The maximum expected loss on any single trading day at a 95% confidence level.
        - **Conditional VaR (CVaR)**: Expected loss on the worst 5% of trading days (average loss beyond the VaR threshold).
        - **Beta ($\\beta$)**: Sensitivity of asset returns to benchmark moves: $\\beta > 1$ denotes higher cyclical volatility than market.
        """)

if __name__ == "__main__":
    show()
