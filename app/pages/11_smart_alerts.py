"""
FinSight AI - Smart Alerts & Notification Center
Configurable threshold monitoring: Price breaks, volatility spikes, and portfolio drawdowns.
"""
import streamlit as st
import pandas as pd
from app.components.header import render_global_header
from app.components.kpi_card import render_kpi_card
from app.services.alert_service import alert_service
from app.services.stock_service import stock_service
from app.database.repository import Repository
from app.core.constants import (
    MARKET_IN, DEFAULT_SYMBOLS, ALERT_PRICE_ABOVE, ALERT_PRICE_BELOW,
    ALERT_VOLATILITY_ABOVE, ALERT_DRAWDOWN_EXCEEDED
)

def show():
    render_global_header("Smart Automated Market Alerts", "Event-driven threshold triggers: Price breakout/breakdown, volatility spikes & tail-risk drawdowns")

    market = st.session_state.get("market", MARKET_IN)
    symbols_list = [s["symbol"] for s in DEFAULT_SYMBOLS.get(market, [])]

    # Evaluate alerts right now
    triggered = alert_service.evaluate_active_alerts(user_id=1)
    if triggered:
        for t in triggered:
            st.warning(f"🚨 **Alert Triggered:** {t['message']}")

    # Create New Alert
    with st.expander("➕ Configure New Smart Alert", expanded=False):
        c_sym, c_type, c_val = st.columns([4, 4, 3])
        with c_sym:
            target_sym = st.selectbox("Symbol", options=symbols_list)
        with c_type:
            alert_type = st.selectbox(
                "Trigger Condition",
                [ALERT_PRICE_ABOVE, ALERT_PRICE_BELOW, ALERT_VOLATILITY_ABOVE, ALERT_DRAWDOWN_EXCEEDED],
                format_func=lambda x: {
                    ALERT_PRICE_ABOVE: "Price Rises Above Target (Breakout)",
                    ALERT_PRICE_BELOW: "Price Drops Below Target (Stop Loss)",
                    ALERT_VOLATILITY_ABOVE: "Realized Volatility Exceeds (%)",
                    ALERT_DRAWDOWN_EXCEEDED: "Drawdown Exceeds Peak (%)"
                }[x]
            )
        with c_val:
            # Default reference price
            q_res = stock_service.get_stock_quote(target_sym, market)
            cur_price = q_res.data.price if q_res.is_success and q_res.data else 100.0
            def_val = cur_price * 1.05 if alert_type == ALERT_PRICE_ABOVE else (cur_price * 0.95 if alert_type == ALERT_PRICE_BELOW else 25.0)
            threshold_val = st.number_input("Threshold Level", value=float(def_val), step=1.0)

        if st.button("Save Alert Trigger", use_container_width=True):
            Repository.create_alert(user_id=1, symbol=target_sym, alert_type=alert_type, threshold=threshold_val, market=market)
            st.success(f"Alert configured for {target_sym} at {threshold_val:.2f}!")
            st.rerun()

    # Active Alerts & Events
    active_alerts = Repository.get_active_alerts(user_id=1)
    past_events = Repository.get_alert_events(user_id=1, limit=20)

    k1, k2 = st.columns(2)
    with k1:
        render_kpi_card(label="Active Triggers", value=f"{len(active_alerts)} Alerts", delta="Listening on refresh", delta_type="neutral")
    with k2:
        render_kpi_card(label="Triggered Events", value=f"{len(past_events)} Logged", delta="Audit history", delta_type="neutral")

    tab_active, tab_history = st.tabs(["Active Monitored Triggers", "Historical Trigger Events"])

    with tab_active:
        if active_alerts:
            rows = []
            for a in active_alerts:
                rows.append({
                    "ID": a["id"],
                    "Symbol": a["symbol"],
                    "Condition": a["type"].replace("_", " "),
                    "Threshold": f"{a['threshold']:,.2f}",
                    "Market": a["market"],
                    "Created": a["created_at"].strftime("%Y-%m-%d %H:%M") if hasattr(a["created_at"], "strftime") else str(a["created_at"])[:16]
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            del_id = st.selectbox("Select Alert to Remove", options=[a["id"] for a in active_alerts], format_func=lambda x: f"Alert #{x}")
            if st.button("Delete Selected Alert"):
                Repository.delete_alert(del_id)
                st.success(f"Deleted Alert #{del_id}!")
                st.rerun()
        else:
            st.info("No active alerts currently monitored.")

    with tab_history:
        if past_events:
            ev_rows = [
                {
                    "Trigger Time": e["triggered_at"].strftime("%Y-%m-%d %H:%M") if hasattr(e["triggered_at"], "strftime") else str(e["triggered_at"])[:16],
                    "Symbol": e["symbol"],
                    "Event Message": e["message"],
                    "Trigger Value": f"{e['triggered_value']:,.2f}",
                    "Threshold Target": f"{e['threshold_value']:,.2f}"
                }
                for e in past_events
            ]
            st.dataframe(pd.DataFrame(ev_rows), use_container_width=True, hide_index=True)
        else:
            st.info("No historical trigger events recorded yet.")

if __name__ == "__main__":
    show()
