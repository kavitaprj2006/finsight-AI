"""
FinSight AI - Stock Intelligence & Technical Analytics
"""
import streamlit as st
import pandas as pd
from app.components.header import render_global_header
from app.components.kpi_card import render_kpi_card
from app.components.charts import create_candlestick_chart, create_rsi_macd_chart
from app.services.stock_service import stock_service
from app.database.repository import Repository
from app.analytics.currency import currency_engine
from app.core.constants import MARKET_IN, DEFAULT_SYMBOLS

def show():
    render_global_header("Stock Intelligence & Analytics", "Company profiles, multi-timeframe candlestick charts, technical indicators & fundamentals")

    market = st.session_state.get("market", MARKET_IN)
    currency = st.session_state.get("currency", "INR" if market == MARKET_IN else "USD")

    # Search & Selection Bar
    symbols_list = [s["symbol"] for s in DEFAULT_SYMBOLS.get(market, [])]
    col_sym, col_period, col_wl_add = st.columns([4, 3, 3])

    with col_sym:
        selected_symbol = st.selectbox(
            "Select or Search Ticker",
            options=symbols_list,
            index=0,
            help="Choose a stock ticker to analyze"
        )

    with col_period:
        lookback = st.selectbox("Lookback Period", ["3 Months", "6 Months", "1 Year", "All Data"], index=2)

    with col_wl_add:
        watchlists = Repository.get_watchlists(user_id=1, market=market)
        wl_names = [w["name"] for w in watchlists] if watchlists else ["Default Watchlist"]
        target_wl = st.selectbox("Add to Watchlist", options=wl_names)
        if st.button("Add Ticker", use_container_width=True):
            added = Repository.add_to_watchlist(user_id=1, watchlist_name=target_wl, symbol=selected_symbol, market=market)
            if added:
                st.success(f"Added {selected_symbol} to {target_wl}!")
            else:
                st.info(f"{selected_symbol} is already in {target_wl}.")

    # Load Quote & Details
    quote_resp = stock_service.get_stock_quote(selected_symbol, market)
    quote = quote_resp.data

    tech_data = stock_service.get_technical_data(selected_symbol, market)
    df = tech_data.get("df")
    risk_prof = tech_data.get("risk_profile", {})
    comp_details = stock_service.get_company_details(selected_symbol, market)
    profile = comp_details.get("profile")
    ratios = comp_details.get("ratios", {})

    if quote is None or df is None or df.empty:
        st.error(f"Unable to retrieve market data for {selected_symbol}. Please check connection or symbol.")
        return

    # Filter period
    days_map = {"3 Months": 65, "6 Months": 130, "1 Year": 252, "All Data": len(df)}
    display_df = df.tail(days_map.get(lookback, 252))

    # Metric Row
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        render_kpi_card(
            label="Current Price",
            value=currency_engine.format_currency(quote.price, currency),
            delta=f"{quote.change_percent:+.2f}%",
            delta_type="positive" if quote.change >= 0 else "negative",
            badge_text=quote_resp.provider,
            badge_style="badge-live" if not quote_resp.is_sample else "badge-sample"
        )
    with m2:
        render_kpi_card(
            label="Day Range",
            value=f"{quote.day_low:,.1f} - {quote.day_high:,.1f}",
            delta=f"Open: {quote.open_price:,.1f}",
            delta_type="neutral"
        )
    with m3:
        render_kpi_card(
            label="Annual Volatility",
            value=f"{risk_prof.get('annualized_volatility', 0.15)*100.0:.1f}%",
            delta=f"Beta: {risk_prof.get('beta', 1.0):.2f}",
            delta_type="neutral"
        )
    with m4:
        pe = ratios.get("pe_ratio")
        pe_str = f"{pe:.1f}x" if pe else "N/A"
        render_kpi_card(
            label="P/E Ratio",
            value=pe_str,
            delta=f"P/B: {ratios.get('pb_ratio', 0.0):.1f}x" if ratios.get("pb_ratio") else "P/B: N/A",
            delta_type="neutral"
        )
    with m5:
        render_kpi_card(
            label="Max Drawdown",
            value=f"{abs(risk_prof.get('max_drawdown', 0.0))*100.0:.1f}%",
            delta=f"Sharpe: {risk_prof.get('sharpe_ratio', 0.0):.2f}",
            delta_type="positive" if risk_prof.get('sharpe_ratio', 0.0) > 1.0 else "neutral"
        )

    # Technical Chart Tabs
    tab_chart, tab_indicators, tab_fundamentals, tab_profile = st.tabs([
        "Price & Moving Averages", "Momentum (RSI & MACD)", "Financial Statements & Ratios", "Company Profile"
    ])

    with tab_chart:
        c_chart = create_candlestick_chart(display_df, selected_symbol, show_sma=True, show_bb=True, show_volume=True)
        st.plotly_chart(c_chart, use_container_width=True)

    with tab_indicators:
        i_chart = create_rsi_macd_chart(display_df)
        st.plotly_chart(i_chart, use_container_width=True)

    with tab_fundamentals:
        col_ratios, col_stmts = st.columns([4, 6])
        with col_ratios:
            st.markdown("##### Valuation & Operational Ratios")
            ratio_items = [
                ("P/E Ratio", f"{ratios.get('pe_ratio', 'N/A')}"),
                ("P/B Ratio", f"{ratios.get('pb_ratio', 'N/A')}"),
                ("P/S Ratio", f"{ratios.get('ps_ratio', 'N/A')}"),
                ("Debt to Equity", f"{ratios.get('debt_to_equity', 'N/A')}"),
                ("Return on Equity (ROE)", f"{ratios.get('roe', 0.0)*100.0:.1f}%" if ratios.get("roe") else "N/A"),
                ("Return on Assets (ROA)", f"{ratios.get('roa', 0.0)*100.0:.1f}%" if ratios.get("roa") else "N/A"),
                ("Net Profit Margin", f"{ratios.get('net_margin', 0.0)*100.0:.1f}%" if ratios.get("net_margin") else "N/A"),
                ("Dividend Yield", f"{ratios.get('dividend_yield', 0.0)*100.0:.2f}%" if ratios.get("dividend_yield") else "N/A"),
            ]
            ratio_df = pd.DataFrame(ratio_items, columns=["Metric", "Value"])
            st.dataframe(ratio_df, use_container_width=True, hide_index=True)

        with col_stmts:
            st.markdown("##### Multi-Year Financial Performance")
            stmts = comp_details.get("statements", {})
            income_list = stmts.get("income_statement", [])
            if income_list:
                inc_df = pd.DataFrame(income_list)
                for c in ["revenue", "operating_income", "net_income"]:
                    if c in inc_df.columns:
                        inc_df[c] = inc_df[c].apply(lambda x: currency_engine.format_currency(x, currency))
                st.dataframe(inc_df, use_container_width=True, hide_index=True)
            else:
                st.info("Financial statements not available for this ticker.")

    with tab_profile:
        if profile:
            st.markdown(f"#### {profile.name} ({profile.symbol})")
            st.markdown(f"**Exchange:** {profile.exchange} | **Sector:** {profile.sector} | **Industry:** {profile.industry}")
            st.write(profile.description or "No detailed description available.")
            if profile.website:
                st.markdown(f"**Official Website:** [{profile.website}]({profile.website})")
        else:
            st.info("Profile details unavailable.")

if __name__ == "__main__":
    show()
