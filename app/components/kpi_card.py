"""
FinSight AI - Financial KPI Card Component
"""
import streamlit as st
from typing import Optional

def render_kpi_card(
    label: str,
    value: str,
    delta: Optional[str] = None,
    delta_type: str = "neutral", # "positive", "negative", "neutral"
    badge_text: Optional[str] = None,
    badge_style: str = "badge-live" # "badge-live", "badge-cached", "badge-sample"
):
    """Renders a styled financial KPI card."""
    delta_html = ""
    if delta:
        css_class = {
            "positive": "finsight-card-delta-pos",
            "negative": "finsight-card-delta-neg",
            "neutral": "finsight-card-delta-neutral"
        }.get(delta_type, "finsight-card-delta-neutral")
        arrow = "▲ " if delta_type == "positive" else ("▼ " if delta_type == "negative" else "")
        delta_html = f'<div class="{css_class}">{arrow}{delta}</div>'

    badge_html = ""
    if badge_text:
        badge_html = f'<span class="badge {badge_style}">{badge_text}</span>'

    card_html = f"""
    <div class="finsight-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div class="finsight-card-label">{label}</div>
            {badge_html}
        </div>
        <div class="finsight-card-value">{value}</div>
        {delta_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)
