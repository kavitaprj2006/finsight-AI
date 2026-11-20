"""
FinSight AI - Historical Strategy Backtesting Engine
Simulates multi-asset walk-forward rebalancing strategies with realistic transaction costs and slippage.
Guarantees NO look-ahead bias by optimizing solely on data preceding each rebalance date.
"""
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd

from app.analytics.portfolio_optimizer import PortfolioOptimizer
from app.analytics.risk_metrics import compute_portfolio_risk_profile
from app.core.logger import logger

class HistoricalBacktester:
    def __init__(
        self,
        prices_df: pd.DataFrame,
        benchmark_prices: Optional[pd.Series] = None,
        initial_capital: float = 100000.0,
        rebalance_interval_days: int = 21,  # ~Monthly
        transaction_cost_pct: float = 0.001, # 0.1% fee
        slippage_pct: float = 0.0005,        # 0.05% slippage
        lookback_window_days: int = 126,     # ~6 months for optimization window
        risk_free_rate: float = 0.05
    ):
        self.prices = prices_df.copy().sort_index()
        self.benchmark = benchmark_prices.copy().sort_index() if benchmark_prices is not None else None
        self.initial_capital = initial_capital
        self.rebalance_interval = max(5, rebalance_interval_days)
        self.fee_rate = transaction_cost_pct + slippage_pct
        self.lookback_window = lookback_window_days
        self.risk_free_rate = risk_free_rate
        self.symbols = list(self.prices.columns)

    def run(self, strategy: str = "MAX_SHARPE", max_weight: float = 0.40) -> Dict[str, Any]:
        """
        Executes chronological backtest walk-forward.
        Strategies supported: 'EQUAL_WEIGHT', 'MIN_VAR', 'MAX_SHARPE', 'INVERSE_VAR'
        """
        n_days = len(self.prices)
        if n_days <= self.lookback_window + 10:
            raise ValueError(f"Insufficient historical data: {n_days} days available, but {self.lookback_window + 10} needed.")

        dates = self.prices.index
        daily_returns = self.prices.pct_change().fillna(0.0)

        # Tracking state
        portfolio_values = [self.initial_capital]
        current_weights = np.ones(len(self.symbols)) / len(self.symbols)
        rebalance_log: List[Dict[str, Any]] = []

        # Start after initial lookback period
        start_idx = self.lookback_window

        # Compute initial weights on historical slice [0:start_idx]
        hist_slice = self.prices.iloc[:start_idx]
        current_weights = self._compute_strategy_weights(hist_slice, strategy, max_weight)
        
        rebalance_log.append({
            "date": str(dates[start_idx].date() if hasattr(dates[start_idx], 'date') else dates[start_idx]),
            "weights": {s: round(float(current_weights[i]), 4) for i, s in enumerate(self.symbols)},
            "reason": "Initial Allocation",
            "cost": float(self.initial_capital * self.fee_rate)
        })

        curr_value = self.initial_capital * (1.0 - self.fee_rate)

        # Walk-forward simulation day-by-day
        for i in range(start_idx, n_days - 1):
            day_return_vector = daily_returns.iloc[i + 1].values
            
            # Portfolio return before rebalancing
            portfolio_day_return = float(np.dot(current_weights, day_return_vector))
            curr_value = curr_value * (1.0 + portfolio_day_return)

            # Natural drift of weights due to price movements
            new_asset_values = current_weights * (1.0 + day_return_vector)
            current_weights = new_asset_values / np.sum(new_asset_values)

            # Check for scheduled rebalance
            if (i - start_idx + 1) % self.rebalance_interval == 0:
                # Rebalance using strictly data strictly up to day i (no look-ahead)
                opt_slice = self.prices.iloc[max(0, i - self.lookback_window):i + 1]
                target_weights = self._compute_strategy_weights(opt_slice, strategy, max_weight)
                
                # Turnover & transaction cost
                turnover = float(np.sum(np.abs(target_weights - current_weights)) / 2.0)
                rebalance_cost = curr_value * turnover * self.fee_rate
                curr_value -= rebalance_cost

                current_weights = target_weights
                rebalance_log.append({
                    "date": str(dates[i + 1].date() if hasattr(dates[i + 1], 'date') else dates[i + 1]),
                    "weights": {s: round(float(target_weights[j]), 4) for j, s in enumerate(self.symbols)},
                    "reason": f"Periodic Rebalance (Turnover: {turnover:.1%})",
                    "cost": float(rebalance_cost)
                })

            portfolio_values.append(curr_value)

        # Construct portfolio equity curve
        eval_dates = dates[start_idx:]
        equity_series = pd.Series(portfolio_values[:len(eval_dates)], index=eval_dates, name="Strategy")

        # Benchmark comparison series
        bench_eval = None
        if self.benchmark is not None:
            aligned_bench = self.benchmark.loc[eval_dates.intersection(self.benchmark.index)]
            if len(aligned_bench) > 0:
                bench_equity = (aligned_bench / aligned_bench.iloc[0]) * self.initial_capital
                bench_eval = bench_equity

        # Calculate performance statistics
        risk_profile = compute_portfolio_risk_profile(equity_series, bench_eval, self.risk_free_rate)

        total_return_pct = (equity_series.iloc[-1] - self.initial_capital) / self.initial_capital
        cagr = risk_profile["annualized_return"]

        # Benchmark stats
        bench_ret_pct = 0.0
        bench_cagr = 0.0
        if bench_eval is not None and len(bench_eval) > 1:
            bench_ret_pct = (bench_eval.iloc[-1] - self.initial_capital) / self.initial_capital
            bench_risk = compute_portfolio_risk_profile(bench_eval, None, self.risk_free_rate)
            bench_cagr = bench_risk["annualized_return"]

        return {
            "strategy": strategy,
            "initial_capital": self.initial_capital,
            "final_value": float(equity_series.iloc[-1]),
            "total_return_pct": float(total_return_pct),
            "cagr": float(cagr),
            "volatility": float(risk_profile["annualized_volatility"]),
            "sharpe_ratio": float(risk_profile["sharpe_ratio"]),
            "sortino_ratio": float(risk_profile["sortino_ratio"]),
            "max_drawdown": float(risk_profile["max_drawdown"]),
            "drawdown_series": risk_profile["drawdown_series"],
            "beta": float(risk_profile["beta"]),
            "equity_curve": equity_series,
            "benchmark_curve": bench_eval,
            "benchmark_return_pct": float(bench_ret_pct),
            "benchmark_cagr": float(bench_cagr),
            "rebalances": rebalance_log,
            "assumptions": {
                "rebalance_interval_days": self.rebalance_interval,
                "transaction_fee_bps": (self.fee_rate) * 10000.0,
                "lookback_window_days": self.lookback_window,
                "no_lookahead_enforced": True
            }
        }

    def _compute_strategy_weights(self, price_slice: pd.DataFrame, strategy: str, max_weight: float) -> np.ndarray:
        """Solves optimization for historical window without look-ahead."""
        opt = PortfolioOptimizer(price_slice, self.risk_free_rate)
        if strategy == "EQUAL_WEIGHT":
            res = opt.optimize_equal_weight()
        elif strategy == "MIN_VAR":
            res = opt.optimize_min_variance(max_weight=max_weight)
        elif strategy == "INVERSE_VAR":
            res = opt.optimize_inverse_variance()
        else: # Default MAX_SHARPE
            res = opt.optimize_max_sharpe(max_weight=max_weight)

        w_dict = res["weights"]
        return np.array([w_dict.get(s, 1.0 / len(self.symbols)) for s in self.symbols])
