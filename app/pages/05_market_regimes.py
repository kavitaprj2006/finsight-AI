"""
FinSight AI - Market Regime Detection Page
Unsupervised K-Means clustering on rolling return, volatility, momentum, and drawdowns.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from app.components.header import render_global_header
from app.components.kpi_card import render_kpi_card
from app.services.stock_service import stock_service
from app.ml.clustering import MarketRegimeDetector
from app.core.constants import MARKET_IN, BENCHMARKS, COLOR_CARD_BG, COLOR_BORDER

def show():
    render_global_header("Market Regime Detection Lab", "Unsupervised machine learning identifying latent market states: Bullish, High-Vol Bearish & Consolidation")

    market = st.session_state.get("market", MARKET_IN)
    bench_sym = BENCHMARKS.get(market, "^NSEI")

    col_target, col_clusters = st.columns([6, 4])
    with col_target:
        sym = st.selectbox("Asset / Benchmark for Regime Analysis", [bench_sym, "RELIANCE.NS" if market == "IN" else "AAPL"], index=0)
    with col_clusters:
        n_clusters = st.slider("Number of Latent Regimes (k)", min_value=2, max_value=5, value=3)

    tech_data = stock_service.get_technical_data(sym, market)
    raw_df = tech_data.get("df")

    if raw_df is None or len(raw_df) < 60:
        st.error(f"Insufficient historical data ({len(raw_df) if raw_df is not None else 0} rows) to detect regimes.")
        return

    detector = MarketRegimeDetector(n_clusters=n_clusters)
    try:
        regime_res = detector.fit_predict(raw_df)
    except Exception as e:
        st.error(f"Clustering error: {e}")
        return

    profiles = regime_res["profiles"]
    current_r = regime_res["current_regime"]
    feat_df = regime_res["features_df"]

    # Top KPI Cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card(
            label="Current Market State",
            value=current_r["name"],
            delta=f"{current_r['frequency_pct']:.1f}% historical frequency",
            delta_type="positive" if "Bullish" in current_r["name"] else ("negative" if "Bearish" in current_r["name"] else "neutral"),
            badge_text="ACTIVE REGIME",
            badge_style="badge-live"
        )
    with k2:
        render_kpi_card(label="Regime Mean Return", value=f"{current_r['mean_return_pct']:+.2f}%", delta="21-day rolling", delta_type="neutral")
    with k3:
        render_kpi_card(label="Regime Volatility", value=f"{current_r['annualized_vol_pct']:.1f}%", delta="Annualized std", delta_type="neutral")
    with k4:
        render_kpi_card(label="Average Drawdown", value=f"{current_r['mean_drawdown_pct']:.1f}%", delta="Peak to trough", delta_type="neutral")

    # Tabs
    tab_timeline, tab_profiles, tab_transitions = st.tabs(["Regime Timeline Overlay", "Cluster Statistics & Empirical Profiles", "Markov Transition Matrix"])

    with tab_timeline:
        st.markdown(f"##### Historical Regimes Colored Over {sym} Close Price")
        aligned_df = raw_df.loc[feat_df.index]
        fig = go.Figure()

        # Add colored scatter points for each regime
        for c, p in profiles.items():
            mask = feat_df["Regime"] == c
            sub_dates = aligned_df.index[mask]
            sub_prices = aligned_df.loc[mask, "Close"]
            fig.add_trace(go.Scatter(
                x=sub_dates, y=sub_prices, mode="markers",
                name=p["name"],
                marker=dict(size=4, color=p["color"])
            ))

        # Base line
        fig.add_trace(go.Scatter(
            x=aligned_df.index, y=aligned_df["Close"], mode="lines",
            name="Close Price", line=dict(color="rgba(148, 163, 184, 0.4)", width=1.5)
        ))

        fig.update_layout(
            paper_bgcolor=COLOR_CARD_BG, plot_bgcolor=COLOR_CARD_BG,
            font=dict(color="#F1F5F9"), margin=dict(l=40, r=20, t=20, b=40),
            xaxis=dict(gridcolor=COLOR_BORDER), yaxis=dict(title="Price", gridcolor=COLOR_BORDER),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab_profiles:
        st.markdown("##### Empirical Quantitative Signatures of Discovered Regimes")
        prof_rows = [
            {
                "Cluster": f"Regime {c}",
                "Classification": p["name"],
                "Mean 21d Return": f"{p['mean_return_pct']:+.2f}%",
                "Annualized Volatility": f"{p['annualized_vol_pct']:.1f}%",
                "Average Drawdown": f"{p['mean_drawdown_pct']:.1f}%",
                "Frequency": f"{p['frequency_pct']:.1f}% ({p['count']} days)"
            }
            for c, p in profiles.items()
        ]
        st.dataframe(pd.DataFrame(prof_rows), use_container_width=True, hide_index=True)

    with tab_transitions:
        st.markdown("##### Regime Transition Probabilities")
        st.caption("Probability of moving from Regime t (rows) to Regime t+1 (columns)")
        trans_df = pd.DataFrame(regime_res["transition_matrix"])
        trans_df.index = [f"From {profiles[i]['name']}" for i in trans_df.index]
        trans_df.columns = [f"To {profiles[int(c)]['name']}" for c in trans_df.columns]
        st.dataframe(trans_df.style.format("{:.1%}"), use_container_width=True)

if __name__ == "__main__":
    show()
