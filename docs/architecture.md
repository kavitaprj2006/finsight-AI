# FinSight AI - System Architecture

FinSight AI is an institutional financial intelligence, stock prediction, and hypothetical portfolio planning application designed for Indian (NSE/BSE) and US (NYSE/NASDAQ) equity markets.

---

## 1. High-Level Architecture

The system is structured in a clean 6-tier architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                       Streamlit UI                          │
│   (14 Modular Pages, Plotly Dark Charts, Global Theme)      │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                      Services Layer                         │
│  (StockService, PortfolioService, AlertService, NLPService)  │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
┌──────────────▼──────────────┐┌──────────────▼───────────────┐
│     Analytics & Engines     ││    Machine Learning & NLP    │
│  • SciPy SLSQP Portfolio    ││  • Walk-Forward Split        │
│  • Modern Portfolio Theory  ││  • Ridge, RF, XGBoost        │
│  • VaR, CVaR, Drawdown, Beta││  • Regime K-Means Clustering │
│  • Walk-Forward Backtester  ││  • TF-IDF Logistic Sentiment │
│  • Currency Converter       ││  • MLflow Experiment Logger  │
└──────────────┬──────────────┘└──────────────┬───────────────┘
               │                              │
┌──────────────▼──────────────────────────────▼───────────────┐
│               Data Provider Adapter Layer                   │
│  (FMP Provider, Alpha Vantage Provider, Offline Provider)   │
│               TTL Disk & In-Memory Cache                    │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                    Persistence Layer                        │
│         SQLAlchemy ORM + Alembic Schema Migrations          │
│       PostgreSQL (Production) / SQLite (Zero-Config)        │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Key Modules & Responsibilities

### Data Provider Adapters (`app/data_providers/`)
- **Abstract Base (`base.py`)**: Defines contract for quotes, historical OHLCV, company profiles, financial ratios, multi-year statements, news, and corporate actions.
- **Provenance & Metadata**: Every response is wrapped in `MarketDataResponse` specifying data source, retrieval timestamp, and explicit `is_sample` flag.
- **Provider Factory (`factory.py`)**: Auto-selects active provider (FMP vs Alpha Vantage vs Offline Provider) based on API key availability and configuration.

### Financial Analytics & Optimization (`app/analytics/`)
- **Technical Indicators (`technical_indicators.py`)**: Computes SMA (20, 50, 200), EMA (12, 26), Wilder RSI (14), MACD (12, 26, 9), Bollinger Bands ($\pm 2\sigma$), ATR, and 21-day annualized volatility.
- **Risk Metrics (`risk_metrics.py`)**: Annualized return, annualized volatility, Sharpe ratio, Sortino ratio (downside deviation), historical Value at Risk (VaR 95%), Conditional VaR (CVaR), and Beta relative to market benchmark.
- **Portfolio Optimizer (`portfolio_optimizer.py`)**: Solves constrained convex quadratic optimizations via SciPy SLSQP for:
  - Equal-Weight ($1/N$)
  - Minimum-Variance (Defensive)
  - Maximum-Sharpe (Tangency Portfolio)
  - Inverse-Variance / Risk Parity
  - Markowitz Efficient Frontier generation
- **Backtester (`backtester.py`)**: Multi-asset walk-forward simulation enforcing zero look-ahead bias and transaction fee frictions.

### Machine Learning (`app/ml/`)
- **Feature Engineering (`feature_engineering.py`)**: Constructs backward-looking momentum, lagged returns, volume ratios, and moving average distances aligned strictly with forward return targets.
- **Supervised Return Regression (`regression_models.py`)**: Trains Ridge Regression baseline, Random Forest, and XGBoost to predict 5-day and 20-day returns.
- **Supervised Direction Classification (`classification_models.py`)**: Trains Logistic Regression, Random Forest, and XGBoost to classify positive vs non-positive returns.
- **Unsupervised Market Regimes (`clustering.py`)**: K-Means clustering identifying distinct latent market regimes.
- **NLP Sentiment (`sentiment_analyzer.py`)**: TF-IDF feature extraction and Logistic Regression classifier for financial headlines.
- **MLflow Tracking (`mlflow_tracker.py`)**: Logs parameters, metrics, and models.
