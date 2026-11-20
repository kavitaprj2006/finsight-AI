"""
FinSight AI - Core Constants and Color Palette
"""

# Color Palette (Dark Financial Analytics Interface)
COLOR_MAIN_BG = "#0B1020"
COLOR_SIDEBAR_BG = "#0E1728"
COLOR_CARD_BG = "#121E30"
COLOR_SECONDARY_SURFACE = "#18263A"
COLOR_PRIMARY_ACCENT = "#39D6A0"     # Mint Green
COLOR_SECONDARY_ACCENT = "#4B9BFF"   # Financial Blue
COLOR_POSITIVE = "#22C997"           # Bullish / Gain
COLOR_NEGATIVE = "#F06470"           # Bearish / Loss
COLOR_WARNING = "#F2B75A"            # Neutral / Caution
COLOR_TEXT_PRIMARY = "#F1F5F9"       # Crisp Off-White
COLOR_TEXT_SECONDARY = "#94A3B8"     # Subdued Slate
COLOR_BORDER = "#26364B"             # Card & Grid Border

# Chart Theme
PLOTLY_DARK_TEMPLATE = {
    "layout": {
        "paper_bgcolor": COLOR_CARD_BG,
        "plot_bgcolor": COLOR_CARD_BG,
        "font": {"color": COLOR_TEXT_PRIMARY, "family": "Inter, -apple-system, BlinkMacSystemFont, sans-serif"},
        "xaxis": {
            "gridcolor": COLOR_BORDER,
            "zerolinecolor": COLOR_BORDER,
            "linecolor": COLOR_BORDER,
            "tickfont": {"color": COLOR_TEXT_SECONDARY},
        },
        "yaxis": {
            "gridcolor": COLOR_BORDER,
            "zerolinecolor": COLOR_BORDER,
            "linecolor": COLOR_BORDER,
            "tickfont": {"color": COLOR_TEXT_SECONDARY},
        },
        "legend": {
            "bgcolor": "rgba(0,0,0,0)",
            "bordercolor": "rgba(0,0,0,0)",
            "font": {"color": COLOR_TEXT_PRIMARY},
        },
        "margin": {"l": 40, "r": 20, "t": 40, "b": 40},
    }
}

# Markets and Currencies
MARKET_IN = "IN"
MARKET_US = "US"
SUPPORTED_MARKETS = [MARKET_IN, MARKET_US]

CURRENCY_INR = "INR"
CURRENCY_USD = "USD"
CURRENCY_SYMBOLS = {
    CURRENCY_INR: "₹",
    CURRENCY_USD: "$",
}

# Default Symbols per Market
DEFAULT_SYMBOLS = {
    MARKET_IN: [
        {"symbol": "RELIANCE.NS", "name": "Reliance Industries Ltd", "exchange": "NSE", "sector": "Energy"},
        {"symbol": "TCS.NS", "name": "Tata Consultancy Services Ltd", "exchange": "NSE", "sector": "Technology"},
        {"symbol": "INFY.NS", "name": "Infosys Ltd", "exchange": "NSE", "sector": "Technology"},
        {"symbol": "HDFCBANK.NS", "name": "HDFC Bank Ltd", "exchange": "NSE", "sector": "Financial Services"},
        {"symbol": "ICICIBANK.NS", "name": "ICICI Bank Ltd", "exchange": "NSE", "sector": "Financial Services"},
        {"symbol": "^NSEI", "name": "NIFTY 50 Index", "exchange": "NSE", "sector": "Index"},
    ],
    MARKET_US: [
        {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ", "sector": "Technology"},
        {"symbol": "MSFT", "name": "Microsoft Corporation", "exchange": "NASDAQ", "sector": "Technology"},
        {"symbol": "GOOGL", "name": "Alphabet Inc.", "exchange": "NASDAQ", "sector": "Communication Services"},
        {"symbol": "NVDA", "name": "NVIDIA Corporation", "exchange": "NASDAQ", "sector": "Technology"},
        {"symbol": "AMZN", "name": "Amazon.com Inc.", "exchange": "NASDAQ", "sector": "Consumer Cyclical"},
        {"symbol": "SPY", "name": "SPDR S&P 500 ETF Trust", "exchange": "NYSE Arca", "sector": "Index"},
    ]
}

# Benchmarks
BENCHMARKS = {
    MARKET_IN: "^NSEI",
    MARKET_US: "SPY",
}

# Prediction Horizons
HORIZON_SHORT = 5   # 5 trading days (~1 week)
HORIZON_MEDIUM = 20 # 20 trading days (~1 month)
PREDICTION_HORIZONS = [HORIZON_SHORT, HORIZON_MEDIUM]

# Alert Types
ALERT_PRICE_ABOVE = "PRICE_ABOVE"
ALERT_PRICE_BELOW = "PRICE_BELOW"
ALERT_VOLATILITY_ABOVE = "VOLATILITY_ABOVE"
ALERT_SENTIMENT_CHANGE = "SENTIMENT_CHANGE"
ALERT_DRAWDOWN_EXCEEDED = "DRAWDOWN_EXCEEDED"
ALERT_ALLOCATION_DRIFT = "ALLOCATION_DRIFT"

# Portfolio Optimization Scenarios
SCENARIO_CONSERVATIVE = "Conservative"
SCENARIO_BALANCED = "Balanced"
SCENARIO_GROWTH = "Growth-Oriented"
PORTFOLIO_SCENARIOS = [SCENARIO_CONSERVATIVE, SCENARIO_BALANCED, SCENARIO_GROWTH]
