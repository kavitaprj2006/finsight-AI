"""
FinSight AI - Paper Portfolio Management Studio
Simulated order execution, average acquisition cost accounting, and persistent P&L tracking.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from app.components.header import render_global_header
from app.components.kpi_card import render_kpi_card
from app.components.tables import render_holdings_table, render_transaction_history_table
from app.services.portfolio_service import portfolio_service
from app.services.stock_service import stock_service
from app.database.repository import Repository
from app.analytics.currency import currency_engine
from app.core.constants import MARKET_IN, DEFAULT_SYMBOLS, COLOR_CARD_BG

def show():
    render_global_header("Simulated Paper Portfolio Studio", "Hypothetical position execution, weighted average cost accounting & persistent P&L ledger")

    market = st.session_state.get("market", MARKET_IN)
    currency = st.session_state.get("currency", "INR" if market == MARKET_IN else "USD")

    portfolios = Repository.get_paper_portfolios(user_id=1, market=market)

    # Portfolio Selection or Creation
    col_sel, col_create = st.columns([6, 4])
    with col_sel:
        if portfolios:
            p_map = {p["id"]: f"{p['name']} ({p['currency']})" for p in portfolios}
            selected_pid = st.selectbox("Select Active Portfolio", options=list(p_map.keys()), format_func=lambda x: p_map[x])
        else:
            selected_pid = None

    with col_create:
        with st.expander("➕ Create New Paper Portfolio"):
            new_p_name = st.text_input("Portfolio Name", value=f"Alpha Fund {market}")
            new_p_cash = st.number_input("Starting Cash", value=1000000.0 if currency == "INR" else 50000.0, step=10000.0)
            if st.button("Initialize Portfolio", use_container_width=True):
                new_id = Repository.create_paper_portfolio(
                    user_id=1, name=new_p_name, market=market, currency=currency, initial_cash=new_p_cash
                )
                st.success(f"Portfolio '{new_p_name}' initialized! (ID #{new_id})")
                st.rerun()

    if not selected_pid:
        st.info("No paper portfolio available. Please create one above.")
        return

    # Fetch Real-time Portfolio State
    summary = portfolio_service.get_paper_portfolio_overview(selected_pid)

    # Top KPI Metrics
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        render_kpi_card(
            label="Total Equity Value",
            value=currency_engine.format_currency(summary["total_value"], currency),
            delta=f"{summary['total_return_pct']:+.2f}% all-time",
            delta_type="positive" if summary["total_return_pct"] >= 0 else "negative",
            badge_text="LIVE NAV",
            badge_style="badge-live"
        )
    with k2:
        render_kpi_card(
            label="Available Cash",
            value=currency_engine.format_currency(summary["cash"], currency),
            delta="Dry Powder",
            delta_type="neutral"
        )
    with k3:
        render_kpi_card(
            label="Invested Capital",
            value=currency_engine.format_currency(summary["invested_value"], currency),
            delta=f"{len(summary['holdings'])} Active Holdings",
            delta_type="neutral"
        )
    with k4:
        render_kpi_card(
            label="Unrealized P&L",
            value=currency_engine.format_currency(summary["unrealized_pnl"], currency),
            delta="Open Positions",
            delta_type="positive" if summary["unrealized_pnl"] >= 0 else "negative"
        )
    with k5:
        render_kpi_card(
            label="Realized P&L",
            value=currency_engine.format_currency(summary["realized_pnl"], currency),
            delta="Closed Positions",
            delta_type="positive" if summary["realized_pnl"] >= 0 else "negative"
        )

    # Order Entry & Holdings
    tab_holdings, tab_order, tab_history = st.tabs(["Current Holdings & Allocation", "Simulated Order Execution", "Transaction Audit Ledger"])

    with tab_holdings:
        col_table, col_pie = st.columns([6, 4])
        with col_table:
            st.markdown("##### Current Positions")
            render_holdings_table(summary["holdings"], currency=currency)

        with col_pie:
            st.markdown("##### Portfolio Composition")
            if summary["holdings"]:
                h_labels = [h["symbol"] for h in summary["holdings"]] + ["Cash"]
                h_vals = [h["market_value"] for h in summary["holdings"]] + [summary["cash"]]
                fig_h = go.Figure(data=[go.Pie(labels=h_labels, values=h_vals, hole=0.55)])
                fig_h.update_layout(
                    paper_bgcolor=COLOR_CARD_BG, plot_bgcolor=COLOR_CARD_BG,
                    font=dict(color="#F1F5F9"), margin=dict(l=20, r=20, t=20, b=20),
                    showlegend=False
                )
                st.plotly_chart(fig_h, use_container_width=True)
            else:
                st.info("100% Cash allocation. Execute simulated trades to build positions.")

    with tab_order:
        st.markdown("##### Place Simulated Trade Order")
        symbols_list = [s["symbol"] for s in DEFAULT_SYMBOLS.get(market, []) if not s["symbol"].startswith("^")]

        o_sym, o_action, o_qty = st.columns(3)
        with o_sym:
            order_sym = st.selectbox("Symbol", options=symbols_list)
        with o_action:
            order_action = st.radio("Action", ["BUY", "SELL"], horizontal=True)
        with o_qty:
            order_qty = st.number_input("Shares / Quantity", min_value=1.0, value=10.0, step=1.0)

        # Quote for execution price
        q_res = stock_service.get_stock_quote(order_sym, market)
        exec_price = q_res.data.price if q_res.is_success and q_res.data else 100.0
        est_total = order_qty * exec_price
        st.caption(f"Estimated Execution Price: **{currency_engine.format_currency(exec_price, currency)}** | Total Value: **{currency_engine.format_currency(est_total, currency)}**")

        if st.button(f"Confirm {order_action} Order", use_container_width=True):
            try:
                Repository.record_transaction(
                    portfolio_id=selected_pid,
                    symbol=order_sym,
                    tx_type=order_action,
                    quantity=order_qty,
                    price=exec_price,
                    cost=10.0 # Standard nominal simulated ticket fee
                )
                st.success(f"Executed {order_action} {order_qty:.0f} shares of {order_sym} at {exec_price:,.2f}!")
                st.rerun()
            except Exception as e:
                st.error(f"Execution Error: {e}")

    with tab_history:
        st.markdown("##### Transaction Audit Trail")
        render_transaction_history_table(summary["recent_transactions"], currency=currency)

if __name__ == "__main__":
    show()
