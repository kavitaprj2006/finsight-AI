"""
Unit Tests for Portfolio Optimization
"""
import pytest
import numpy as np
import pandas as pd
from app.analytics.portfolio_optimizer import PortfolioOptimizer

@pytest.fixture
def multi_asset_prices():
    """Generates 3 synthetic asset price series with different risk/return characteristics."""
    np.random.seed(42)
    dates = pd.bdate_range(end=pd.Timestamp.now(), periods=150)
    
    # Asset A: High Return, High Vol
    ret_a = np.random.normal(0.0012, 0.02, 150)
    # Asset B: Moderate Return, Low Vol
    ret_b = np.random.normal(0.0006, 0.01, 150)
    # Asset C: Defensive
    ret_c = np.random.normal(0.0004, 0.008, 150)

    p_a = 100.0 * np.cumprod(1.0 + ret_a)
    p_b = 50.0 * np.cumprod(1.0 + ret_b)
    p_c = 200.0 * np.cumprod(1.0 + ret_c)

    return pd.DataFrame({"AssetA": p_a, "AssetB": p_b, "AssetC": p_c}, index=dates)

def test_equal_weight_optimization(multi_asset_prices):
    opt = PortfolioOptimizer(multi_asset_prices)
    res = opt.optimize_equal_weight()
    
    weights = list(res["weights"].values())
    assert pytest.approx(sum(weights), abs=1e-5) == 1.0
    for w in weights:
        assert pytest.approx(w, abs=1e-5) == 1.0 / 3.0

def test_min_variance_optimization(multi_asset_prices):
    opt = PortfolioOptimizer(multi_asset_prices)
    res = opt.optimize_min_variance(max_weight=0.60)
    
    weights = list(res["weights"].values())
    assert pytest.approx(sum(weights), abs=1e-4) == 1.0
    assert all(w >= -1e-5 for w in weights) # No short selling
    assert all(w <= 0.60 + 1e-4 for w in weights) # Respects max weight bound

def test_max_sharpe_optimization(multi_asset_prices):
    opt = PortfolioOptimizer(multi_asset_prices)
    res = opt.optimize_max_sharpe(max_weight=0.60)
    
    weights = list(res["weights"].values())
    assert pytest.approx(sum(weights), abs=1e-4) == 1.0
    assert all(w >= -1e-5 for w in weights)
    assert res["sharpe_ratio"] is not None

def test_efficient_frontier_generation(multi_asset_prices):
    opt = PortfolioOptimizer(multi_asset_prices)
    frontier = opt.generate_efficient_frontier(points=10, max_weight=0.60)
    
    assert len(frontier) >= 5
    for pt in frontier:
        assert "return" in pt
        assert "volatility" in pt
        assert "weights" in pt
        assert pytest.approx(sum(pt["weights"].values()), abs=1e-3) == 1.0
