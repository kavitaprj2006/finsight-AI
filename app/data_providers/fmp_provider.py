"""
FinSight AI - Financial Modeling Prep (FMP) Data Provider
Primary market data provider adapter.
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

class FMPDataProvider(BaseMarketDataProvider):
    """Integrates with Financial Modeling Prep API."""

    BASE_URL = "https://financialmodelingprep.com/api/v3"

    def __init__(self, api_key: str):
        self.api_key = api_key.strip() if api_key else ""

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        if not self.api_key:
            return None
        url = f"{self.BASE_URL}/{endpoint}"
        query = {"apikey": self.api_key}
        if params:
            query.update(params)

        cache_key = f"fmp_{endpoint}_{str(sorted(query.items()))}"
        cached_val = cache.get(cache_key)
        if cached_val is not None:
            return cached_val

        try:
            resp = requests.get(url, params=query, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                # Verify not an error payload like {"Error Message": ...}
                if isinstance(data, dict) and "Error Message" in data:
                    logger.warning(f"FMP API Error: {data['Error Message']}")
                    return None
                cache.set(cache_key, data, ttl=300) # 5 min TTL for live endpoints
                return data
            else:
                logger.warning(f"FMP HTTP Error {resp.status_code}: {resp.text}")
                return None
        except Exception as e:
            logger.error(f"FMP Request Exception for {endpoint}: {e}")
            return None

    def get_quote(self, symbol: str, market: str = "IN") -> MarketDataResponse:
        fmp_symbol = symbol.replace("^", "%5E")
        data = self._get(f"quote/{fmp_symbol}")

        if not data or not isinstance(data, list) or len(data) == 0:
            return MarketDataResponse(
                data=None, provider="FMP", is_sample=False, market=market,
                error=f"No quote data returned for {symbol} from FMP."
            )

        item = data[0]
        quote = QuoteData(
            symbol=symbol,
            price=float(item.get("price", 0.0)),
            change=float(item.get("change", 0.0)),
            change_percent=float(item.get("changesPercentage", 0.0)),
            day_high=float(item.get("dayHigh", 0.0)),
            day_low=float(item.get("dayLow", 0.0)),
            volume=float(item.get("volume", 0.0)),
            open_price=float(item.get("open", 0.0)),
            prev_close=float(item.get("previousClose", 0.0)),
            market_cap=float(item.get("marketCap", 0.0)) if item.get("marketCap") else None,
            pe_ratio=float(item.get("pe", 0.0)) if item.get("pe") else None,
            currency="INR" if market == "IN" else "USD",
            timestamp=datetime.now(timezone.utc)
        )
        return MarketDataResponse(data=quote, provider="FMP", is_sample=False, market=market)

    def get_historical_ohlcv(
        self,
        symbol: str,
        market: str = "IN",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = "1d"
    ) -> MarketDataResponse:
        params = {}
        if start_date:
            params["from"] = start_date
        if end_date:
            params["to"] = end_date

        data = self._get(f"historical-price-full/{symbol}", params=params)
        if not data or "historical" not in data or not data["historical"]:
            return MarketDataResponse(
                data=None, provider="FMP", is_sample=False, market=market,
                error=f"No historical price data for {symbol}."
            )

        rows = []
        for h in data["historical"]:
            rows.append({
                "Date": h.get("date"),
                "Open": float(h.get("open", 0.0)),
                "High": float(h.get("high", 0.0)),
                "Low": float(h.get("low", 0.0)),
                "Close": float(h.get("close", 0.0)),
                "Adj Close": float(h.get("adjClose", h.get("close", 0.0))),
                "Volume": float(h.get("volume", 0.0))
            })

        df = pd.DataFrame(rows)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date").reset_index(drop=True)
        df.set_index("Date", inplace=True)

        return MarketDataResponse(data=df, provider="FMP", is_sample=False, market=market)

    def get_company_profile(self, symbol: str, market: str = "IN") -> MarketDataResponse:
        data = self._get(f"profile/{symbol}")
        if not data or not isinstance(data, list) or len(data) == 0:
            return MarketDataResponse(data=None, provider="FMP", is_sample=False, market=market, error="Profile not found.")

        p = data[0]
        profile = CompanyProfile(
            symbol=symbol,
            name=p.get("companyName", symbol),
            exchange=p.get("exchangeShortName", "Exchange"),
            market=market,
            currency=p.get("currency", "INR" if market == "IN" else "USD"),
            sector=p.get("sector", "General"),
            industry=p.get("industry", "General"),
            website=p.get("website"),
            description=p.get("description"),
            ceo=p.get("ceo"),
            country=p.get("country"),
            market_cap=float(p.get("mktCap", 0.0)) if p.get("mktCap") else None
        )
        return MarketDataResponse(data=profile, provider="FMP", is_sample=False, market=market)

    def get_financial_ratios(self, symbol: str, market: str = "IN") -> MarketDataResponse:
        data = self._get(f"ratios/{symbol}", params={"limit": 1})
        if not data or not isinstance(data, list) or len(data) == 0:
            return MarketDataResponse(data=None, provider="FMP", is_sample=False, market=market, error="Ratios not found.")

        r = data[0]
        ratios = {
            "pe_ratio": r.get("priceEarningsRatio"),
            "pb_ratio": r.get("priceToBookRatio"),
            "ps_ratio": r.get("priceToSalesRatio"),
            "debt_to_equity": r.get("debtEquityRatio"),
            "roe": r.get("returnOnEquity"),
            "roa": r.get("returnOnAssets"),
            "net_margin": r.get("netProfitMargin"),
            "dividend_yield": r.get("dividendYield"),
            "market": market
        }
        return MarketDataResponse(data=ratios, provider="FMP", is_sample=False, market=market)

    def get_financial_statements(self, symbol: str, market: str = "IN") -> MarketDataResponse:
        income = self._get(f"income-statement/{symbol}", params={"limit": 4}) or []
        balance = self._get(f"balance-sheet-statement/{symbol}", params={"limit": 4}) or []
        statements = {
            "income_statement": [
                {"year": i.get("calendarYear", i.get("date", "")[:4]),
                 "revenue": i.get("revenue"),
                 "operating_income": i.get("operatingIncome"),
                 "net_income": i.get("netIncome")}
                for i in income
            ],
            "balance_sheet": [
                {"year": b.get("calendarYear", b.get("date", "")[:4]),
                 "total_assets": b.get("totalAssets"),
                 "total_liabilities": b.get("totalLiabilities"),
                 "total_equity": b.get("totalStockholdersEquity")}
                for b in balance
            ]
        }
        return MarketDataResponse(data=statements, provider="FMP", is_sample=False, market=market)

    def get_news(self, symbol: Optional[str] = None, market: str = "IN", limit: int = 15) -> MarketDataResponse:
        params = {"limit": limit}
        if symbol:
            params["tickers"] = symbol
        data = self._get("stock_news", params=params)
        if not data or not isinstance(data, list):
            return MarketDataResponse(data=[], provider="FMP", is_sample=False, market=market)

        news = []
        for n in data:
            news.append({
                "headline": n.get("title"),
                "symbol": n.get("symbol", symbol),
                "market": market,
                "source": n.get("site", "Financial News"),
                "published_at": n.get("publishedDate"),
                "url": n.get("url"),
                "summary": n.get("text")
            })
        return MarketDataResponse(data=news, provider="FMP", is_sample=False, market=market)

    def get_corporate_events(self, symbol: Optional[str] = None, market: str = "IN") -> MarketDataResponse:
        # FMP Earnings Calendar
        data = self._get("historical/earning_calendar", params={"limit": 10})
        events = []
        if data and isinstance(data, list):
            for e in data:
                if not symbol or e.get("symbol") == symbol:
                    events.append({
                        "symbol": e.get("symbol"),
                        "market": market,
                        "event_type": "Earnings Announcement",
                        "event_date": e.get("date"),
                        "details": f"Estimated EPS: {e.get('epsEstimated', 'N/A')}"
                    })
        return MarketDataResponse(data=events, provider="FMP", is_sample=False, market=market)

    def get_exchange_rate(self, from_currency: str = "USD", to_currency: str = "INR") -> MarketDataResponse:
        pair = f"{from_currency}{to_currency}"
        data = self._get(f"fx/{pair}")
        rate = 84.0
        if data and isinstance(data, list) and len(data) > 0:
            rate = float(data[0].get("bid", 84.0))
        return MarketDataResponse(data={"rate": rate, "from": from_currency, "to": to_currency}, provider="FMP", is_sample=False)

    def search_symbols(self, query: str, market: str = "IN") -> List[Dict[str, Any]]:
        data = self._get("search", params={"query": query, "limit": 10})
        if not data or not isinstance(data, list):
            return []
        return [{"symbol": d.get("symbol"), "name": d.get("name"), "exchange": d.get("exchangeShortName")} for d in data]

    def get_market_indices(self, market: str = "IN") -> MarketDataResponse:
        sym = "^NSEI" if market == "IN" else "SPY"
        return self.get_quote(sym, market)
