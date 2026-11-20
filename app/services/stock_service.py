"""
FinSight AI - Stock Intelligence Service
"""
from typing import Dict, List, Any, Optional
import pandas as pd
from app.data_providers.factory import get_market_data_provider
from app.analytics.technical_indicators import compute_all_indicators
from app.analytics.risk_metrics import compute_portfolio_risk_profile
from app.core.constants import DEFAULT_SYMBOLS, BENCHMARKS

class StockService:
    def __init__(self):
        self.provider = get_market_data_provider()

    def get_stock_quote(self, symbol: str, market: str = "IN"):
        return self.provider.get_quote(symbol, market)

    def get_historical_data(self, symbol: str, market: str = "IN", start_date: Optional[str] = None, end_date: Optional[str] = None):
        return self.provider.get_historical_ohlcv(symbol, market, start_date, end_date)

    def get_technical_data(self, symbol: str, market: str = "IN") -> Dict[str, Any]:
        resp = self.provider.get_historical_ohlcv(symbol, market)
        if not resp.is_success or resp.data is None or len(resp.data) == 0:
            return {"data": None, "error": resp.error or "No data available."}

        df_indicators = compute_all_indicators(resp.data)
        bench_sym = BENCHMARKS.get(market, "^NSEI")
        bench_resp = self.provider.get_historical_ohlcv(bench_sym, market)
        bench_series = bench_resp.data["Close"] if bench_resp.is_success and bench_resp.data is not None else None

        risk_profile = compute_portfolio_risk_profile(df_indicators["Close"], bench_series)

        return {
            "df": df_indicators,
            "risk_profile": risk_profile,
            "provider": resp.provider,
            "is_sample": resp.is_sample,
            "market": market
        }

    def get_company_details(self, symbol: str, market: str = "IN") -> Dict[str, Any]:
        profile_resp = self.provider.get_company_profile(symbol, market)
        ratios_resp = self.provider.get_financial_ratios(symbol, market)
        stmts_resp = self.provider.get_financial_statements(symbol, market)

        return {
            "profile": profile_resp.data if profile_resp.is_success else None,
            "ratios": ratios_resp.data if ratios_resp.is_success else {},
            "statements": stmts_resp.data if stmts_resp.is_success else {},
            "is_sample": profile_resp.is_sample
        }

    def get_market_overview(self, market: str = "IN") -> Dict[str, Any]:
        index_resp = self.provider.get_market_indices(market)
        symbols = DEFAULT_SYMBOLS.get(market, [])
        quotes = []
        for s in symbols:
            q_resp = self.provider.get_quote(s["symbol"], market)
            if q_resp.is_success and q_resp.data is not None:
                quotes.append(q_resp.data)

        # Gainers & Losers
        sorted_quotes = sorted(quotes, key=lambda x: x.change_percent, reverse=True)
        gainers = [q for q in sorted_quotes if q.change_percent > 0][:5]
        losers = [q for q in sorted_quotes if q.change_percent < 0][-5:]

        return {
            "index_quote": index_resp.data if index_resp.is_success else None,
            "all_quotes": quotes,
            "gainers": gainers,
            "losers": losers,
            "is_sample": index_resp.is_sample
        }

    def search_stocks(self, query: str, market: str = "IN") -> List[Dict[str, Any]]:
        return self.provider.search_symbols(query, market)

stock_service = StockService()
