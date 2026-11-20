"""
FinSight AI - SQLAlchemy Relational Database Models
"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey,
    Index, UniqueConstraint, JSON
)
from sqlalchemy.orm import relationship
from app.database.connection import Base

def utc_now():
    return datetime.now(timezone.utc)

# 1. Users
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    watchlists = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
    paper_portfolios = relationship("PaperPortfolio", back_populates="user", cascade="all, delete-orphan")
    portfolio_scenarios = relationship("PortfolioScenario", back_populates="user", cascade="all, delete-orphan")
    saved_alerts = relationship("SavedAlert", back_populates="user", cascade="all, delete-orphan")

# 2. User Preferences
class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    default_market = Column(String(10), default="IN", nullable=False)  # IN or US
    default_currency = Column(String(10), default="INR", nullable=False) # INR or USD
    dark_mode = Column(Boolean, default=True, nullable=False)
    risk_tolerance = Column(String(20), default="Moderate", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="preferences")

# 3. Stock Symbols Directory
class StockSymbol(Base):
    __tablename__ = "stock_symbols"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(30), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    market = Column(String(10), nullable=False, index=True) # IN or US
    exchange = Column(String(30), nullable=False) # NSE, BSE, NYSE, NASDAQ
    sector = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    currency = Column(String(10), default="INR", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

# 4. Market Data Metadata (Tracking source, staleness, caching)
class MarketDataMetadata(Base):
    __tablename__ = "market_data_metadata"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(30), nullable=False, index=True)
    market = Column(String(10), nullable=False)
    provider = Column(String(50), nullable=False) # FMP, ALPHA_VANTAGE, OFFLINE_SAMPLE
    data_type = Column(String(50), nullable=False) # OHLCV, QUOTE, PROFILE, FUNDAMENTALS
    is_sample_data = Column(Boolean, default=False, nullable=False)
    is_cached = Column(Boolean, default=True, nullable=False)
    last_fetched_at = Column(DateTime, default=utc_now, nullable=False)
    record_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    __table_args__ = (
        Index("idx_market_data_sym_type", "symbol", "data_type"),
    )

# 5. Watchlists
class Watchlist(Base):
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    market = Column(String(10), default="IN", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="watchlists")
    items = relationship("WatchlistItem", back_populates="watchlist", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_watchlist_name"),
    )

# 6. Watchlist Items
class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id = Column(Integer, primary_key=True, index=True)
    watchlist_id = Column(Integer, ForeignKey("watchlists.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(30), nullable=False, index=True)
    notes = Column(String(255), nullable=True)
    added_at = Column(DateTime, default=utc_now, nullable=False)

    watchlist = relationship("Watchlist", back_populates="items")

    __table_args__ = (
        UniqueConstraint("watchlist_id", "symbol", name="uq_watchlist_symbol"),
    )

# 7. Stock Fundamentals
class StockFundamental(Base):
    __tablename__ = "stock_fundamentals"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(30), nullable=False, index=True)
    market = Column(String(10), nullable=False)
    fiscal_date = Column(String(20), nullable=False)
    period = Column(String(10), default="FY", nullable=False)
    pe_ratio = Column(Float, nullable=True)
    pb_ratio = Column(Float, nullable=True)
    ps_ratio = Column(Float, nullable=True)
    debt_to_equity = Column(Float, nullable=True)
    roe = Column(Float, nullable=True)
    roa = Column(Float, nullable=True)
    net_margin = Column(Float, nullable=True)
    revenue = Column(Float, nullable=True)
    net_income = Column(Float, nullable=True)
    market_cap = Column(Float, nullable=True)
    dividend_yield = Column(Float, nullable=True)
    is_sample_data = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("symbol", "fiscal_date", "period", name="uq_fund_sym_date_period"),
    )

# 8. News Articles
class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    headline = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=True)
    source = Column(String(100), nullable=False)
    published_at = Column(DateTime, nullable=False, index=True)
    symbol = Column(String(30), nullable=True, index=True)
    market = Column(String(10), nullable=False)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    sentiment = relationship("SentimentResult", back_populates="article", uselist=False, cascade="all, delete-orphan")

# 9. Sentiment Results
class SentimentResult(Base):
    __tablename__ = "sentiment_results"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("news_articles.id", ondelete="CASCADE"), nullable=False, unique=True)
    symbol = Column(String(30), nullable=True, index=True)
    sentiment_label = Column(String(20), nullable=False) # Positive, Negative, Neutral
    compound_score = Column(Float, nullable=False) # -1.0 to +1.0
    confidence = Column(Float, nullable=False)
    model_type = Column(String(50), default="TFIDF_LOGREG", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    article = relationship("NewsArticle", back_populates="sentiment")

# 10. Prediction Records
class PredictionRecord(Base):
    __tablename__ = "prediction_records"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(30), nullable=False, index=True)
    market = Column(String(10), nullable=False)
    task_type = Column(String(30), nullable=False) # REGRESSION or CLASSIFICATION
    model_name = Column(String(50), nullable=False) # Ridge, RandomForest, XGBoost
    horizon_days = Column(Integer, nullable=False) # 5 or 20 days
    predicted_return = Column(Float, nullable=True) # Expected % change
    predicted_direction = Column(String(20), nullable=True) # UP or DOWN
    prediction_probability = Column(Float, nullable=True)
    as_of_price = Column(Float, nullable=False)
    model_version = Column(String(50), default="v1.0", nullable=False)
    features_used = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

# 11. Portfolio Scenarios (Hypothetical Allocation)
class PortfolioScenario(Base):
    __tablename__ = "portfolio_scenarios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    strategy_type = Column(String(50), nullable=False) # EQUAL_WEIGHT, MIN_VAR, MAX_SHARPE, HRP
    scenario_type = Column(String(50), default="Balanced", nullable=False) # Conservative, Balanced, Growth
    market = Column(String(10), default="IN", nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    budget = Column(Float, nullable=False)
    expected_return = Column(Float, nullable=False)
    expected_volatility = Column(Float, nullable=False)
    sharpe_ratio = Column(Float, nullable=False)
    sortino_ratio = Column(Float, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    user = relationship("User", back_populates="portfolio_scenarios")
    assets = relationship("PortfolioAsset", back_populates="scenario", cascade="all, delete-orphan")

# 12. Portfolio Assets
class PortfolioAsset(Base):
    __tablename__ = "portfolio_assets"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("portfolio_scenarios.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(30), nullable=False)
    weight = Column(Float, nullable=False) # 0.0 to 1.0
    allocated_amount = Column(Float, nullable=False)
    shares = Column(Float, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    scenario = relationship("PortfolioScenario", back_populates="assets")

# 13. Paper Portfolios (Persistent Simulated Investment Tracking)
class PaperPortfolio(Base):
    __tablename__ = "paper_portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    market = Column(String(10), default="IN", nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    initial_cash = Column(Float, default=100000.0, nullable=False)
    available_cash = Column(Float, default=100000.0, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="paper_portfolios")
    transactions = relationship("PaperTransaction", back_populates="portfolio", cascade="all, delete-orphan")
    snapshots = relationship("PortfolioSnapshot", back_populates="portfolio", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_paper_portfolio_name"),
    )

# 14. Paper Transactions
class PaperTransaction(Base):
    __tablename__ = "paper_transactions"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("paper_portfolios.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(30), nullable=False, index=True)
    transaction_type = Column(String(10), nullable=False) # BUY or SELL
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    transaction_cost = Column(Float, default=0.0, nullable=False)
    realized_pnl = Column(Float, default=0.0, nullable=False)
    notes = Column(String(255), nullable=True)
    executed_at = Column(DateTime, default=utc_now, nullable=False)

    portfolio = relationship("PaperPortfolio", back_populates="transactions")

# 15. Portfolio Snapshots (Performance History)
class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("paper_portfolios.id", ondelete="CASCADE"), nullable=False)
    snapshot_date = Column(DateTime, default=utc_now, nullable=False, index=True)
    total_value = Column(Float, nullable=False)
    cash_balance = Column(Float, nullable=False)
    invested_value = Column(Float, nullable=False)
    unrealized_pnl = Column(Float, default=0.0, nullable=False)
    daily_return = Column(Float, default=0.0, nullable=False)

    portfolio = relationship("PaperPortfolio", back_populates="snapshots")

# 16. Saved Alerts
class SavedAlert(Base):
    __tablename__ = "saved_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(30), nullable=False, index=True)
    alert_type = Column(String(30), nullable=False) # PRICE_ABOVE, PRICE_BELOW, VOLATILITY_ABOVE, DRAWDOWN_EXCEEDED
    threshold_value = Column(Float, nullable=False)
    market = Column(String(10), default="IN", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="saved_alerts")
    events = relationship("AlertEvent", back_populates="alert", cascade="all, delete-orphan")

# 17. Alert Events (Triggered history)
class AlertEvent(Base):
    __tablename__ = "alert_events"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("saved_alerts.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(30), nullable=False)
    triggered_value = Column(Float, nullable=False)
    threshold_value = Column(Float, nullable=False)
    message = Column(String(255), nullable=False)
    triggered_at = Column(DateTime, default=utc_now, nullable=False)

    alert = relationship("SavedAlert", back_populates="events")

# 18. ML Experiments Metadata
class MLExperimentMetadata(Base):
    __tablename__ = "ml_experiments_metadata"

    id = Column(Integer, primary_key=True, index=True)
    experiment_name = Column(String(100), nullable=False, index=True)
    run_id = Column(String(100), unique=True, nullable=False)
    model_name = Column(String(50), nullable=False)
    task_type = Column(String(30), nullable=False) # REGRESSION, CLASSIFICATION, CLUSTERING
    market = Column(String(10), nullable=False)
    symbol = Column(String(30), nullable=True)
    parameters = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=True)
    artifact_uri = Column(String(500), nullable=True)
    status = Column(String(30), default="FINISHED", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

# 19. Model Versions
class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(50), nullable=False, index=True)
    version = Column(String(30), nullable=False)
    task_type = Column(String(30), nullable=False)
    evaluation_score = Column(Float, nullable=True) # E.g., R2 or Accuracy
    metric_name = Column(String(30), default="R2", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    filepath = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("model_name", "version", name="uq_model_name_version"),
    )
