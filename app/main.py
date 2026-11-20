"""
FinSight AI - Central Application Entry Point
Configures Streamlit navigation using st.Page and st.navigation with cohesive dark financial UI.
"""
import streamlit as st
from app.core.styles import inject_custom_css
from app.database.connection import init_db
from app.database.repository import Repository
from app.core.constants import COLOR_MAIN_BG

# Set page configuration
st.set_page_config(
    page_title="FinSight AI - Financial Analytics & Portfolio Planning",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom CSS
st.markdown(inject_custom_css(), unsafe_allow_html=True)

# Initialize Database & seed defaults
try:
    init_db()
    Repository.get_or_create_default_user()
    Repository.seed_stock_symbols()
except Exception as e:
    st.sidebar.error(f"DB Error: {e}")

# Sidebar Brand Header
with st.sidebar:
    st.markdown(
        """
        <div style="padding: 10px 0 16px 0; border-bottom: 1px solid #26364B; margin-bottom: 16px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="background: #39D6A0; width: 14px; height: 14px; border-radius: 3px;"></div>
                <span style="font-size: 1.3rem; font-weight: 700; letter-spacing: -0.02em; color: #F1F5F9;">FinSight AI</span>
            </div>
            <div style="font-size: 0.72rem; color: #94A3B8; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.05em;">
                Institutional Financial Intelligence
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# Define pages using modern st.Page architecture
page_overview = st.Page("pages/01_overview.py", title="Executive Overview", icon="📊", default=True)
page_stock = st.Page("pages/02_stock_intelligence.py", title="Stock Intelligence", icon="📈")
page_comparison = st.Page("pages/04_stock_comparison.py", title="Peer Comparison", icon="⚖️")
page_events = st.Page("pages/12_corporate_events.py", title="Corporate Events", icon="📅")

page_prediction = st.Page("pages/03_prediction_center.py", title="Prediction Center", icon="🔮")
page_regimes = st.Page("pages/05_market_regimes.py", title="Market Regimes", icon="🌊")
page_sentiment = st.Page("pages/08_news_sentiment.py", title="News & Sentiment", icon="📰")
page_ml_lab = st.Page("pages/13_ml_laboratory.py", title="ML Laboratory", icon="🧪")

page_planner = st.Page("pages/06_portfolio_planner.py", title="Portfolio Planner", icon="💼")
page_risk = st.Page("pages/07_risk_analyzer.py", title="Risk Analyzer", icon="🛡️")
page_backtesting = st.Page("pages/09_backtesting_lab.py", title="Backtesting Lab", icon="⏪")
page_paper = st.Page("pages/10_paper_portfolio.py", title="Paper Portfolio", icon="📝")
page_alerts = st.Page("pages/11_smart_alerts.py", title="Smart Alerts", icon="🔔")

page_settings = st.Page("pages/14_settings.py", title="System Settings", icon="⚙️")

# Register navigation groups
nav = st.navigation({
    "Markets & Analysis": [page_overview, page_stock, page_comparison, page_events],
    "Machine Learning & NLP": [page_prediction, page_regimes, page_sentiment, page_ml_lab],
    "Portfolio & Risk Management": [page_planner, page_risk, page_backtesting, page_paper, page_alerts],
    "System": [page_settings]
})

# Sidebar Footer
with st.sidebar:
    st.markdown("---")
    st.markdown(
        """
        <div style="font-size: 0.72rem; color: #94A3B8; text-align: center;">
            FinSight AI • Version 1.0.0<br>
            Supported: NSE/BSE & NYSE/NASDAQ
        </div>
        """,
        unsafe_allow_html=True
    )

# Execute active navigation page
nav.run()
