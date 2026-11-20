"""
FinSight AI - Professional Dark Financial Analytics UI Theme
"""

CUSTOM_CSS = """
<style>
/* Import Inter Font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* Global Reset & Base Styling */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #F1F5F9;
    background-color: #0B1020;
}

/* Streamlit Main Container */
.stApp {
    background-color: #0B1020;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: #0E1728 !important;
    border-right: 1px solid #26364B;
}

[data-testid="stSidebar"] hr {
    border-color: #26364B;
}

/* Header & Top Bar */
header[data-testid="stHeader"] {
    background: rgba(11, 16, 32, 0.85);
    backdrop-filter: blur(8px);
    border-bottom: 1px solid #26364B;
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
    color: #F1F5F9 !important;
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    letter-spacing: -0.02em;
}

/* Financial KPI Card */
.finsight-card {
    background: #121E30;
    border: 1px solid #26364B;
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 16px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    transition: transform 0.15s ease, border-color 0.15s ease;
}

.finsight-card:hover {
    border-color: #39D6A0;
}

.finsight-card-label {
    font-size: 0.78rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #94A3B8;
    margin-bottom: 6px;
}

.finsight-card-value {
    font-size: 1.65rem;
    font-weight: 700;
    color: #F1F5F9;
    font-feature-settings: "tnum";
    font-variant-numeric: tabular-nums;
    line-height: 1.2;
}

.finsight-card-delta-pos {
    font-size: 0.82rem;
    font-weight: 600;
    color: #22C997;
    margin-top: 4px;
}

.finsight-card-delta-neg {
    font-size: 0.82rem;
    font-weight: 600;
    color: #F06470;
    margin-top: 4px;
}

.finsight-card-delta-neutral {
    font-size: 0.82rem;
    font-weight: 500;
    color: #94A3B8;
    margin-top: 4px;
}

/* Status Badges */
.badge {
    display: inline-block;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.badge-live {
    background: rgba(34, 201, 151, 0.15);
    color: #22C997;
    border: 1px solid rgba(34, 201, 151, 0.3);
}

.badge-cached {
    background: rgba(75, 155, 255, 0.15);
    color: #4B9BFF;
    border: 1px solid rgba(75, 155, 255, 0.3);
}

.badge-sample {
    background: rgba(242, 183, 90, 0.15);
    color: #F2B75A;
    border: 1px solid rgba(242, 183, 90, 0.3);
}

.badge-offline {
    background: rgba(240, 100, 112, 0.15);
    color: #F06470;
    border: 1px solid rgba(240, 100, 112, 0.3);
}

/* Section Header */
.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 10px;
    margin-bottom: 18px;
    border-bottom: 1px solid #26364B;
}

.section-title {
    font-size: 1.15rem;
    font-weight: 600;
    color: #F1F5F9;
}

.section-subtitle {
    font-size: 0.82rem;
    color: #94A3B8;
}

/* Streamlit Inputs & Buttons */
.stButton > button {
    background-color: #18263A;
    color: #F1F5F9;
    border: 1px solid #26364B;
    border-radius: 6px;
    font-weight: 500;
    padding: 6px 16px;
    transition: all 0.15s ease;
}

.stButton > button:hover {
    background-color: #39D6A0;
    color: #0B1020;
    border-color: #39D6A0;
}

.stButton > button:active {
    transform: scale(0.98);
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    border-bottom: 1px solid #26364B;
    background-color: transparent;
}

.stTabs [data-baseweb="tab"] {
    background-color: transparent;
    color: #94A3B8;
    border-radius: 6px 6px 0 0;
    padding: 8px 16px;
    font-weight: 500;
    border: none;
}

.stTabs [aria-selected="true"] {
    color: #39D6A0 !important;
    border-bottom: 2px solid #39D6A0 !important;
    background-color: rgba(57, 214, 160, 0.05) !important;
}

/* Tables & Dataframes */
div[data-testid="stDataFrame"] {
    border: 1px solid #26364B;
    border-radius: 8px;
    overflow: hidden;
    background-color: #121E30;
}

/* Metrics */
[data-testid="stMetricValue"] {
    font-family: 'Inter', sans-serif !important;
    font-feature-settings: "tnum";
    font-variant-numeric: tabular-nums;
    color: #F1F5F9 !important;
}

[data-testid="stMetricLabel"] {
    color: #94A3B8 !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.04em !important;
}

/* Tooltip / Info box */
.stAlert {
    background-color: #121E30;
    border: 1px solid #26364B;
    color: #F1F5F9;
    border-radius: 8px;
}
</style>
"""

def inject_custom_css():
    """Returns the CSS string to be injected via st.markdown(..., unsafe_allow_html=True)"""
    return CUSTOM_CSS
