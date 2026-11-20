"""
Unit Tests for Financial Risk Metrics
"""
import pytest
import numpy as np
import pandas as pd
from app.analytics.risk_metrics import (
    calculate_daily_returns, calculate_annualized_return,
    calculate_annualized_volatility, calculate_sharpe_ratio,
    calculate_sortino_ratio, calculate_drawdown,
    calculate_var, calculate_cvar, calculate_beta,
    compute_portfolio_risk_profile
)

def test_daily_returns(sample_price_series):
    returns = calculate_daily_returns(sample_price_series)
    assert len(returns) == len(sample_price_series) - 1
    assert isinstance(returns, pd.Series)
    assert not returns.isna().any()

def test_annualized_return_and_volatility():
    # 10% annual return with zero vol
    constant_daily_ret = pd.Series([0.0004] * 252) # ~10% annual
    ann_ret = calculate_annualized_return(constant_daily_ret)
    assert 0.09 < ann_ret < 0.12

    # Known volatility test
    noisy_ret = pd.Series(np.random.normal(loc=0.0, scale=0.01, size=252))
    ann_vol = calculate_annualized_volatility(noisy_ret)
    assert 0.12 < ann_vol < 0.20 # 0.01 * sqrt(252) ~ 0.158

def test_sharpe_and_sortino_ratio():
    # Positive return series
    daily_ret = pd.Series(np.random.normal(loc=0.002, scale=0.01, size=252))
    sharpe = calculate_sharpe_ratio(daily_ret, risk_free_rate=0.05)
    sortino = calculate_sortino_ratio(daily_ret, risk_free_rate=0.05)
    assert isinstance(sharpe, float)
    assert isinstance(sortino, float)
    assert sortino >= sharpe  # Sortino only penalizes downside

def test_drawdown_calculation():
    # Prices: 100 -> 120 -> 90 -> 110
    prices = pd.Series([100.0, 120.0, 90.0, 110.0])
    dd_res = calculate_drawdown(prices)
    # Peak is 120, trough is 90 -> drawdown is (90 - 120) / 120 = -0.25 (-25%)
    assert pytest.approx(dd_res["max_drawdown"], abs=1e-3) == -0.25
    assert len(dd_res["drawdown_series"]) == 4

def test_var_and_cvar():
    np.random.seed(42)
    daily_ret = pd.Series(np.random.normal(loc=0.0, scale=0.02, size=500))
    var_95 = calculate_var(daily_ret, confidence_level=0.95)
    cvar_95 = calculate_cvar(daily_ret, confidence_level=0.95)

    assert var_95 > 0.0
    assert cvar_95 >= var_95  # Expected shortfall is always at least as extreme as VaR

def test_beta_calculation():
    bench_ret = pd.Series(np.random.normal(loc=0.0005, scale=0.01, size=100))
    # Asset with beta = 1.5 + noise
    asset_ret = 1.5 * bench_ret + pd.Series(np.random.normal(loc=0.0, scale=0.002, size=100))
    beta = calculate_beta(asset_ret, bench_ret)
    assert pytest.approx(beta, abs=0.2) == 1.5
