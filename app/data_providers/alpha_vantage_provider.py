"""
FinSight AI - Alpha Vantage Data Provider
Secondary market data provider adapter.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import requests
import pandas as pd

from app.core.logger import logger
from app.data_providers.base import (
    BaseMarketDataProvider, MarketDataResponse, QuoteData, CompanyProfile
)
from app.data_providers.cache import cache

class AlphaVantageDataProvider(BaseMarketDataProvider):
    """Integrates with Alpha Vantage API."""

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: str):
        self.api_key = api_key.strip() if api_key else ""

    def _get(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            return None
        query = {"apikey": self.api_key}
        query.update(params)

        cache_key = f"av_{params.get('function')}_{params.get('symbol')}_{str(sorted(query.items()))}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            resp = requests.get(self.BASE_URL, params=query, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if "Note" in data:
                    logger.warning("Alpha Vantage standard API rate limit (5 calls/min) hit.")
                    return None
                if "Error Message" in data:
                    logger.warning(f"Alpha Vantage error: {data['Error Message']}")
                    return None
                cache.set(cache_key, data, ttl=300)
                return data
            return None
        except Exception as e:
            logger.error(f"Alpha Vantage request error: {e}")
            return None

    def get_quote(self, symbol: str, market: str = "IN") -> MarketDataResponse:
        data = self._get({"function": "GLOBAL_QUOTE", "symbol": symbol})
        if not data or "Global Quote" not in data or not data["Global Quote"]:
            return MarketDataResponse(data=None, provider="ALPHA_VANTAGE", is_sample=False, market=market, error="Quote unavailable.")

        q = data["Global Quote"]
        try:
            price = float(q.get("05. price", 0.0))
            change = float(q.get("09. change", 0.0))
            change_pct_str = q.get("10. change percent", "0%").replace("%", "")
            change_pct = float(change_pct_str)
            quote = QuoteData(
                symbol=symbol,
                price=price,
                change=change,
                change_percent=change_pct,
                day_high=float(q.get("03. high", price)),
                day_low=float(q.get("04. low", price)),
                volume=float(q.get("06. volume", 0.0)),
                open_price=float(q.get("02. open", price)),
                prev_close=float(q.get("08. previous close", price)),
                currency="INR" if market == "IN" else "USD",
                timestamp=datetime.now(timezone.utc)
            )
            return MarketDataResponse(data=quote, provider="ALPHA_VANTAGE", is_sample=False, market=market)
        except Exception as e:
            return MarketDataResponse(data=None, provider="ALPHA_VANTAGE", is_sample=False, error=str(e))

    def get_historical_ohlcv(
        self,
        symbol: str,
        market: str = "IN",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = "1d"
    ) -> MarketDataResponse:
        data = self._get({"function": "TIME_SERIES_DAILY", "symbol": symbol, "outputsize": "full"})
        if not data or "Time Series (Daily)" not in data:
            return MarketDataResponse(data=None, provider="ALPHA_VANTAGE", is_sample=False, market=market, error="Historical series unavailable.")

        ts = data["Time Series (Daily)"]
        rows = []
        for d_str, vals in ts.items():
            rows.append({
                "Date": d_str,
                "Open": float(vals.get("1. open", 0.0)),
                "High": float(vals.get("2. high", 0.0)),
                "Low": float(vals.get("3. low", 0.0)),
                "Close": float(vals.get("4. close", 0.0)),
                "Adj Close": float(vals.get("4. close", 0.0)),
                "Volume": float(vals.get("5. volume", 0.0))
            })

        df = pd.DataFrame(rows)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date").reset_index(drop=True)
        if start_date:
            df = df[df["Date"] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df["Date"] <= pd.to_datetime(end_date)]
        df.set_index("Date", inplace=True)

        return MarketDataResponse(data=df, provider="ALPHA_VANTAGE", is_sample=False, market=market)

    def get_company_profile(self, symbol: str, market: str = "IN") -> MarketDataResponse:
        data = self._get({"function": "OVERVIEW", "symbol": symbol})
        if not data:
            return MarketDataResponse(data=None, provider="ALPHA_VANTAGE", is_sample=False, market=market, error="Overview unavailable.")

        profile = CompanyProfile(
            symbol=symbol,
            name=data.get("Name", symbol),
            exchange=data.get("Exchange", "Exchange"),
            market=market,
            currency=data.get("Currency", "USD"),
            sector=data.get("Sector", "General"),
            industry=data.get("Industry", "General"),
            description=data.get("Description"),
            country=data.get("Country"),
            market_cap=float(data.get("MarketCapitalization", 0.0)) if data.get("MarketCapitalization") else None
        )
        return MarketDataResponse(data=profile, provider="ALPHA_VANTAGE", is_sample=False, market=market)

    def get_financial_ratios(self, symbol: str, market: str = "IN") -> MarketDataResponse:
        data = self._get({"function": "OVERVIEW", "symbol": symbol})
        if not data:
            return MarketDataResponse(data=None, provider="ALPHA_VANTAGE", is_sample=False, market=market, error="Overview unavailable.")

        def safe_float(v):
            try:
                return float(v)
            except (ValueError, TypeError):
                return None

        ratios = {
            "pe_ratio": safe_float(data.get("PERatio")),
            "pb_ratio": safe_float(data.get("PriceToBookRatio")),
            "ps_ratio": safe_float(data.get("PriceToSalesRatioTTM")),
            "debt_to_equity": None,
            "roe": safe_float(data.get("ReturnOnEquityTTM")),
            "roa": safe_float(data.get("ReturnOnAssetsTTM")),
            "net_margin": safe_float(data.get("ProfitMargin")),
            "dividend_yield": safe_float(data.get("DividendYield")),
            "market": market
        }
        return MarketDataResponse(data=ratios, provider="ALPHA_VANTAGE", is_sample=False, market=market)

    def get_financial_statements(self, symbol: str, market: str = "IN") -> MarketDataResponse:
        income_data = self._get({"function": "INCOME_STATEMENT", "symbol": symbol}) or {}
        reports = income_data.get("annualReports", [])[:4]
        stmts = {
            "income_statement": [
                {"year": r.get("fiscalDateEnding", "")[:4],
                 "revenue": float(r.get("totalRevenue", 0)),
                 "operating_income": float(r.get("operatingIncome", 0)),
                 "net_income": float(r.get("netIncome", 0))}
                for r in reports
            ],
            "balance_sheet": []
        }
        return MarketDataResponse(data=stmts, provider="ALPHA_VANTAGE", is_sample=False, market=market)

    def get_news(self, symbol: Optional[str] = None, market: str = "IN", limit: int = 15) -> MarketDataResponse:
        params = {"function": "NEWS_SENTIMENT", "limit": limit}
        if symbol:
            params["tickers"] = symbol
        data = self._get(params)
        if not data or "feed" not in data:
            return MarketDataResponse(data=[], provider="ALPHA_VANTAGE", is_sample=False, market=market)

        news = []
        for item in data["feed"][:limit]:
            news.append({
                "headline": item.get("title"),
                "symbol": symbol,
                "market": market,
                "source": item.get("source"),
                "published_at": item.get("time_published"),
                "url": item.get("url"),
                "summary": item.get("summary")
            })
        return MarketDataResponse(data=news, provider="ALPHA_VANTAGE", is_sample=False, market=market)

    def get_corporate_events(self, symbol: Optional[str] = None, market: str = "IN") -> MarketDataResponse:
        return MarketDataResponse(data=[], provider="ALPHA_VANTAGE", is_sample=False, market=market)

    def get_exchange_rate(self, from_currency: str = "USD", to_currency: str = "INR") -> MarketDataResponse:
        data = self._get({"function": "CURRENCY_EXCHANGE_RATE", "from_currency": from_currency, "to_currency": to_currency})
        rate = 84.0
        if data and "Realtime Currency Exchange Rate" in data:
            rate = float(data["Realtime Currency Exchange Rate"].get("5. Exchange Rate", 84.0))
        return MarketDataResponse(data={"rate": rate, "from": from_currency, "to": to_currency}, provider="ALPHA_VANTAGE", is_sample=False)

    def search_symbols(self, query: str, market: str = "IN") -> List[Dict[str, Any]]:
        data = self._get({"function": "SYMBOL_SEARCH", "keywords": query})
        if not data or "bestMatches" not in data:
            return []
        return [{"symbol": m.get("1. symbol"), "name": m.get("2. name"), "exchange": m.get("4. region")} for m in data["bestMatches"]]

    def get_market_indices(self, market: str = "IN") -> MarketDataResponse:
        sym = "SPY" if market == "US" else "^NSEI"
        return self.get_quote(sym, market)
