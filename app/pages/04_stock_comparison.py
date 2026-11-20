"""
FinSight AI - Multi-Stock Comparison Engine
Normalized returns, cross-asset correlation, valuation multiples, and risk benchmarks.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from app.components.header import render_global_header
from app.components.charts import create_correlation_heatmap
from app.services.stock_service import stock_service
from app.analytics.risk_metrics import compute_portfolio_risk_profile
from app.core.constants import MARKET_IN, DEFAULT_SYMBOLS, COLOR_CARD_BG, COLOR_BORDER

def show():
    render_global_header("Comparative Stock Intelligence", "Cross-asset normalized performance, correlation matrix & financial multiple comparison")

    market = st.session_state.get("market", MARKET_IN)
    symbols_list = [s["symbol"] for s in DEFAULT_SYMBOLS.get(market, [])]

    # Select multiple tickers
    selected = st.multiselect(
        "Select Stocks for Peer Analysis",
        options=symbols_list,
        default=symbols_list[:3] if len(symbols_list) >= 3 else symbols_list
    )

    if len(selected) < 2:
        st.info("Please select at least 2 tickers to generate comparative analysis.")
        return

    # Load price matrix
    price_dict = {}
    ratio_rows = []
    risk_rows = []

    for s in selected:
        t_data = stock_service.get_technical_data(s, market)
        df = t_data.get("df")
        if df is not None and not df.empty:
            price_dict[s] = df["Close"]
            risk = t_data.get("risk_profile", {})
            risk_rows.append({
                "Ticker": s,
                "Annualized Return": f"{risk.get('annualized_return', 0.0)*100.0:+.1f}%",
                "Volatility": f"{risk.get('annualized_volatility', 0.0)*100.0:.1f}%",
                "Sharpe Ratio": f"{risk.get('sharpe_ratio', 0.0):.2f}",
                "Sortino Ratio": f"{risk.get('sortino_ratio', 0.0):.2f}",
                "Max Drawdown": f"{risk.get('max_drawdown', 0.0)*100.0:.1f}%",
                "Beta": f"{risk.get('beta', 1.0):.2f}"
            })

        comp_details = stock_service.get_company_details(s, market)
        r = comp_details.get("ratios", {})
        ratio_rows.append({
            "Ticker": s,
            "P/E Ratio": f"{r.get('pe_ratio', 'N/A')}",
            "P/B Ratio": f"{r.get('pb_ratio', 'N/A')}",
            "P/S Ratio": f"{r.get('ps_ratio', 'N/A')}",
            "Debt/Equity": f"{r.get('debt_to_equity', 'N/A')}",
            "ROE": f"{r.get('roe', 0.0)*100.0:.1f}%" if r.get("roe") else "N/A",
            "Net Margin": f"{r.get('net_margin', 0.0)*100.0:.1f}%" if r.get("net_margin") else "N/A",
            "Div Yield": f"{r.get('dividend_yield', 0.0)*100.0:.2f}%" if r.get("dividend_yield") else "N/A",
        })

    price_df = pd.DataFrame(price_dict).dropna()
    if price_df.empty:
        st.error("Unable to align closing prices across selected tickers.")
        return

    # Normalized Comparison Chart (Base 100)
    norm_df = (price_df / price_df.iloc[0]) * 100.0
    fig_norm = go.Figure()
    for col in norm_df.columns:
        fig_norm.add_trace(go.Scatter(x=norm_df.index, y=norm_df[col], mode="lines", name=col, line=dict(width=2)))

    fig_norm.update_layout(
        paper_bgcolor=COLOR_CARD_BG, plot_bgcolor=COLOR_CARD_BG,
        font=dict(color="#F1F5F9"), margin=dict(l=40, r=20, t=30, b=30),
        xaxis=dict(gridcolor=COLOR_BORDER), yaxis=dict(title="Normalized Index (Base=100)", gridcolor=COLOR_BORDER),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    tab_norm, tab_risk, tab_val, tab_corr = st.tabs([
        "Normalized Price Return (Base=100)", "Risk & Volatility Profile", "Valuation Multiples", "Correlation Heatmap"
    ])

    with tab_norm:
        st.plotly_chart(fig_norm, use_container_width=True)

    with tab_risk:
        st.markdown("##### Comparative Risk & Return Metrics")
        st.dataframe(pd.DataFrame(risk_rows), use_container_width=True, hide_index=True)

    with tab_val:
        st.markdown("##### Fundamental Valuation Multiples")
        st.dataframe(pd.DataFrame(ratio_rows), use_container_width=True, hide_index=True)

    with tab_corr:
        st.markdown("##### Cross-Asset Correlation Heatmap")
        returns_df = price_df.pct_change().dropna()
        corr_fig = create_correlation_heatmap(returns_df.corr())
        st.plotly_chart(corr_fig, use_container_width=True)

if __name__ == "__main__":
    show()
