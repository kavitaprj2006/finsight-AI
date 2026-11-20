"""
FinSight AI - Portfolio & Asset Allocation Service
"""
from typing import Dict, List, Any, Optional
import pandas as pd
from app.data_providers.factory import get_market_data_provider
from app.analytics.portfolio_optimizer import PortfolioOptimizer
from app.database.repository import Repository
from app.core.constants import SCENARIO_CONSERVATIVE, SCENARIO_BALANCED, SCENARIO_GROWTH

class PortfolioService:
    def __init__(self):
        self.provider = get_market_data_provider()

    def fetch_price_matrix(self, symbols: List[str], market: str = "IN") -> pd.DataFrame:
        """Loads and aligns historical closing prices for multiple symbols."""
        series_dict = {}
        for s in symbols:
            resp = self.provider.get_historical_ohlcv(s, market)
            if resp.is_success and resp.data is not None and not resp.data.empty:
                series_dict[s] = resp.data["Close"]
        
        df = pd.DataFrame(series_dict).dropna()
        return df

    def generate_educational_scenarios(
        self,
        symbols: List[str],
        budget: float,
        market: str = "IN",
        max_weight: float = 0.40
    ) -> Dict[str, Any]:
        """Generates Conservative, Balanced, and Growth-Oriented educational portfolios."""
        price_df = self.fetch_price_matrix(symbols, market)
        if len(price_df.columns) < 2 or len(price_df) < 30:
            raise ValueError("At least 2 assets with >= 30 days of price history are required for optimization.")

        opt = PortfolioOptimizer(price_df)

        # 1. Conservative (Minimum-Variance, tighter position limit)
        cons_res = opt.optimize_min_variance(max_weight=min(0.35, max_weight))
        cons_assets = self._format_assets(cons_res["weights"], budget, price_df.iloc[-1])

        # 2. Balanced (Blended inverse variance / equal mix)
        bal_res = opt.optimize_inverse_variance()
        bal_assets = self._format_assets(bal_res["weights"], budget, price_df.iloc[-1])

        # 3. Growth-Oriented (Maximum Sharpe Ratio)
        growth_res = opt.optimize_max_sharpe(max_weight=max_weight)
        growth_assets = self._format_assets(growth_res["weights"], budget, price_df.iloc[-1])

        # Efficient frontier points
        frontier = opt.generate_efficient_frontier(points=20, max_weight=max_weight)

        return {
            SCENARIO_CONSERVATIVE: {
                "strategy": "Minimum-Variance",
                "expected_return": cons_res["expected_return"],
                "expected_volatility": cons_res["expected_volatility"],
                "sharpe_ratio": cons_res["sharpe_ratio"],
                "assets": cons_assets,
                "description": "Aims to minimize portfolio volatility and drawdown risk with well-diversified defensive positions."
            },
            SCENARIO_BALANCED: {
                "strategy": "Risk Parity / Balanced",
                "expected_return": bal_res["expected_return"],
                "expected_volatility": bal_res["expected_volatility"],
                "sharpe_ratio": bal_res["sharpe_ratio"],
                "assets": bal_assets,
                "description": "Balances risk across asset volatility to maintain steady long-term appreciation."
            },
            SCENARIO_GROWTH: {
                "strategy": "Maximum-Sharpe",
                "expected_return": growth_res["expected_return"],
                "expected_volatility": growth_res["expected_volatility"],
                "sharpe_ratio": growth_res["sharpe_ratio"],
                "assets": growth_assets,
                "description": "Optimizes risk-adjusted expected returns for higher capital growth tolerance."
            },
            "efficient_frontier": frontier,
            "covariance_matrix": opt.cov_matrix.to_dict(),
            "correlation_matrix": opt.returns.corr().to_dict()
        }

    def _format_assets(self, weights: Dict[str, float], budget: float, latest_prices: pd.Series) -> List[Dict[str, Any]]:
        assets = []
        for sym, w in weights.items():
            if w > 0.005: # ignore negligible weights (<0.5%)
                allocated = budget * w
                price = float(latest_prices.get(sym, 1.0))
                shares = allocated / price if price > 0 else 0
                assets.append({
                    "symbol": sym,
                    "weight": round(w, 4),
                    "allocated_amount": round(allocated, 2),
                    "current_price": round(price, 2),
                    "shares": round(shares, 2)
                })
        return assets

    def get_paper_portfolio_overview(self, portfolio_id: int) -> Dict[str, Any]:
        """Calculates current holdings, market values, and P&L for a paper portfolio."""
        holdings = Repository.get_portfolio_holdings(portfolio_id)
        txs = Repository.get_portfolio_transactions(portfolio_id)

        # Retrieve portfolio cash details from DB
        portfolios = Repository.get_paper_portfolios(user_id=1) # Default user
        curr_p = next((p for p in portfolios if p["id"] == portfolio_id), None)
        cash = curr_p["available_cash"] if curr_p else 0.0
        initial_cash = curr_p["initial_cash"] if curr_p else 100000.0
        market = curr_p["market"] if curr_p else "IN"

        total_invested_cost = 0.0
        total_market_value = 0.0
        holdings_list = []

        for sym, h in holdings.items():
            qty = h["quantity"]
            avg_cost = h["avg_cost"]
            total_cost = qty * avg_cost

            q_resp = self.provider.get_quote(sym, market)
            cur_price = q_resp.data.price if q_resp.is_success and q_resp.data is not None else avg_cost
            mkt_val = qty * cur_price
            unrealized_pnl = mkt_val - total_cost
            pnl_pct = (unrealized_pnl / total_cost) * 100.0 if total_cost > 0 else 0.0

            total_invested_cost += total_cost
            total_market_value += mkt_val

            holdings_list.append({
                "symbol": sym,
                "quantity": qty,
                "avg_cost": round(avg_cost, 2),
                "current_price": round(cur_price, 2),
                "total_cost": round(total_cost, 2),
                "market_value": round(mkt_val, 2),
                "unrealized_pnl": round(unrealized_pnl, 2),
                "pnl_percent": round(pnl_pct, 2)
            })

        total_portfolio_value = cash + total_market_value
        total_unrealized_pnl = total_market_value - total_invested_cost
        total_realized_pnl = sum(h["realized_pnl"] for h in holdings.values())
        total_pnl = (total_portfolio_value - initial_cash)
        total_return_pct = (total_pnl / initial_cash) * 100.0 if initial_cash > 0 else 0.0

        return {
            "portfolio": curr_p,
            "cash": round(cash, 2),
            "invested_value": round(total_market_value, 2),
            "total_value": round(total_portfolio_value, 2),
            "unrealized_pnl": round(total_unrealized_pnl, 2),
            "realized_pnl": round(total_realized_pnl, 2),
            "total_return_pct": round(total_return_pct, 2),
            "holdings": holdings_list,
            "recent_transactions": txs[:10]
        }

portfolio_service = PortfolioService()
