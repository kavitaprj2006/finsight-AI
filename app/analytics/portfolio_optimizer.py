"""
FinSight AI - Portfolio Optimization Engine
Implements Equal-Weight, Minimum-Variance, Maximum-Sharpe, and Inverse-Variance/HRP optimization
using SciPy constrained optimization (SLSQP).
"""
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from app.core.logger import logger

class PortfolioOptimizer:
    def __init__(self, price_df: pd.DataFrame, risk_free_rate: float = 0.05):
        """
        price_df: DataFrame indexed by Date with symbols as columns containing daily prices.
        """
        self.symbols = list(price_df.columns)
        self.num_assets = len(self.symbols)
        self.risk_free_rate = risk_free_rate

        # Calculate daily returns
        self.returns = price_df.pct_change().dropna()
        # Annualized expected returns (sample mean) and covariance
        self.mean_returns = self.returns.mean() * 252.0
        self.cov_matrix = self.returns.cov() * 252.0

    def portfolio_performance(self, weights: np.ndarray) -> Tuple[float, float, float]:
        """Calculates expected return, volatility, and Sharpe ratio for weights."""
        weights = np.array(weights)
        p_return = float(np.dot(weights, self.mean_returns))
        p_vol = float(np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights))))
        sharpe = (p_return - self.risk_free_rate) / (p_vol + 1e-10)
        return p_return, p_vol, sharpe

    def optimize_equal_weight(self) -> Dict[str, Any]:
        """Equal-weight benchmark (1/N)."""
        w = np.ones(self.num_assets) / self.num_assets
        ret, vol, sharpe = self.portfolio_performance(w)
        return {
            "strategy": "Equal-Weight",
            "weights": {s: float(w[i]) for i, s in enumerate(self.symbols)},
            "expected_return": ret,
            "expected_volatility": vol,
            "sharpe_ratio": sharpe
        }

    def optimize_min_variance(self, max_weight: float = 0.40) -> Dict[str, Any]:
        """
        Minimum-Variance Portfolio.
        Minimizes portfolio variance subject to weights summing to 1 and bounds [0, max_weight].
        """
        init_guess = np.ones(self.num_assets) / self.num_assets
        bounds = tuple((0.0, max_weight) for _ in range(self.num_assets))
        constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}

        def objective(w):
            return np.dot(w.T, np.dot(self.cov_matrix, w))

        opt = minimize(objective, init_guess, method="SLSQP", bounds=bounds, constraints=constraints)
        if not opt.success:
            logger.warning(f"Min-variance optimization did not converge: {opt.message}")

        weights = np.clip(opt.x, 0.0, 1.0)
        weights /= np.sum(weights)
        ret, vol, sharpe = self.portfolio_performance(weights)

        return {
            "strategy": "Minimum-Variance",
            "weights": {s: float(weights[i]) for i, s in enumerate(self.symbols)},
            "expected_return": ret,
            "expected_volatility": vol,
            "sharpe_ratio": sharpe
        }

    def optimize_max_sharpe(self, max_weight: float = 0.40) -> Dict[str, Any]:
        """
        Maximum-Sharpe (Tangency) Portfolio.
        Maximizes Sharpe ratio subject to weights summing to 1 and bounds [0, max_weight].
        """
        init_guess = np.ones(self.num_assets) / self.num_assets
        bounds = tuple((0.0, max_weight) for _ in range(self.num_assets))
        constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}

        def negative_sharpe(w):
            p_ret = np.dot(w, self.mean_returns)
            p_vol = np.sqrt(np.dot(w.T, np.dot(self.cov_matrix, w)))
            return -((p_ret - self.risk_free_rate) / (p_vol + 1e-10))

        opt = minimize(negative_sharpe, init_guess, method="SLSQP", bounds=bounds, constraints=constraints)
        if not opt.success:
            logger.warning(f"Max-Sharpe optimization did not converge: {opt.message}")

        weights = np.clip(opt.x, 0.0, 1.0)
        weights /= np.sum(weights)
        ret, vol, sharpe = self.portfolio_performance(weights)

        return {
            "strategy": "Maximum-Sharpe",
            "weights": {s: float(weights[i]) for i, s in enumerate(self.symbols)},
            "expected_return": ret,
            "expected_volatility": vol,
            "sharpe_ratio": sharpe
        }

    def optimize_inverse_variance(self) -> Dict[str, Any]:
        """
        Inverse-Variance Portfolio (Risk Parity proxy).
        Weights inversely proportional to individual asset variance.
        """
        variances = np.diag(self.cov_matrix)
        inv_vars = 1.0 / (variances + 1e-10)
        weights = inv_vars / np.sum(inv_vars)
        ret, vol, sharpe = self.portfolio_performance(weights)

        return {
            "strategy": "Inverse-Variance / Risk Parity",
            "weights": {s: float(weights[i]) for i, s in enumerate(self.symbols)},
            "expected_return": ret,
            "expected_volatility": vol,
            "sharpe_ratio": sharpe
        }

    def generate_efficient_frontier(self, points: int = 25, max_weight: float = 0.50) -> List[Dict[str, Any]]:
        """
        Generates points along Markowitz Efficient Frontier by sweeping target returns.
        """
        min_v = self.optimize_min_variance(max_weight=max_weight)
        max_s = self.optimize_max_sharpe(max_weight=max_weight)

        min_ret = min_v["expected_return"]
        max_ret = max(float(self.mean_returns.max()), max_s["expected_return"])
        
        target_returns = np.linspace(min_ret, max_ret, points)
        frontier_points = []

        init_guess = np.ones(self.num_assets) / self.num_assets
        bounds = tuple((0.0, max_weight) for _ in range(self.num_assets))

        for target in target_returns:
            constraints = [
                {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
                {"type": "eq", "fun": lambda w, t=target: np.dot(w, self.mean_returns) - t}
            ]
            opt = minimize(
                lambda w: np.dot(w.T, np.dot(self.cov_matrix, w)),
                init_guess,
                method="SLSQP",
                bounds=bounds,
                constraints=constraints
            )
            if opt.success:
                w = np.clip(opt.x, 0.0, 1.0)
                w /= np.sum(w)
                ret, vol, sharpe = self.portfolio_performance(w)
                frontier_points.append({
                    "return": ret,
                    "volatility": vol,
                    "sharpe": sharpe,
                    "weights": {s: float(w[i]) for i, s in enumerate(self.symbols)}
                })

        return frontier_points
