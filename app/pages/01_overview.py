"""
FinSight AI - Overview Dashboard Page
"""
import streamlit as st
import pandas as pd
from app.components.header import render_global_header
from app.components.kpi_card import render_kpi_card
from app.components.charts import create_candlestick_chart
from app.services.stock_service import stock_service
from app.services.portfolio_service import portfolio_service
from app.services.sentiment_service import sentiment_service
from app.database.repository import Repository
from app.analytics.currency import currency_engine
from app.core.constants import MARKET_IN, MARKET_US, CURRENCY_INR, CURRENCY_USD, BENCHMARKS

def show():
    render_global_header("Executive Market Overview", "Macro indices, simulated portfolio health, top market movers & intelligence")

    market = st.session_state.get("market", MARKET_IN)
    currency = st.session_state.get("currency", CURRENCY_INR if market == MARKET_IN else CURRENCY_USD)

    # 1. Top Financial KPI Metrics
    paper_portfolios = Repository.get_paper_portfolios(user_id=1, market=market)
    primary_p = paper_portfolios[0] if paper_portfolios else None
    
    total_val = primary_p["initial_cash"] if primary_p else 0.0
    p_return_pct = 0.0
    p_unrealized_pnl = 0.0
    if primary_p:
        summary = portfolio_service.get_paper_portfolio_overview(primary_p["id"])
        total_val = summary["total_value"]
        p_return_pct = summary["total_return_pct"]
        p_unrealized_pnl = summary["unrealized_pnl"]

    watchlists = Repository.get_watchlists(user_id=1, market=market)
    total_wl_items = sum(len(w["symbols"]) for w in watchlists)

    # Fetch index benchmark quote
    bench_sym = BENCHMARKS.get(market, "^NSEI")
    bench_quote_resp = stock_service.get_stock_quote(bench_sym, market)
    bench_quote = bench_quote_resp.data

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        render_kpi_card(
            label=f"Simulated Portfolio ({market})",
            value=currency_engine.format_currency(total_val, currency),
            delta=f"{p_return_pct:+.2f}% total return",
            delta_type="positive" if p_return_pct >= 0 else "negative",
            badge_text="PAPER TRADING",
            badge_style="badge-cached"
        )
    with kpi2:
        if bench_quote:
            render_kpi_card(
                label=f"{bench_sym} Benchmark Index",
                value=f"{bench_quote.price:,.2f}",
                delta=f"{bench_quote.change_percent:+.2f}% ({bench_quote.change:+.2f})",
                delta_type="positive" if bench_quote.change >= 0 else "negative",
                badge_text="INDEX",
                badge_style="badge-live" if not bench_quote_resp.is_sample else "badge-sample"
            )
        else:
            render_kpi_card(label="Benchmark Index", value="N/A", delta="Offline", delta_type="neutral")

    with kpi3:
        render_kpi_card(
            label="Active Watchlists",
            value=f"{total_wl_items} Stocks",
            delta=f"{len(watchlists)} lists configured",
            delta_type="neutral",
            badge_text="MONITORING",
            badge_style="badge-live"
        )

    with kpi4:
        # Market Volatility Gauge
        hist_bench = stock_service.get_technical_data(bench_sym, market)
        ann_vol = hist_bench.get("risk_profile", {}).get("annualized_volatility", 0.15) * 100.0
        risk_level = "Low" if ann_vol < 12 else ("Moderate" if ann_vol < 20 else "Elevated")
        render_kpi_card(
            label="Market Realized Volatility",
            value=f"{ann_vol:.1f}%",
            delta=f"{risk_level} Volatility Regime",
            delta_type="positive" if ann_vol < 15 else "negative",
            badge_text="RISK GAUGE",
            badge_style="badge-cached"
        )

    # 2. Main Section: Benchmark Chart & Top Movers
    col_chart, col_movers = st.columns([7, 3])

    with col_chart:
        st.markdown(f"#### {bench_sym} Benchmark Candlestick Performance")
        if hist_bench.get("df") is not None and not hist_bench["df"].empty:
            chart = create_candlestick_chart(hist_bench["df"].tail(120), bench_sym, show_sma=True, show_bb=True)
            st.plotly_chart(chart, use_container_width=True)
        else:
            st.warning("Benchmark historical chart data unavailable.")

    with col_movers:
        st.markdown("#### Top Market Movers")
        mkt_overview = stock_service.get_market_overview(market)
        gainers = mkt_overview.get("gainers", [])
        losers = mkt_overview.get("losers", [])

        st.caption("🟢 Top Gainers")
        for g in gainers[:3]:
            st.markdown(
                f"<div style='display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid #26364B;'>"
                f"<span><b>{g.symbol}</b></span>"
                f"<span style='color:#22C997;'>▲ {g.change_percent:+.2f}%</span>"
                f"<span>{currency_engine.format_currency(g.price, currency)}</span>"
                f"</div>",
                unsafe_allow_html=True
            )

        st.caption("<br>🔴 Top Decliners", unsafe_allow_html=True)
        for l in losers[:3]:
            st.markdown(
                f"<div style='display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid #26364B;'>"
                f"<span><b>{l.symbol}</b></span>"
                f"<span style='color:#F06470;'>▼ {l.change_percent:+.2f}%</span>"
                f"<span>{currency_engine.format_currency(l.price, currency)}</span>"
                f"</div>",
                unsafe_allow_html=True
            )

    # 3. Bottom Section: Watchlist Summary & Financial News
    col_wl, col_news = st.columns([5, 5])

    with col_wl:
        st.markdown("#### Watchlist Tracking Summary")
        if watchlists:
            active_wl = watchlists[0]
            st.caption(f"Showing items in: **{active_wl['name']}**")
            wl_rows = []
            for sym in active_wl["symbols"]:
                q_res = stock_service.get_stock_quote(sym, market)
                if q_res.is_success and q_res.data:
                    q = q_res.data
                    wl_rows.append({
                        "Symbol": sym,
                        "Price": currency_engine.format_currency(q.price, currency),
                        "Day Change": f"{q.change_percent:+.2f}%",
                        "High": currency_engine.format_currency(q.day_high, currency),
                        "Low": currency_engine.format_currency(q.day_low, currency),
                    })
            if wl_rows:
                st.dataframe(pd.DataFrame(wl_rows), use_container_width=True, hide_index=True)
            else:
                st.info("No quotes found for symbols in watchlist.")
        else:
            st.info("No watchlists created yet.")

    with col_news:
        st.markdown("#### Live Financial News & Sentiment")
        news_data = sentiment_service.get_news_with_sentiment(market=market, limit=4)
        articles = news_data.get("articles", [])

        if articles:
            for a in articles:
                badge_style = "badge-live" if a.get("sentiment_label") == "Positive" else ("badge-offline" if a.get("sentiment_label") == "Negative" else "badge-sample")
                st.markdown(
                    f"<div class='finsight-card' style='padding: 12px 16px; margin-bottom: 10px;'>"
                    f"<div style='display:flex; justify-content:space-between; align-items:center;'>"
                    f"<span style='font-size:0.75rem; color:#94A3B8;'>{a.get('source')} • {a.get('published_at', '')[:16]}</span>"
                    f"<span class='badge {badge_style}'>{a.get('sentiment_label')} ({a.get('compound_score'):+.2f})</span>"
                    f"</div>"
                    f"<div style='font-weight:600; font-size:0.88rem; margin-top:5px;'>{a.get('headline')}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        else:
            st.info("No recent news articles available.")

if __name__ == "__main__":
    show()
