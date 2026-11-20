"""
FinSight AI - Overview Dashboard Page
Executive Market Overview with robust error handling, dynamic user context,
and decoupled sentiment / provenance badges.
"""
from typing import Dict, Any, Optional, Tuple
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

def format_volatility_kpi(risk_profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Safely extracts and formats realized volatility.
    Never substitutes an invented fallback (e.g. 15%).
    Returns 'N/A' when calculation is unavailable.
    """
    if not risk_profile or not isinstance(risk_profile, dict):
        return {
            "value": "N/A",
            "delta": "Data calculation unavailable",
            "delta_type": "neutral",
            "badge_text": "DATA UNAVAILABLE",
            "badge_style": "badge-offline",
            "is_available": False
        }

    raw_vol = risk_profile.get("annualized_volatility")
    if raw_vol is None or pd.isna(raw_vol) or raw_vol <= 0.0:
        return {
            "value": "N/A",
            "delta": "Data calculation unavailable",
            "delta_type": "neutral",
            "badge_text": "DATA UNAVAILABLE",
            "badge_style": "badge-offline",
            "is_available": False
        }

    ann_vol = float(raw_vol) * 100.0
    risk_level = "Low" if ann_vol < 12.0 else ("Moderate" if ann_vol < 20.0 else "Elevated")
    return {
        "value": f"{ann_vol:.1f}%",
        "delta": f"{risk_level} Volatility Regime",
        "delta_type": "positive" if ann_vol < 15.0 else "negative",
        "badge_text": "RISK GAUGE",
        "badge_style": "badge-cached",
        "is_available": True
    }

def get_sentiment_and_provenance_badges(
    article: Dict[str, Any],
    global_is_sample: bool = False,
    global_is_cached: bool = False
) -> Dict[str, str]:
    """
    Decouples sentiment classification from data freshness/provenance.
    Positive, Negative, Neutral are mapped strictly to model outputs.
    Live, Cached, Sample are mapped strictly to data provider metadata.
    """
    sentiment_label = article.get("sentiment_label", "Neutral")
    if sentiment_label == "Positive":
        sent_class = "badge-sentiment-pos"
    elif sentiment_label == "Negative":
        sent_class = "badge-sentiment-neg"
    else:
        sent_class = "badge-sentiment-neu"

    # Evaluate data provenance independently
    is_sample = article.get("is_sample", global_is_sample)
    is_cached = article.get("is_cached", global_is_cached)

    if is_sample:
        prov_label = "SAMPLE"
        prov_class = "badge-sample"
    elif is_cached:
        prov_label = "CACHED"
        prov_class = "badge-cached"
    else:
        prov_label = "LIVE"
        prov_class = "badge-live"

    return {
        "sentiment_label": sentiment_label,
        "sentiment_badge_class": sent_class,
        "provenance_label": prov_label,
        "provenance_badge_class": prov_class
    }

def format_market_movers_header(tracked_count: int, universe_size: int, market: str) -> Dict[str, str]:
    """Provides transparent non-misleading labeling of tracked stock universe."""
    return {
        "title": "Top Movers — Tracked Universe",
        "caption": f"Tracked Universe: {tracked_count} of {universe_size} active equities ({market})"
    }

def show():
    render_global_header("Executive Market Overview", "Macro indices, simulated portfolio health, top market movers & intelligence")

    market = st.session_state.get("market", MARKET_IN)
    currency = st.session_state.get("currency", CURRENCY_INR if market == MARKET_IN else CURRENCY_USD)

    # 1. Central Current User Context
    default_user = Repository.get_or_create_default_user()
    current_user_id = default_user.id

    # 2. Top Financial KPI Metrics
    paper_portfolios = Repository.get_paper_portfolios(user_id=current_user_id, market=market)
    primary_p = paper_portfolios[0] if paper_portfolios else None

    total_val = primary_p["initial_cash"] if primary_p else 0.0
    p_return_pct = 0.0
    if primary_p:
        summary = portfolio_service.get_paper_portfolio_overview(primary_p["id"], user_id=current_user_id)
        total_val = summary.get("total_value", primary_p["initial_cash"])
        p_return_pct = summary.get("total_return_pct", 0.0)

    watchlists = Repository.get_watchlists(user_id=current_user_id, market=market)
    total_wl_items = sum(len(w.get("symbols", [])) for w in watchlists)

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
            render_kpi_card(label="Benchmark Index", value="N/A", delta="Data unavailable", delta_type="neutral")

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
        # Market Volatility Gauge without silent fake fallback
        hist_bench = stock_service.get_technical_data(bench_sym, market)
        vol_info = format_volatility_kpi(hist_bench.get("risk_profile"))

        render_kpi_card(
            label="Market Realized Volatility",
            value=vol_info["value"],
            delta=vol_info["delta"],
            delta_type=vol_info["delta_type"],
            badge_text=vol_info["badge_text"],
            badge_style=vol_info["badge_style"]
        )

    if not vol_info["is_available"]:
        st.info(f"ℹ️ Note: Realized volatility calculation is currently unavailable for {bench_sym} due to insufficient historical trading sessions.")

    # 3. Main Section: Benchmark Chart & Top Movers
    col_chart, col_movers = st.columns([7, 3])

    with col_chart:
        st.markdown(f"#### {bench_sym} Benchmark Candlestick Performance")
        if hist_bench.get("df") is not None and not hist_bench["df"].empty:
            chart = create_candlestick_chart(hist_bench["df"].tail(120), bench_sym, show_sma=True, show_bb=True)
            st.plotly_chart(chart, use_container_width=True)
        else:
            st.warning("Benchmark historical chart data unavailable.")

    with col_movers:
        mkt_overview = stock_service.get_market_overview(market)
        gainers = mkt_overview.get("gainers", [])
        losers = mkt_overview.get("losers", [])
        universe_size = mkt_overview.get("universe_size", 0)
        tracked_count = mkt_overview.get("tracked_count", len(gainers) + len(losers))

        movers_meta = format_market_movers_header(tracked_count, universe_size, market)
        st.markdown(f"#### {movers_meta['title']}")
        st.caption(movers_meta["caption"])

        st.caption("🟢 Top Gainers")
        if gainers:
            for g in gainers[:3]:
                st.markdown(
                    f"<div style='display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid #26364B;'>"
                    f"<span><b>{g.symbol}</b></span>"
                    f"<span style='color:#22C997;'>▲ {g.change_percent:+.2f}%</span>"
                    f"<span>{currency_engine.format_currency(g.price, currency)}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        else:
            st.info("No gainers in tracked universe.")

        st.caption("<br>🔴 Top Decliners", unsafe_allow_html=True)
        if losers:
            for l in losers[:3]:
                st.markdown(
                    f"<div style='display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid #26364B;'>"
                    f"<span><b>{l.symbol}</b></span>"
                    f"<span style='color:#F06470;'>▼ {l.change_percent:+.2f}%</span>"
                    f"<span>{currency_engine.format_currency(l.price, currency)}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        else:
            st.info("No decliners in tracked universe.")

    # 4. Bottom Section: Watchlist Summary & Financial News
    col_wl, col_news = st.columns([5, 5])

    with col_wl:
        st.markdown("#### Watchlist Tracking Summary")
        if watchlists:
            active_wl = watchlists[0]
            st.caption(f"Showing items in: **{active_wl['name']}**")
            symbols_in_wl = active_wl.get("symbols", [])
            if symbols_in_wl:
                wl_rows = []
                for sym in symbols_in_wl:
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
                    st.info("No live or sample quotes returned for symbols in watchlist.")
            else:
                st.info(f"Watchlist '{active_wl['name']}' currently contains no stock symbols.")
        else:
            st.info("No watchlists created yet. Create or add stocks from the Stock Intelligence page.")

    with col_news:
        st.markdown("#### Financial News & Sentiment")
        news_data = sentiment_service.get_news_with_sentiment(market=market, limit=4)
        articles = news_data.get("articles", [])
        global_is_sample = news_data.get("is_sample", False)
        global_is_cached = news_data.get("is_cached", False)

        st.caption("ℹ️ Headline sentiment generated by TF-IDF & Logistic Regression classifier trained on curated financial corpus. Model confidence represents posterior probability, not guaranteed prediction certainty.")

        if articles:
            for a in articles:
                badges = get_sentiment_and_provenance_badges(
                    a, global_is_sample=global_is_sample, global_is_cached=global_is_cached
                )
                confidence = a.get("confidence")
                conf_text = f" • Model Confidence: {confidence*100.0:.0f}%" if confidence is not None else ""

                st.markdown(
                    f"<div class='finsight-card' style='padding: 12px 16px; margin-bottom: 10px;'>"
                    f"<div style='display:flex; justify-content:space-between; align-items:center;'>"
                    f"<span style='font-size:0.75rem; color:#94A3B8;'>{a.get('source', 'Financial News')} • {str(a.get('published_at', ''))[:16]}{conf_text}</span>"
                    f"<div style='display:flex; gap:6px;'>"
                    f"<span class='badge {badges['sentiment_badge_class']}'>{badges['sentiment_label']} ({a.get('compound_score', 0.0):+.2f})</span>"
                    f"<span class='badge {badges['provenance_badge_class']}'>{badges['provenance_label']}</span>"
                    f"</div>"
                    f"</div>"
                    f"<div style='font-weight:600; font-size:0.88rem; margin-top:5px; color:#F1F5F9;'>{a.get('headline')}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        else:
            st.info("No news articles retrieved for this market universe.")

if __name__ == "__main__":
    show()
