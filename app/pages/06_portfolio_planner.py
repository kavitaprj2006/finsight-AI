"""
FinSight AI - Portfolio Planner & Asset Allocation Studio
Markowitz Modern Portfolio Theory, Equal-Weight, Minimum-Variance, and Maximum-Sharpe Optimization.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from app.components.header import render_global_header
from app.components.kpi_card import render_kpi_card
from app.components.charts import create_efficient_frontier_chart
from app.services.portfolio_service import portfolio_service
from app.database.repository import Repository
from app.analytics.currency import currency_engine
from app.core.constants import (
    MARKET_IN, DEFAULT_SYMBOLS, SCENARIO_CONSERVATIVE, SCENARIO_BALANCED, SCENARIO_GROWTH,
    COLOR_CARD_BG, COLOR_BORDER
)

def show():
    render_global_header("Strategic Portfolio Planning", "Constrained mathematical optimization: Efficient Frontier, Minimum-Variance & Maximum-Sharpe models")

    market = st.session_state.get("market", MARKET_IN)
    currency = st.session_state.get("currency", "INR" if market == MARKET_IN else "USD")

    # 1. Inputs & Parameters
    all_syms = [s["symbol"] for s in DEFAULT_SYMBOLS.get(market, []) if not s["symbol"].startswith("^")]
    
    col_syms, col_budget, col_cap = st.columns([5, 3, 2])
    with col_syms:
        chosen_universe = st.multiselect(
            "Asset Universe",
            options=all_syms,
            default=all_syms[:4] if len(all_syms) >= 4 else all_syms
        )
    with col_budget:
        budget = st.number_input(
            f"Investment Budget ({currency})",
            min_value=1000.0,
            max_value=100000000.0,
            value=500000.0 if currency == "INR" else 25000.0,
            step=5000.0
        )
    with col_cap:
        max_weight = st.slider("Max Asset Weight", min_value=0.20, max_value=0.80, value=0.40, step=0.05)

    if len(chosen_universe) < 2:
        st.warning("Please select at least 2 distinct assets to run portfolio optimization.")
        return

    # 2. Run Optimization Engine
    try:
        scenarios = portfolio_service.generate_educational_scenarios(
            symbols=chosen_universe, budget=budget, market=market, max_weight=max_weight
        )
    except Exception as e:
        st.error(f"Optimization error: {e}")
        return

    frontier_pts = scenarios.get("efficient_frontier", [])

    # 3. Scenario Selector & Metric Display
    selected_sc_name = st.radio(
        "Educational Asset Allocation Models",
        [SCENARIO_CONSERVATIVE, SCENARIO_BALANCED, SCENARIO_GROWTH],
        horizontal=True
    )
    active_sc = scenarios[selected_sc_name]

    st.caption(f"ℹ️ **Profile:** {active_sc['description']}")

    # Metric Cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card(
            label="Expected Annual Return",
            value=f"{active_sc['expected_return']*100.0:+.2f}%",
            delta=f"Sharpe: {active_sc['sharpe_ratio']:.2f}",
            delta_type="positive" if active_sc['expected_return'] >= 0 else "negative",
            badge_text=selected_sc_name.upper(),
            badge_style="badge-live"
        )
    with k2:
        render_kpi_card(
            label="Annualized Volatility",
            value=f"{active_sc['expected_volatility']*100.0:.2f}%",
            delta="Portfolio Standard Dev",
            delta_type="neutral"
        )
    with k3:
        render_kpi_card(
            label="Sharpe Ratio",
            value=f"{active_sc['sharpe_ratio']:.2f}",
            delta="Risk-Adjusted Return",
            delta_type="positive" if active_sc['sharpe_ratio'] > 1.0 else "neutral"
        )
    with k4:
        render_kpi_card(
            label="Total Allocation",
            value=currency_engine.format_currency(budget, currency),
            delta=f"{len(active_sc['assets'])} Active Positions",
            delta_type="neutral"
        )

    # 4. Allocation Visuals & Holdings Table
    col_donut, col_holdings = st.columns([4, 6])

    with col_donut:
        st.markdown(f"##### {selected_sc_name} Target Weights")
        assets = active_sc["assets"]
        labels = [a["symbol"] for a in assets]
        values = [a["weight"] for a in assets]

        fig_donut = go.Figure(data=[go.Pie(
            labels=labels, values=values, hole=0.55,
            marker=dict(colors=["#39D6A0", "#4B9BFF", "#F2B75A", "#F06470", "#A78BFA"]),
            textinfo="label+percent"
        )])
        fig_donut.update_layout(
            paper_bgcolor=COLOR_CARD_BG, plot_bgcolor=COLOR_CARD_BG,
            font=dict(color="#F1F5F9"), margin=dict(l=20, r=20, t=20, b=20),
            showlegend=False
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_holdings:
        st.markdown("##### Target Position Breakdown")
        table_rows = []
        for a in assets:
            table_rows.append({
                "Asset": a["symbol"],
                "Weight": f"{a['weight']*100.0:.1f}%",
                "Allocation Amount": currency_engine.format_currency(a["allocated_amount"], currency),
                "Latest Price": currency_engine.format_currency(a["current_price"], currency),
                "Implied Shares": f"{a['shares']:.1f}"
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

        if st.button("💾 Save Portfolio Scenario to Database", use_container_width=True):
            sc_id = Repository.save_portfolio_scenario(
                user_id=1,
                name=f"{selected_sc_name} Portfolio ({len(assets)} Assets)",
                strategy=active_sc["strategy"],
                scenario_type=selected_sc_name,
                market=market,
                currency=currency,
                budget=budget,
                exp_return=active_sc["expected_return"],
                exp_vol=active_sc["expected_volatility"],
                sharpe=active_sc["sharpe_ratio"],
                sortino=0.0,
                assets=assets
            )
            st.success(f"Scenario saved successfully! (Scenario ID: #{sc_id})")

    # 5. Efficient Frontier Chart
    st.markdown("##### Markowitz Efficient Frontier & Scenario Positioning")
    frontier_chart = create_efficient_frontier_chart(frontier_pts, scenarios)
    st.plotly_chart(frontier_chart, use_container_width=True)

if __name__ == "__main__":
    show()
