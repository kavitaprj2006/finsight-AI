"""
FinSight AI - Offline Sample Market Data Provider
Provides robust, high-fidelity sample market data for offline development,
testing, and guaranteed reproducibility without requiring live API keys.
All outputs are clearly tagged with is_sample=True.
"""
import os
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np

from app.config import settings
from app.core.logger import logger
from app.core.constants import DEFAULT_SYMBOLS, BENCHMARKS
from app.data_providers.base import (
    BaseMarketDataProvider, MarketDataResponse, QuoteData, CompanyProfile
)

class OfflineDataProvider(BaseMarketDataProvider):
    """Fallback provider serving realistic local sample datasets."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or settings.SAMPLE_PRICES_DIR
        self.fundamentals_dir = settings.SAMPLE_FUNDAMENTALS_DIR
        self.news_dir = settings.SAMPLE_NEWS_DIR

    def _normalize_filename(self, symbol: str) -> str:
        return symbol.replace("^", "IDX_").replace(".", "_") + ".csv"

    def get_quote(self, symbol: str, market: str = "IN") -> MarketDataResponse:
        csv_file = self.data_dir / self._normalize_filename(symbol)
        currency = "INR" if market == "IN" else "USD"

        if not csv_file.exists():
            return MarketDataResponse(
                data=None,
                provider="OFFLINE_SAMPLE",
                is_sample=True,
                market=market,
                error=f"Symbol '{symbol}' not found in sample price database."
            )

        try:
            df = pd.read_csv(csv_file)
            if df.empty or len(df) < 2:
                return MarketDataResponse(data=None, provider="OFFLINE_SAMPLE", is_sample=True, error="Insufficient data.")

            last_row = df.iloc[-1]
            prev_row = df.iloc[-2]
            price = float(last_row["Close"])
            prev_close = float(prev_row["Close"])
            change = price - prev_close
            change_pct = (change / prev_close) * 100.0 if prev_close else 0.0

            quote = QuoteData(
                symbol=symbol,
                price=round(price, 2),
                change=round(change, 2),
                change_percent=round(change_pct, 2),
                day_high=round(float(last_row["High"]), 2),
                day_low=round(float(last_row["Low"]), 2),
                volume=float(last_row["Volume"]),
                open_price=round(float(last_row["Open"]), 2),
                prev_close=round(prev_close, 2),
                currency=currency,
                timestamp=datetime.now(timezone.utc)
            )

            return MarketDataResponse(
                data=quote,
                provider="OFFLINE_SAMPLE",
                is_sample=True,
                is_cached=False,
                market=market
            )
        except Exception as e:
            logger.error(f"Error reading sample quote for {symbol}: {e}")
            return MarketDataResponse(data=None, provider="OFFLINE_SAMPLE", is_sample=True, error=str(e))

    def get_historical_ohlcv(
        self,
        symbol: str,
        market: str = "IN",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = "1d"
    ) -> MarketDataResponse:
        csv_file = self.data_dir / self._normalize_filename(symbol)
        if not csv_file.exists():
            return MarketDataResponse(
                data=None,
                provider="OFFLINE_SAMPLE",
                is_sample=True,
                market=market,
                error=f"No historical price file for {symbol}."
            )

        try:
            df = pd.read_csv(csv_file)
            df["Date"] = pd.to_datetime(df["Date"])
            df = df.sort_values("Date").reset_index(drop=True)

            if start_date:
                df = df[df["Date"] >= pd.to_datetime(start_date)]
            if end_date:
                df = df[df["Date"] <= pd.to_datetime(end_date)]

            df.set_index("Date", inplace=True)

            return MarketDataResponse(
                data=df,
                provider="OFFLINE_SAMPLE",
                is_sample=True,
                is_cached=False,
                market=market
            )
        except Exception as e:
            logger.error(f"Error loading historical data for {symbol}: {e}")
            return MarketDataResponse(data=None, provider="OFFLINE_SAMPLE", is_sample=True, error=str(e))

    def get_company_profile(self, symbol: str, market: str = "IN") -> MarketDataResponse:
        currency = "INR" if market == "IN" else "USD"
        all_syms = DEFAULT_SYMBOLS.get(market, [])
        found = next((s for s in all_syms if s["symbol"] == symbol), None)
        
        name = found["name"] if found else symbol
        exchange = found["exchange"] if found else ("NSE" if market == "IN" else "NASDAQ")
        sector = found["sector"] if found else "General"

        profile = CompanyProfile(
            symbol=symbol,
            name=name,
            exchange=exchange,
            market=market,
            currency=currency,
            sector=sector,
            industry=f"{sector} Industry",
            website=f"https://www.{symbol.lower().replace('.', '')}.com",
            description=f"{name} is a leading enterprise operating in the {sector} sector.",
            country="India" if market == "IN" else "United States",
            market_cap=1500000000000.0 if market == "IN" else 250000000000.0
        )
        return MarketDataResponse(data=profile, provider="OFFLINE_SAMPLE", is_sample=True, market=market)

    def get_financial_ratios(self, symbol: str, market: str = "IN") -> MarketDataResponse:
        fund_file = self.fundamentals_dir / "fundamentals.json"
        if fund_file.exists():
            try:
                with open(fund_file, "r") as f:
                    data = json.load(f)
                if symbol in data:
                    return MarketDataResponse(data=data[symbol], provider="OFFLINE_SAMPLE", is_sample=True, market=market)
            except Exception as e:
                logger.warning(f"Error loading sample fundamentals: {e}")

        # Default fallback ratios
        defaults = {
            "pe_ratio": 24.5, "pb_ratio": 3.8, "ps_ratio": 4.1,
            "debt_to_equity": 0.35, "roe": 0.185, "roa": 0.092,
            "net_margin": 0.142, "dividend_yield": 0.012,
            "revenue": 50000000000, "net_income": 7100000000,
            "market_cap": 250000000000, "currency": "INR" if market == "IN" else "USD",
            "market": market
        }
        return MarketDataResponse(data=defaults, provider="OFFLINE_SAMPLE", is_sample=True, market=market)

    def get_financial_statements(self, symbol: str, market: str = "IN") -> MarketDataResponse:
        years = ["2021", "2022", "2023", "2024"]
        scale = 1000000000 if market == "IN" else 100000000
        
        income_stmt = [
            {"year": y, "revenue": round(50 * scale * (1.1 ** i), 2),
             "operating_income": round(15 * scale * (1.12 ** i), 2),
             "net_income": round(10 * scale * (1.11 ** i), 2)}
            for i, y in enumerate(years)
        ]
        balance_sheet = [
            {"year": y, "total_assets": round(120 * scale * (1.08 ** i), 2),
             "total_liabilities": round(40 * scale * (1.05 ** i), 2),
             "total_equity": round(80 * scale * (1.10 ** i), 2)}
            for i, y in enumerate(years)
        ]
        statements = {"income_statement": income_stmt, "balance_sheet": balance_sheet}
        return MarketDataResponse(data=statements, provider="OFFLINE_SAMPLE", is_sample=True, market=market)

    def get_news(self, symbol: Optional[str] = None, market: str = "IN", limit: int = 15) -> MarketDataResponse:
        news_file = self.news_dir / "news.json"
        if news_file.exists():
            try:
                with open(news_file, "r") as f:
                    all_news = json.load(f)
                
                filtered = [n for n in all_news if n.get("market") == market]
                if symbol:
                    sym_filtered = [n for n in filtered if n.get("symbol") == symbol]
                    if sym_filtered:
                        filtered = sym_filtered
                return MarketDataResponse(data=filtered[:limit], provider="OFFLINE_SAMPLE", is_sample=True, market=market)
            except Exception as e:
                logger.error(f"Error loading sample news: {e}")

        return MarketDataResponse(data=[], provider="OFFLINE_SAMPLE", is_sample=True, market=market)

    def get_corporate_events(self, symbol: Optional[str] = None, market: str = "IN") -> MarketDataResponse:
        now = datetime.now()
        events = [
            {"symbol": "RELIANCE.NS", "market": "IN", "event_type": "Earnings Announcement", "event_date": (now + timedelta(days=14)).strftime("%Y-%m-%d"), "details": "Q3 FY26 Financial Results"},
            {"symbol": "TCS.NS", "market": "IN", "event_type": "Dividend Ex-Date", "event_date": (now + timedelta(days=8)).strftime("%Y-%m-%d"), "details": "Interim Dividend ₹12.00 per share"},
            {"symbol": "HDFCBANK.NS", "market": "IN", "event_type": "Annual General Meeting", "event_date": (now + timedelta(days=22)).strftime("%Y-%m-%d"), "details": "Shareholder approval for debt issuance"},
            {"symbol": "AAPL", "market": "US", "event_type": "Earnings Announcement", "event_date": (now + timedelta(days=12)).strftime("%Y-%m-%d"), "details": "Q1 2026 Earnings Call & Guidance"},
            {"symbol": "NVDA", "market": "US", "event_type": "Product Keynote", "event_date": (now + timedelta(days=5)).strftime("%Y-%m-%d"), "details": "GTC AI Developer Conference Keynote"},
            {"symbol": "MSFT", "market": "US", "event_type": "Dividend Ex-Date", "event_date": (now + timedelta(days=18)).strftime("%Y-%m-%d"), "details": "Quarterly Dividend $0.75 per share"},
        ]
        filtered = [e for e in events if e["market"] == market]
        if symbol:
            filtered = [e for e in filtered if e["symbol"] == symbol]
        return MarketDataResponse(data=filtered, provider="OFFLINE_SAMPLE", is_sample=True, market=market)

    def get_exchange_rate(self, from_currency: str = "USD", to_currency: str = "INR") -> MarketDataResponse:
        rate = 84.25 if from_currency == "USD" and to_currency == "INR" else (1.0 / 84.25 if from_currency == "INR" and to_currency == "USD" else 1.0)
        return MarketDataResponse(data={"rate": rate, "from": from_currency, "to": to_currency}, provider="OFFLINE_SAMPLE", is_sample=True)

    def search_symbols(self, query: str, market: str = "IN") -> List[Dict[str, Any]]:
        symbols = DEFAULT_SYMBOLS.get(market, [])
        q = query.lower()
        matches = [s for s in symbols if q in s["symbol"].lower() or q in s["name"].lower()]
        return matches

    def get_market_indices(self, market: str = "IN") -> MarketDataResponse:
        sym = BENCHMARKS.get(market, "^NSEI")
        return self.get_quote(sym, market)
