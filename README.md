# FinSight AI 📈
### Intelligent Stock Market Prediction, Financial Analytics & Portfolio Planning Platform

[![Python Version](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Streamlit-1.67%2B-red.svg)](https://streamlit.io/)
[![Database](https://img.shields.io/badge/Database-PostgreSQL%20%2F%20SQLite-green.svg)](https://www.postgresql.org/)
[![ML Tracking](https://img.shields.io/badge/MLflow-Tracking-orange.svg)](https://mlflow.org/)
[![Tests](https://img.shields.io/badge/Tests-32%20Passed-brightgreen.svg)]()

FinSight AI is a quantitative financial intelligence and investment simulation platform supporting **both Indian equity markets (NSE/BSE)** and **US equity markets (NYSE/NASDAQ)**.

Built as an institutional-grade portfolio project, FinSight AI combines real-time and cached market data adapters, machine learning return forecasting, unsupervised market regime discovery, NLP financial sentiment intelligence, Markowitz portfolio optimization, walk-forward strategy backtesting, persistent paper portfolio tracking, and an interactive dark quantitative dashboard.

---

## 🌟 Key Application Features

### 1. Executive Market Overview (`01_overview.py`)
- Real-time benchmark index tracking (**NIFTY 50** for India, **S&P 500** for the US).
- Top market movers (gainers and decliners).
- Realized annualized volatility gauge and market health status.
- Simulated paper portfolio NAV and all-time return.
- Watchlist summary cards and recent financial news feeds.

### 2. Stock Intelligence (`02_stock_intelligence.py`)
- Deep company profiles, market cap, and business descriptions.
- TradingView-style interactive candlestick charts with custom lookbacks.
- Technical overlays: SMA (20, 50, 200), EMA (12, 26), Bollinger Bands ($\pm 2\sigma$), Wilder RSI (14), MACD (12, 26, 9), and ATR.
- Multi-year financial statements (Income Statement & Balance Sheet) and operational ratios (P/E, P/B, P/S, Debt/Equity, ROE, ROA, Net Margin, Dividend Yield).
- One-click addition to personal watchlists.

### 3. Prediction Center (`03_prediction_center.py`)
- **Forward Return Regression**: Ridge Regression baseline, Random Forest Regressor, and XGBoost Regressor forecasting 5-day and 20-day returns.
- **Market Direction Classification**: Logistic Regression, Random Forest, and XGBoost classifying forward moves (Bullish vs Bearish) with probability confidence.
- Strict chronological train/validation/test splits preventing future-data leakage.
- Leaderboard ranking models by MAE, RMSE, $R^2$, Directional Accuracy, Precision, Recall, F1, and ROC-AUC.
- Bar charts of feature importance rankings.

### 4. Stock Comparison (`04_stock_comparison.py`)
- Multi-ticker normalized return comparison (Base 100).
- Side-by-side comparative risk statistics (CAGR, Volatility, Sharpe, Sortino, Max Drawdown, Beta).
- Fundamental valuation multiple comparison tables.
- Interactive cross-asset correlation matrix heatmap.

### 5. Market Regime Detection (`05_market_regimes.py`)
- Unsupervised K-Means clustering on rolling returns, volatility, momentum, drawdown, and volume dynamics.
- Discovers empirical market states: *Bullish Low-Vol*, *Bearish High-Vol*, *Expansion*, and *Consolidation*.
- Price chart timeline with colored regime markers.
- Markov regime transition probability matrix.

### 6. Portfolio Planner (`06_portfolio_planner.py`)
- Mathematical portfolio optimization using SciPy constrained optimization (SLSQP).
- Three educational allocation models:
  - **Conservative**: Minimum-Variance portfolio with defensive position bounds.
  - **Balanced**: Inverse-variance risk parity balancing risk contributions.
  - **Growth-Oriented**: Maximum-Sharpe (tangency portfolio) maximizing risk-adjusted returns.
- Markowitz Efficient Frontier hyperbola curve visualization.
- Asset weight donut chart, holding breakdowns, and database persistence.

### 7. Risk Analyzer (`07_risk_analyzer.py`)
- Comprehensive risk diagnostics: Sharpe, Sortino, Beta to benchmark.
- Historical Value at Risk (VaR 95% 1-day) and Conditional Value at Risk (CVaR / Expected Shortfall).
- Interactive underwater drawdown peak-to-trough charts.
- 21-day rolling volatility timelines and quantitative formula definitions.

### 8. News & Sentiment Intelligence (`08_news_sentiment.py`)
- Financial headline retrieval and company ticker association.
- Natural Language Processing (NLP) with TF-IDF n-gram vectorization and Logistic Regression classifier.
- Classifies stories into Positive, Negative, or Neutral with compound scores ($-1.0$ to $+1.0$) and confidence percentages.

### 9. Backtesting Lab (`09_backtesting_lab.py`)
- Walk-forward chronological strategy backtesting with periodic rebalancing (Monthly or Quarterly).
- Strategy models: Maximum-Sharpe, Minimum-Variance, Equal-Weight (1/N), and Inverse-Variance.
- Realistic execution frictions: configurable transaction fees and slippage.
- Strategy equity curve plotted directly against benchmark index.
- Full rebalance audit trail log.

### 10. Paper Portfolio Studio (`10_paper_portfolio.py`)
- Persistent hypothetical portfolio investing.
- Buy and sell order entry with balance checks and share validation.
- Weighted average acquisition cost calculation.
- Unrealized P&L, realized P&L, cash balance, and historical transaction ledger.

### 11. Smart Alerts (`11_smart_alerts.py`)
- Configurable alerts for price breakouts/breakdowns, volatility spikes, and drawdown limits.
- Evaluates triggers on data refresh.
- Persistent alert storage and triggered event audit logs.

### 12. Corporate Events (`12_corporate_events.py`)
- Schedule of upcoming earnings releases, dividend ex-dates, splits, and shareholder meetings.
- Displays corporate details, dates, and provider attribution.

### 13. ML Laboratory (`13_ml_laboratory.py`)
- MLflow-integrated experiment tracking.
- Logs parameters, metrics, run IDs, and artifact paths.
- Compares experiments across regression, classification, and clustering runs.

### 14. Settings & Integration Center (`14_settings.py`)
- Live provider key configuration (FMP and Alpha Vantage).
- Offline sample development mode toggle.
- Disk and memory cache manager with one-click cache purge.
- Database connection diagnostics.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Language** | Python 3.11+ / Python 3.13 |
| **User Interface** | Streamlit, Plotly, Custom CSS (`#0B1020` Institutional Dark Palette) |
| **Data Processing** | Pandas, NumPy, Requests |
| **Data Providers** | Financial Modeling Prep (FMP), Alpha Vantage, Offline Sample Provider |
| **Machine Learning** | Scikit-learn, XGBoost, TF-IDF, Joblib |
| **Quantitative Finance**| SciPy (SLSQP constrained optimization), PyPortfolioOpt patterns |
| **Database** | PostgreSQL & SQLite via SQLAlchemy 2.0 ORM, Alembic Migrations |
| **ML Tracking** | MLflow Experiment Tracking & Model Registry |
| **Testing** | Pytest (32 Unit & Integration Tests) |

---

## 🚀 Quickstart Guide

### 1. Clone & Set Up Virtual Environment

```bash
git clone https://github.com/your-username/finsightAI.git
cd finsightAI

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(Optional)* Add your **FMP** or **Alpha Vantage** API keys. If left blank, FinSight AI automatically runs in its **high-fidelity Offline Sample Data Mode** with pre-generated multi-year historical data for both Indian and US markets.

### 4. Initialize Database & Generate Sample Data

```bash
# Generate multi-year sample prices, fundamentals & news
python scripts/generate_sample_data.py

# Apply database migrations
alembic upgrade head
```

### 5. Launch Application

```bash
streamlit run app/main.py
```
Open your browser at `http://localhost:8501`.

---

## 🧪 Running Tests

FinSight AI includes a comprehensive Pytest test suite covering financial risk calculations, technical indicators, portfolio optimization, machine learning models, database persistence, and data providers:

```bash
pytest -v
```

**Result:**
```
======================= 32 passed in ~24s =======================
```

---

## 🏛️ Educational Disclaimer
FinSight AI is built strictly for financial research, investment simulation, and machine learning portfolio evaluation. It does not execute real-money trades, connect to brokerage accounts, or provide guaranteed investment returns. All forecasts represent statistical expected values conditional on historical indicators.
