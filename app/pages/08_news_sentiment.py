"""
FinSight AI - Financial News & Sentiment Intelligence
NLP-driven sentiment analysis using TF-IDF feature extraction and Logistic Regression classification.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from app.components.header import render_global_header
from app.components.kpi_card import render_kpi_card
from app.services.sentiment_service import sentiment_service
from app.core.constants import MARKET_IN, DEFAULT_SYMBOLS, COLOR_CARD_BG, COLOR_BORDER

def show():
    render_global_header("News Sentiment & NLP Intelligence", "Natural language sentiment classification (Positive / Negative / Neutral) across corporate headlines")

    market = st.session_state.get("market", MARKET_IN)
    symbols_list = ["All Symbols"] + [s["symbol"] for s in DEFAULT_SYMBOLS.get(market, [])]

    col_sym, col_limit = st.columns([7, 3])
    with col_sym:
        sym_choice = st.selectbox("Filter News by Ticker", options=symbols_list, index=0)
    with col_limit:
        limit = st.slider("Number of Articles", min_value=5, max_value=25, value=10)

    target_sym = None if sym_choice == "All Symbols" else sym_choice
    news_res = sentiment_service.get_news_with_sentiment(symbol=target_sym, market=market, limit=limit)

    articles = news_res.get("articles", [])
    total = news_res.get("total_count", 0)

    # Top KPI Cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        avg_score = news_res.get("avg_compound_score", 0.0)
        overall_label = "BULLISH" if avg_score > 0.1 else ("BEARISH" if avg_score < -0.1 else "NEUTRAL")
        render_kpi_card(
            label="Aggregate Sentiment",
            value=overall_label,
            delta=f"Compound Score: {avg_score:+.2f}",
            delta_type="positive" if avg_score > 0.05 else ("negative" if avg_score < -0.05 else "neutral"),
            badge_text="NLP CLASSIFIER",
            badge_style="badge-live"
        )
    with k2:
        render_kpi_card(label="Positive Stories", value=f"{news_res.get('positive_pct', 0.0)}%", delta=f"{news_res.get('positive_count', 0)} articles", delta_type="positive")
    with k3:
        render_kpi_card(label="Negative Stories", value=f"{news_res.get('negative_pct', 0.0)}%", delta=f"{news_res.get('negative_count', 0)} articles", delta_type="negative")
    with k4:
        render_kpi_card(label="Neutral Stories", value=f"{news_res.get('neutral_pct', 0.0)}%", delta=f"{news_res.get('neutral_count', 0)} articles", delta_type="neutral")

    # Sentiment Breakdown & Articles Feed
    col_chart, col_feed = st.columns([4, 6])

    with col_chart:
        st.markdown("##### Sentiment Distribution Breakdown")
        labels = ["Positive", "Negative", "Neutral"]
        counts = [news_res.get("positive_count", 0), news_res.get("negative_count", 0), news_res.get("neutral_count", 0)]
        colors = ["#22C997", "#F06470", "#F2B75A"]

        fig_pie = go.Figure(data=[go.Pie(
            labels=labels, values=counts, hole=0.55,
            marker=dict(colors=colors), textinfo="label+percent"
        )])
        fig_pie.update_layout(
            paper_bgcolor=COLOR_CARD_BG, plot_bgcolor=COLOR_CARD_BG,
            font=dict(color="#F1F5F9"), margin=dict(l=20, r=20, t=20, b=20),
            showlegend=False
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_feed:
        st.markdown("##### Processed Corporate Headlines")
        if not articles:
            st.info("No articles retrieved for this selection.")
        else:
            for a in articles:
                badge_style = "badge-live" if a.get("sentiment_label") == "Positive" else ("badge-offline" if a.get("sentiment_label") == "Negative" else "badge-sample")
                st.markdown(
                    f"<div class='finsight-card' style='padding: 14px 18px; margin-bottom: 12px;'>"
                    f"<div style='display:flex; justify-content:space-between; align-items:center;'>"
                    f"<span style='font-size:0.78rem; color:#94A3B8;'>{a.get('source')} • {a.get('published_at', '')[:16]} • <b>{a.get('symbol', 'General')}</b></span>"
                    f"<span class='badge {badge_style}'>{a.get('sentiment_label')} ({a.get('confidence', 0.0)*100:.0f}%)</span>"
                    f"</div>"
                    f"<div style='font-weight:600; font-size:0.95rem; margin-top:6px; color:#F1F5F9;'>{a.get('headline')}</div>"
                    f"<div style='font-size:0.8rem; color:#94A3B8; margin-top:4px;'>Compound Score: {a.get('compound_score', 0.0):+.2f} | Model: TFIDF_LOGREG</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )

if __name__ == "__main__":
    show()
