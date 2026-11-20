"""
FinSight AI - Settings & System Configuration Page
"""
import streamlit as st
from app.components.header import render_global_header
from app.components.kpi_card import render_kpi_card
from app.config import settings
from app.data_providers.cache import cache
from app.data_providers.factory import ProviderFactory

def show():
    render_global_header("System Settings & Integration Center", "API keys, data provider diagnostics, local cache management & database status")

    provider = ProviderFactory.get_provider()
    active_prov_name = "FMP (Financial Modeling Prep)" if settings.FMP_API_KEY and settings.FMP_API_KEY != "your_fmp_api_key_here" else (
        "Alpha Vantage" if settings.ALPHA_VANTAGE_API_KEY and settings.ALPHA_VANTAGE_API_KEY != "your_alphavantage_api_key_here" else "Offline / High-Fidelity Sample Provider"
    )

    k1, k2, k3 = st.columns(3)
    with k1:
        render_kpi_card(
            label="Active Provider",
            value=active_prov_name.split()[0],
            delta=active_prov_name,
            delta_type="positive" if "Offline" not in active_prov_name else "neutral",
            badge_text="DATA ENGINE",
            badge_style="badge-live" if "Offline" not in active_prov_name else "badge-sample"
        )
    with k2:
        render_kpi_card(
            label="Database Connection",
            value="Operational",
            delta=settings.DATABASE_URL.split("://")[0].upper(),
            delta_type="positive",
            badge_text="POSTGRES/SQLITE",
            badge_style="badge-live"
        )
    with k3:
        cache_files = list(settings.CACHE_DIR.glob("*.cache"))
        render_kpi_card(
            label="Local Data Cache",
            value=f"{len(cache_files)} Cached Items",
            delta=f"TTL: {settings.CACHE_TTL_SECONDS}s",
            delta_type="neutral"
        )

    # API Configuration Form
    st.markdown("##### Market Data Provider Credentials")
    st.caption("FinSight AI never hardcodes keys; environment variables in `.env` are loaded automatically.")

    col_fmp, col_av = st.columns(2)
    with col_fmp:
        fmp_key = st.text_input("Financial Modeling Prep (FMP) API Key", value=settings.FMP_API_KEY, type="password")
    with col_av:
        av_key = st.text_input("Alpha Vantage API Key", value=settings.ALPHA_VANTAGE_API_KEY, type="password")

    col_offline, col_cache_btn = st.columns(2)
    with col_offline:
        force_offline = st.checkbox("Force Offline Development Mode (Use verified local sample data)", value=settings.OFFLINE_MODE)
        if st.button("Save Configuration", use_container_width=True):
            settings.FMP_API_KEY = fmp_key
            settings.ALPHA_VANTAGE_API_KEY = av_key
            settings.OFFLINE_MODE = force_offline
            st.success("Configuration updated successfully!")
            st.rerun()

    with col_cache_btn:
        st.write("")
        st.write("")
        if st.button("🗑️ Clear Disk and Memory Cache", use_container_width=True):
            cache.clear()
            st.success("Cache cleared successfully!")
            st.rerun()

    st.markdown("---")
    st.markdown("##### Application Architecture & Provenance")
    st.markdown("""
    - **Indian Equities:** National Stock Exchange (NSE) & Bombay Stock Exchange (BSE) with INR currency formatting.
    - **US Equities:** New York Stock Exchange (NYSE) & NASDAQ with USD currency formatting.
    - **Educational Guardrails:** Predictive models compute statistical conditional distributions and explicitly do NOT guarantee future stock prices.
    """)

if __name__ == "__main__":
    show()
