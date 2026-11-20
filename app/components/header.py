"""
FinSight AI - Global Header Component
"""
import streamlit as st
from datetime import datetime, timezone
from app.core.constants import MARKET_IN, MARKET_US, CURRENCY_INR, CURRENCY_USD
from app.data_providers.factory import get_market_data_provider

def render_global_header(page_title: str, subtitle: str = ""):
    """Renders the top application navigation header and status indicator."""
    if "market" not in st.session_state:
        st.session_state["market"] = MARKET_IN
    if "currency" not in st.session_state:
        st.session_state["currency"] = CURRENCY_INR if st.session_state["market"] == MARKET_IN else CURRENCY_USD

    col_title, col_market, col_curr, col_status = st.columns([4, 2, 2, 2])

    with col_title:
        st.markdown(f"### {page_title}")
        if subtitle:
            st.caption(subtitle)

    with col_market:
        market_options = {"IN": "🇮🇳 Indian (NSE/BSE)", "US": "🇺🇸 US (NYSE/NASDAQ)"}
        selected_m = st.selectbox(
            "Market Universe",
            options=list(market_options.keys()),
            format_func=lambda x: market_options[x],
            index=0 if st.session_state["market"] == "IN" else 1,
            key="market_selector_header",
            label_visibility="collapsed"
        )
        if selected_m != st.session_state["market"]:
            st.session_state["market"] = selected_m
            st.session_state["currency"] = CURRENCY_INR if selected_m == "IN" else CURRENCY_USD
            st.rerun()

    with col_curr:
        curr_options = {"INR": "₹ INR", "USD": "$ USD"}
        selected_c = st.selectbox(
            "Base Currency",
            options=list(curr_options.keys()),
            format_func=lambda x: curr_options[x],
            index=0 if st.session_state["currency"] == "INR" else 1,
            key="currency_selector_header",
            label_visibility="collapsed"
        )
        if selected_c != st.session_state["currency"]:
            st.session_state["currency"] = selected_c
            st.rerun()

    with col_status:
        provider = get_market_data_provider()
        dummy_resp = provider.get_market_indices(st.session_state["market"])
        if dummy_resp.is_sample:
            badge_cls = "badge-sample"
            badge_txt = "SAMPLE / OFFLINE"
        elif dummy_resp.is_cached:
            badge_cls = "badge-cached"
            badge_txt = f"CACHED ({dummy_resp.provider})"
        else:
            badge_cls = "badge-live"
            badge_txt = f"LIVE ({dummy_resp.provider})"

        st.markdown(
            f'<div style="text-align: right; padding-top: 6px;"><span class="badge {badge_cls}">● {badge_txt}</span></div>',
            unsafe_allow_html=True
        )

    st.markdown("<hr style='margin-top: 5px; margin-bottom: 20px; border-color: #26364B;'>", unsafe_allow_html=True)
