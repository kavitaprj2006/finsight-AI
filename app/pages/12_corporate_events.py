"""
FinSight AI - Corporate Events & Earnings Calendar
Upcoming earnings announcements, dividend ex-dates, splits, and shareholder meetings.
"""
import streamlit as st
import pandas as pd
from app.components.header import render_global_header
from app.components.kpi_card import render_kpi_card
from app.data_providers.factory import get_market_data_provider
from app.core.constants import MARKET_IN, DEFAULT_SYMBOLS

def show():
    render_global_header("Corporate Actions & Events Calendar", "Upcoming quarterly earnings releases, dividend record dates, splits & shareholder meetings")

    market = st.session_state.get("market", MARKET_IN)
    provider = get_market_data_provider()

    events_resp = provider.get_corporate_events(market=market)
    events = events_resp.data if events_resp.is_success and events_resp.data is not None else []

    # KPI counts
    earnings_count = sum(1 for e in events if "Earnings" in e.get("event_type", ""))
    div_count = sum(1 for e in events if "Dividend" in e.get("event_type", ""))
    other_count = len(events) - earnings_count - div_count

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card(
            label="Total Scheduled Events",
            value=f"{len(events)} Events",
            delta=f"Market: {market}",
            delta_type="neutral",
            badge_text=events_resp.provider,
            badge_style="badge-live" if not events_resp.is_sample else "badge-sample"
        )
    with k2:
        render_kpi_card(label="Earnings Calls", value=f"{earnings_count}", delta="Quarterly releases", delta_type="positive")
    with k3:
        render_kpi_card(label="Dividend Ex-Dates", value=f"{div_count}", delta="Income distributions", delta_type="positive")
    with k4:
        render_kpi_card(label="General Meetings", value=f"{other_count}", delta="Governance actions", delta_type="neutral")

    st.markdown("##### Detailed Events Schedule")
    if events:
        ev_rows = []
        for e in events:
            ev_rows.append({
                "Date": e.get("event_date"),
                "Symbol": e.get("symbol"),
                "Event Type": e.get("event_type"),
                "Details / Estimates": e.get("details"),
                "Market": e.get("market"),
                "Source Provider": events_resp.provider
            })
        df_events = pd.DataFrame(ev_rows).sort_values("Date")
        st.dataframe(df_events, use_container_width=True, hide_index=True)
    else:
        st.info("No upcoming corporate events found for this market.")

if __name__ == "__main__":
    show()
