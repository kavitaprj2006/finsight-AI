"""
FinSight AI - Financial Risk Analytics Engine
Calculates Sharpe, Sortino, Max Drawdown, Historical VaR, CVaR, Beta, and Correlations.
"""
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd

def calculate_daily_returns(series: pd.Series) -> pd.Series:
    """Computes daily percentage returns."""
    return series.pct_change().dropna()

def calculate_annualized_return(returns: pd.Series, periods_per_year: int = 252) -> float:
    """Calculates geometric compound annualized return."""
    if len(returns) == 0:
        return 0.0
    cum_return = (1.0 + returns).prod()
    n_years = len(returns) / periods_per_year
    if n_years <= 0 or cum_return <= 0:
        return float(returns.mean() * periods_per_year)
    return float(cum_return ** (1.0 / n_years) - 1.0)

def calculate_annualized_volatility(returns: pd.Series, periods_per_year: int = 252) -> float:
    """Calculates annualized standard deviation of returns."""
    if len(returns) < 2:
        return 0.0
    return float(returns.std() * np.sqrt(periods_per_year))

def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.05, periods_per_year: int = 252) -> float:
    """
    Computes annualized Sharpe ratio.
    Default risk-free rate is 5% (0.05).
    """
    ann_vol = calculate_annualized_volatility(returns, periods_per_year)
    if ann_vol < 1e-6:
        return 0.0
    ann_ret = calculate_annualized_return(returns, periods_per_year)
    return float((ann_ret - risk_free_rate) / ann_vol)

def calculate_sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.05, periods_per_year: int = 252) -> float:
    """
    Computes annualized Sortino ratio using downside semi-deviation.
    """
    rf_daily = risk_free_rate / periods_per_year
    downside_diff = returns - rf_daily
    downside_returns = downside_diff[downside_diff < 0.0]
    if len(downside_returns) < 2:
        return 0.0
    downside_dev = np.sqrt((downside_returns ** 2).mean()) * np.sqrt(periods_per_year)
    if downside_dev < 1e-6:
        return 0.0
    ann_ret = calculate_annualized_return(returns, periods_per_year)
    return float((ann_ret - risk_free_rate) / downside_dev)

def calculate_drawdown(series: pd.Series) -> Dict[str, Any]:
    """
    Computes drawdown series and maximum drawdown.
    """
    if len(series) == 0:
        return {"max_drawdown": 0.0, "drawdown_series": pd.Series(dtype=float)}
    cum_max = series.cummax()
    drawdown = (series - cum_max) / (cum_max + 1e-10)
    max_dd = float(drawdown.min())  # negative float e.g. -0.18
    return {
        "max_drawdown": max_dd,
        "drawdown_series": drawdown
    }

def calculate_var(returns: pd.Series, confidence_level: float = 0.95) -> float:
    """
    Historical Value at Risk (VaR).
    Returns positive value representing maximum expected loss % at given confidence.
    """
    if len(returns) == 0:
        return 0.0
    percentile = (1.0 - confidence_level) * 100.0
    var_val = -float(np.percentile(returns, percentile))
    return max(0.0, var_val)

def calculate_cvar(returns: pd.Series, confidence_level: float = 0.95) -> float:
    """
    Conditional Value at Risk (CVaR / Expected Shortfall).
    Expected loss given that loss exceeds the VaR threshold.
    """
    if len(returns) == 0:
        return 0.0
    var_threshold = -calculate_var(returns, confidence_level)
    tail_losses = returns[returns <= var_threshold]
    if len(tail_losses) == 0:
        return calculate_var(returns, confidence_level)
    return float(-tail_losses.mean())

def calculate_beta(asset_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """
    Calculates asset Beta relative to benchmark.
    Aligns both series chronologically on date index.
    """
    combined = pd.concat([asset_returns, benchmark_returns], axis=1, join="inner").dropna()
    if len(combined) < 10:
        return 1.0
    cov = np.cov(combined.iloc[:, 0], combined.iloc[:, 1])[0, 1]
    var_bench = np.var(combined.iloc[:, 1])
    if var_bench < 1e-8:
        return 1.0
    return float(cov / var_bench)

def compute_portfolio_risk_profile(
    price_series: pd.Series,
    benchmark_series: Optional[pd.Series] = None,
    risk_free_rate: float = 0.05
) -> Dict[str, Any]:
    """Generates a complete financial risk assessment dictionary."""
    daily_ret = calculate_daily_returns(price_series)
    ann_ret = calculate_annualized_return(daily_ret)
    ann_vol = calculate_annualized_volatility(daily_ret)
    sharpe = calculate_sharpe_ratio(daily_ret, risk_free_rate)
    sortino = calculate_sortino_ratio(daily_ret, risk_free_rate)
    dd_info = calculate_drawdown(price_series)
    var_95 = calculate_var(daily_ret, 0.95)
    cvar_95 = calculate_cvar(daily_ret, 0.95)

    beta = 1.0
    if benchmark_series is not None and len(benchmark_series) > 10:
        bench_ret = calculate_daily_returns(benchmark_series)
        beta = calculate_beta(daily_ret, bench_ret)

    return {
        "annualized_return": ann_ret,
        "annualized_volatility": ann_vol,
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino,
        "max_drawdown": dd_info["max_drawdown"],
        "drawdown_series": dd_info["drawdown_series"],
        "var_95": var_95,
        "cvar_95": cvar_95,
        "beta": beta,
        "daily_returns": daily_ret
    }
