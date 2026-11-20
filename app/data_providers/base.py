"""
FinSight AI - Abstract Market Data Provider Interface
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import pandas as pd

@dataclass
class MarketDataResponse:
    """Standardized response wrapper containing metadata and provenance."""
    data: Any
    provider: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_sample: bool = False
    is_cached: bool = False
    market: str = "IN"
    error: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return self.error is None and self.data is not None

@dataclass
class QuoteData:
    symbol: str
    price: float
    change: float
    change_percent: float
    day_high: float
    day_low: float
    volume: float
    open_price: float
    prev_close: float
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    currency: str = "INR"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class CompanyProfile:
    symbol: str
    name: str
    exchange: str
    market: str
    currency: str
    sector: str
    industry: str
    website: Optional[str] = None
    description: Optional[str] = None
    ceo: Optional[str] = None
    country: Optional[str] = None
    market_cap: Optional[float] = None

class BaseMarketDataProvider(ABC):
    """Abstract Base Class for all market data integrations."""

    @abstractmethod
    def get_quote(self, symbol: str, market: str = "IN") -> MarketDataResponse:
        """Fetch current stock quote."""
        pass

    @abstractmethod
    def get_historical_ohlcv(
        self,
        symbol: str,
        market: str = "IN",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = "1d"
    ) -> MarketDataResponse:
        """Fetch historical OHLCV data returned as a Pandas DataFrame indexed by Date."""
        pass

    @abstractmethod
    def get_company_profile(self, symbol: str, market: str = "IN") -> MarketDataResponse:
        """Fetch company profile and overview information."""
        pass

    @abstractmethod
    def get_financial_ratios(self, symbol: str, market: str = "IN") -> MarketDataResponse:
        """Fetch key financial metrics & ratios."""
        pass

    @abstractmethod
    def get_financial_statements(self, symbol: str, market: str = "IN") -> MarketDataResponse:
        """Fetch balance sheet, income statement, cash flow summary."""
        pass

    @abstractmethod
    def get_news(self, symbol: Optional[str] = None, market: str = "IN", limit: int = 15) -> MarketDataResponse:
        """Fetch relevant financial news articles."""
        pass

    @abstractmethod
    def get_corporate_events(self, symbol: Optional[str] = None, market: str = "IN") -> MarketDataResponse:
        """Fetch earnings dates, dividends, splits."""
        pass

    @abstractmethod
    def get_exchange_rate(self, from_currency: str = "USD", to_currency: str = "INR") -> MarketDataResponse:
        """Fetch forex conversion rate."""
        pass

    @abstractmethod
    def search_symbols(self, query: str, market: str = "IN") -> List[Dict[str, Any]]:
        """Search available tickers matching query."""
        pass

    @abstractmethod
    def get_market_indices(self, market: str = "IN") -> MarketDataResponse:
        """Fetch benchmark index quotes (e.g. NIFTY 50, S&P 500)."""
        pass
